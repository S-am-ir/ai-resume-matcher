from langchain_core.messages import HumanMessage, SystemMessage
from .llm import get_vision_llm, get_main_llm
import json
import re
import os
import time

RESUME_EXTRACT_PROMPT = """You are a resume analyzer. Look at this resume PDF/image and extract information.

Output ONLY valid JSON (no markdown, no explanations):
{
  "target_roles": ["job titles they're seeking - include variations like 'AI Engineer', 'Python Developer', 'ML Engineer', 'Backend Developer', 'Automation Engineer"],
  "experience_level": "junior" | "mid" | "senior" | "principal",
  "key_skills": ["all technical skills, tools, frameworks, languages mentioned"],
  "must_have": ["critical requirements from their background"],
  "avoid": ["roles that don't match their level"],
  "search_keywords": ["flexible search terms combining skills + roles, e.g., 'Python AI', 'machine learning automation', 'LLM backend'"]
}

Rules:
1. Find target roles from: summary, objective, work experience, skills sections
2. Experience: "junior/entry/new grad/0-2 years" → junior, "mid/2-5 years" → mid, "senior/5+ years" → senior
3. Extract ALL specific tech mentioned: Python, TensorFlow, PyTorch, React, FastAPI, AWS, Docker, etc.
4. For "avoid": roles too senior (Principal/Staff/Director/Lead) if they're junior/mid
5. For "search_keywords": create 5-10 flexible combinations that would match real job postings
6. Be generous with skills - include everything relevant
7. CRITICAL: Do NOT return empty arrays - extract at least 3 items for each field
8. CRITICAL: Analyze the ACTUAL resume content - do NOT return generic defaults if you can see the resume"""

# Fallback prompt for text-based parsing (if Vision fails)
RESUME_TEXT_EXTRACT_PROMPT = """You are a resume analyzer. Extract structured information from this resume text.

Output ONLY valid JSON (no markdown, no explanations):
{
  "target_roles": ["job titles from summary/experience"],
  "experience_level": "junior" | "mid" | "senior" | "principal",
  "key_skills": ["technical skills mentioned"],
  "must_have": ["critical requirements"],
  "avoid": ["roles too senior for candidate"],
  "search_keywords": ["flexible search term combinations"]
}

Analyze the text carefully and extract meaningful data. Do NOT return empty arrays."""

def extract_resume_keywords(resume_text_or_path: str) -> dict:
    """Extract structured keywords from resume using Groq Vision API with robust fallbacks."""

    # Default fallback - dynamic based on filename analysis
    def get_dynamic_fallback(file_path=None):
        """Generate smarter fallback based on filename heuristics."""
        base_fallback = {
            "target_roles": ["Software Engineer", "Python Developer", "Backend Developer"],
            "experience_level": "mid",
            "key_skills": ["Python", "JavaScript", "SQL", "Git", "REST APIs"],
            "must_have": ["software development experience"],
            "avoid": ["Principal", "Staff", "Lead", "Director", "VP"],
            "search_keywords": ["python developer", "backend engineer", "software engineer"]
        }
        
        if file_path and os.path.exists(file_path):
            filename = os.path.basename(file_path).lower().replace('.pdf', '').replace('.png', '')
            
            # Extract keywords from filename
            filename_lower = filename.lower()
            
            # Role-specific keywords
            role_indicators = {
                "python": (["Python Developer", "Backend Engineer", "Python Engineer"], ["Python", "Django", "FastAPI", "Flask"]),
                "java": (["Java Developer", "Backend Engineer", "Software Engineer"], ["Java", "Spring Boot", "Maven", "Gradle"]),
                "javascript": (["JavaScript Developer", "Frontend Engineer", "Full Stack Developer"], ["JavaScript", "TypeScript", "Node.js", "React"]),
                "react": (["React Developer", "Frontend Engineer", "UI Developer"], ["React", "Redux", "JavaScript", "TypeScript", "CSS"]),
                "node": (["Node.js Developer", "Backend Engineer", "Full Stack Developer"], ["Node.js", "Express", "JavaScript", "MongoDB"]),
                "backend": (["Backend Developer", "Backend Engineer", "API Developer"], ["Python", "Java", "Go", "REST APIs", "SQL"]),
                "frontend": (["Frontend Developer", "Frontend Engineer", "UI Developer"], ["React", "Vue", "Angular", "JavaScript", "CSS"]),
                "fullstack": (["Full Stack Developer", "Full Stack Engineer"], ["JavaScript", "Python", "React", "Node.js", "SQL"]),
                "devops": (["DevOps Engineer", "Cloud Engineer", "SRE"], ["AWS", "Docker", "Kubernetes", "CI/CD", "Terraform"]),
                "data": (["Data Engineer", "Data Scientist", "Analytics Engineer"], ["Python", "SQL", "Spark", "Airflow", "Pandas"]),
                "ml": (["ML Engineer", "AI Engineer", "Machine Learning Engineer"], ["Python", "TensorFlow", "PyTorch", "Scikit-learn", "ML"]),
                "ai": (["AI Engineer", "ML Engineer", "AI Researcher"], ["Python", "PyTorch", "TensorFlow", "LLM", "NLP"]),
                "android": (["Android Developer", "Mobile Engineer"], ["Kotlin", "Java", "Android SDK", "Jetpack Compose"]),
                "ios": (["iOS Developer", "Mobile Engineer"], ["Swift", "SwiftUI", "iOS SDK", "Objective-C"]),
                "flutter": (["Flutter Developer", "Mobile Engineer"], ["Flutter", "Dart", "Firebase", "Mobile Development"]),
            }
            
            for keyword, (roles, skills) in role_indicators.items():
                if keyword in filename_lower:
                    return {
                        "target_roles": roles,
                        "experience_level": "mid",
                        "key_skills": skills,
                        "must_have": ["relevant development experience"],
                        "avoid": ["Principal", "Staff", "Lead", "Director", "VP"],
                        "search_keywords": [role.lower() for role in roles] + [skill.lower() for skill in skills[:3]]
                    }
        
        return base_fallback

    default_result = get_dynamic_fallback(
        resume_text_or_path if os.path.exists(resume_text_or_path) else None
    )

    # Check if this is a file path
    if os.path.exists(resume_text_or_path):
        file_path = resume_text_or_path
        print(f"[DEBUG] Processing resume file with Groq Vision: {file_path}")

        # Retry logic: 3 attempts with exponential backoff
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                with open(file_path, "rb") as f:
                    file_data = f.read()

                import base64
                base64_data = base64.b64encode(file_data).decode("utf-8")
                mime_type = "application/pdf" if file_path.endswith(".pdf") else "image/png"

                llm = get_vision_llm()
                msg = HumanMessage(
                    content=[
                        {"type": "text", "text": RESUME_EXTRACT_PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_data}"}}
                    ]
                )

                response = llm.invoke([msg])
                content = response.content.strip()

                # Parse JSON from response
                result = _parse_json_response(content, default_result)

                # VALIDATION: Ensure we got meaningful data
                validation_errors = []
                
                if not result.get('target_roles') or len(result['target_roles']) < 2:
                    validation_errors.append(f"target_roles has {len(result.get('target_roles', []))} items (need ≥2)")
                    
                if not result.get('key_skills') or len(result['key_skills']) < 3:
                    validation_errors.append(f"key_skills has {len(result.get('key_skills', []))} items (need ≥3)")

                if validation_errors:
                    print(f"[WARN] Vision API validation failed: {', '.join(validation_errors)}")
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2  # 2s, 4s, 6s
                        print(f"[INFO] Retrying in {wait_time}s... (attempt {attempt + 2}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        print("[WARN] All Vision API attempts failed, using fallback")
                        return _extract_from_text_fallback(file_path, default_result)

                print(f"[DEBUG] Groq Vision parsed successfully: {result}")
                return result

            except Exception as e:
                last_error = e
                print(f"[ERROR] Groq Vision API attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"[INFO] Retrying in {wait_time}s... (attempt {attempt + 2}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print("[INFO] All Vision API attempts exhausted, using text fallback...")
                    return _extract_from_text_fallback(file_path, default_result)

        # Should not reach here, but just in case
        return _extract_from_text_fallback(file_path, default_result)

    else:
        # It's text - but if it's PDF binary, we can't parse it
        if resume_text_or_path.startswith("%PDF"):
            print("[WARN] Received PDF binary. Use file path for Vision API.")
            return default_result

        # Parse as text
        try:
            llm = get_main_llm()
            msg = HumanMessage(content=f"{RESUME_TEXT_EXTRACT_PROMPT}\n\nResume:\n{resume_text_or_path[:4000]}")
            response = llm.invoke([msg])
            return _parse_json_response(response.content, default_result)
        except Exception as e:
            print(f"[ERROR] Text parsing failed: {e}")
            return default_result


def _extract_from_text_fallback(file_path: str, default_result: dict) -> dict:
    """Fallback: Extract text from PDF using pypdf and parse with LLM."""
    try:
        # Try to extract text using pypdf
        try:
            import pypdf
            print(f"[INFO] Extracting text from PDF: {file_path}")
            
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                text = ""
                for page in reader.pages[:5]:  # First 5 pages
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

            if text.strip():
                print(f"[INFO] Extracted {len(text)} chars from PDF")
                llm = get_main_llm()
                msg = HumanMessage(content=f"{RESUME_TEXT_EXTRACT_PROMPT}\n\nResume Text:\n{text[:5000]}")
                response = llm.invoke([msg])
                result = _parse_json_response(response.content, default_result)
                print(f"[DEBUG] Text fallback parsed: {result}")
                return result
            else:
                print("[WARN] PDF text extraction returned empty text")
        except ImportError as e:
            print(f"[INFO] pypdf not available: {e}")
        except Exception as e:
            print(f"[WARN] PDF text extraction failed: {e}")

        # Last resort: use filename/path hints for intelligent fallback
        filename = os.path.basename(file_path).lower()
        print(f"[INFO] Using filename-based heuristic: {filename}")
        
        # Extract keywords from filename
        filename_keywords = {
            "python": ["Python Developer", "Backend Engineer", "Python Engineer"],
            "java": ["Java Developer", "Backend Engineer", "Software Engineer"],
            "javascript": ["JavaScript Developer", "Frontend Engineer", "Full Stack Developer"],
            "react": ["React Developer", "Frontend Engineer", "UI Developer"],
            "node": ["Node.js Developer", "Backend Engineer", "Full Stack Developer"],
            "backend": ["Backend Developer", "Backend Engineer", "API Developer"],
            "frontend": ["Frontend Developer", "Frontend Engineer", "UI Developer"],
            "fullstack": ["Full Stack Developer", "Full Stack Engineer"],
            "devops": ["DevOps Engineer", "Cloud Engineer", "SRE"],
            "data": ["Data Engineer", "Data Scientist", "Analytics Engineer"],
            "ml": ["ML Engineer", "AI Engineer", "Machine Learning Engineer"],
            "ai": ["AI Engineer", "ML Engineer", "AI Researcher"],
            "cv": default_result["target_roles"],
            "resume": default_result["target_roles"],
        }
        
        matched_roles = []
        matched_skills = []
        
        for keyword, roles in filename_keywords.items():
            if keyword in filename:
                matched_roles.extend(roles[:2])
                if keyword not in ["cv", "resume"]:
                    matched_skills.append(keyword.upper() if len(keyword) <= 3 else keyword.title())
        
        if matched_roles:
            fallback = {
                "target_roles": list(set(matched_roles))[:4],
                "experience_level": "mid",
                "key_skills": list(set(matched_skills)) if matched_skills else default_result["key_skills"],
                "must_have": ["software development experience"],
                "avoid": ["Principal", "Staff", "Lead", "Director", "VP"],
                "search_keywords": [role.lower() for role in matched_roles[:3]]
            }
            print(f"[INFO] Filename heuristic fallback: {fallback}")
            return fallback

    except Exception as e:
        print(f"[ERROR] All fallbacks failed: {e}")

    return default_result

def _parse_json_response(content: str, default_result: dict) -> dict:
    """Parse JSON from LLM response with robust error handling."""
    try:
        # Remove markdown code blocks
        if '```' in content:
            matches = re.findall(r'```(?:json)?\s*({.*?})\s*```', content, re.DOTALL)
            if matches:
                content = matches[0]
            else:
                content = content.replace('```json', '').replace('```', '').strip()

        # Extract JSON object
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            content = content[json_start:json_end]

        parsed = json.loads(content)

        # Validate and merge with defaults
        result = {
            "target_roles": parsed.get("target_roles", default_result["target_roles"]),
            "experience_level": parsed.get("experience_level", default_result["experience_level"]),
            "key_skills": parsed.get("key_skills", default_result["key_skills"]),
            "must_have": parsed.get("must_have", default_result["must_have"]),
            "avoid": parsed.get("avoid", default_result["avoid"])
        }
        
        # Add search_keywords if present
        if "search_keywords" in parsed:
            result["search_keywords"] = parsed["search_keywords"]
        else:
            # Generate from roles + skills
            result["search_keywords"] = [f"{role}" for role in result["target_roles"][:3]]

        # Validate experience level
        valid_levels = ["junior", "mid", "senior", "principal"]
        if result["experience_level"] not in valid_levels:
            roles_str = ' '.join(result["target_roles"]).lower()
            if "junior" in roles_str or "entry" in roles_str or "grad" in roles_str:
                result["experience_level"] = "junior"
            elif "senior" in roles_str or "lead" in roles_str:
                result["experience_level"] = "senior"
            elif "principal" in roles_str or "staff" in roles_str:
                result["experience_level"] = "principal"
            else:
                result["experience_level"] = "mid"

        return result

    except Exception as e:
        print(f"[ERROR] JSON parse failed: {e}")
        print(f"[DEBUG] Raw content: {content[:300]}")
        return default_result
