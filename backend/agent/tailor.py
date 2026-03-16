"""
Resume tailoring using Qwen3-32B via Groq.
Based on 2025 recruiter preferences and ATS standards.
"""
import os
import json
import uuid
from pypdf import PdfReader
from .llm import get_primary_llm


def extract_text_from_pdf(file_path: str) -> str:
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"[PDF] Error: {e}")
        return ""


async def tailor_resume_html(visual_resume_path: str, job_description: str, output_dir: str = "output"):
    if not os.path.exists(visual_resume_path):
        return None

    resume_text = extract_text_from_pdf(visual_resume_path)
    if not resume_text:
        return None

    llm = get_primary_llm()

    prompt = f"""You are an expert resume writer. Create a tailored, ATS-optimized resume that gets interviews.

ORIGINAL RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

=== CRITICAL RULES - NEVER VIOLATE ===

1. PRESERVE ALL ORIGINAL DATA:
   - Keep ALL contact info exactly as-is (email, phone, GitHub, LinkedIn, portfolio, etc.)
   - Keep ALL dates exactly as-is (if original has no dates, DO NOT add any)
   - Keep ALL company names, job titles, universities exactly as-is
   - Keep ALL skills, projects, technologies exactly as-is
   - NEVER invent: dates, companies, job titles, skills, metrics, or any facts

2. WHAT YOU CAN DO:
   - REORDER: Put most relevant skills/projects first
   - REFRAME: Rewrite bullet points to emphasize job-relevant aspects
   - REWORD: Use job description keywords where candidate genuinely has experience
   - REWRITE SUMMARY: Customize for this specific job
   - CONDENSE: Make content more concise to fit space

=== MATCH ANALYSIS ===

Evaluate HOLISTICALLY (all factors together):

RETURN {{"mismatched": true}} ONLY IF MULTIPLE RED FLAGS:
- Weak experience (0-1 yr) + Missing 2+ required skills + No relevant projects
- 5+ years required + 0 years experience + No strong compensating projects  
- Completely wrong domain + No transferable skills + Missing required skills

DO NOT mismatch for:
- Years gap alone (if projects/skills are strong)
- Missing 1 required skill (if rest is strong)
- Missing preferred skills
- Entry-level with good projects applying for 1-3 yr role

=== IF MATCH: GENERATE TAILORED RESUME ===

TAILORING STRATEGY (what makes resumes effective in 2025):

1. PROFESSIONAL SUMMARY (2-3 lines):
   - Mention the job title from JD (or close equivalent)
   - Highlight 2-3 most relevant skills from JD
   - Hint at impact/results (from original resume)
   - Example: "Backend developer with experience building REST APIs using FastAPI and Python. Skilled in database design and LangChain integrations, with projects demonstrating scalable system architecture."

2. SKILLS SECTION:
   - Put JD-relevant skills FIRST
   - Use exact terminology from JD (if candidate has them)
   - Group logically: Languages, Frameworks, Tools, Databases, etc.
   - Don't add skills candidate doesn't have

3. PROJECTS (emphasize for entry-level):
   - Lead with projects most relevant to JD
   - Rewrite bullets using CAR method: Challenge → Action → Result
   - Add metrics if original has them (don't invent)
   - Use JD keywords naturally: "Built REST API with FastAPI" not "Made an app"
   - 2-4 bullets per project, focus on relevance to THIS job

4. WORK EXPERIENCE (if exists in original):
   - Emphasize achievements relevant to JD
   - Use action verbs: Built, Developed, Led, Optimized, Reduced, Increased
   - Quantify where original has numbers (don't invent metrics)
   - 3-5 bullets per role

5. CONTACT INFO:
   - Copy EXACTLY from original resume
   - Include: Name, Email, Phone, GitHub, LinkedIn, Portfolio, Location
   - DO NOT add, remove, or modify anything

ATS FORMATTING (2025 standards):
- Font: Calibri or Arial only
- Name: 20-22pt bold, Headers: 12-14pt bold, Body: 10-11pt
- Margins: 0.75in all sides
- Line spacing: 1.15
- Single column, left-aligned
- NO tables, images, icons, graphics, headers/footers
- Standard section headers: "Professional Summary", "Technical Skills", "Projects", "Work Experience", "Education"

PAGE LENGTH:
- Entry-level (no work experience): 1 page maximum
- Has work experience: 1-2 pages based on content
- Adjust bullet conciseness to fit - NO text cutoff

=== OUTPUT HTML ===

Use this EXACT structure (fill in from original resume):

<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{ 
  font-family: 'Calibri', 'Arial', sans-serif; 
  font-size: 11pt; 
  line-height: 1.15; 
  max-width: 8.5in; 
  margin: 0.75in auto; 
  color: #000;
}}
h1 {{ 
  font-size: 22pt; 
  font-weight: bold; 
  margin: 0 0 6pt 0; 
  text-align: center;
}}
.contact {{ 
  font-size: 9.5pt; 
  text-align: center; 
  margin-bottom: 14pt;
  color: #333;
}}
h2 {{ 
  font-size: 13pt; 
  font-weight: bold; 
  margin: 16pt 0 8pt 0;
  border-bottom: 1px solid #000;
  padding-bottom: 3pt;
  text-transform: uppercase;
}}
.entry {{ 
  margin-bottom: 12pt;
}}
.entry-header {{
  display: flex;
  justify-content: space-between;
  font-weight: bold;
  font-size: 11pt;
  margin-bottom: 2pt;
}}
.entry-sub {{
  font-size: 10.5pt;
  font-style: italic;
  margin-bottom: 4pt;
  color: #444;
}}
ul {{
  margin: 6pt 0;
  padding-left: 18pt;
}}
li {{
  font-size: 11pt;
  margin-bottom: 3pt;
}}
.skills {{
  font-size: 11pt;
  line-height: 1.5;
}}
@media print {{
  body {{ margin: 0.5in; }}
}}
</style>
</head>
<body>

<h1>[Name from original]</h1>
<div class="contact">[ALL contact info from original - email, phone, GitHub, LinkedIn, etc.]</div>

<h2>Professional Summary</h2>
<p>[2-3 lines tailored to job, using JD keywords where candidate has experience]</p>

<h2>Technical Skills</h2>
<div class="skills">[Most relevant skills first, grouped logically]</div>

<h2>Projects</h2>
<div class="entry">
  <div class="entry-header">
    <span>[Project Name]</span>
    <span>[Date ONLY if original has it]</span>
  </div>
  <ul>
    <li>[CAR method: Challenge, Action, Result]</li>
    <li>[Emphasize aspects relevant to JD]</li>
    <li>[Use JD keywords naturally]</li>
  </ul>
</div>

<h2>Work Experience</h2>
[ONLY if original resume has this section - DO NOT INVENT]
<div class="entry">
  <div class="entry-header">
    <span>[Job Title] · [Company]</span>
    <span>[Dates from original]</span>
  </div>
  <div class="entry-sub">[Location from original]</div>
  <ul>
    <li>[Tailored bullets with metrics from original]</li>
  </ul>
</div>

<h2>Education</h2>
<div class="entry">
  <div class="entry-header">
    <span>[Degree] in [Major]</span>
    <span>[Graduation from original]</span>
  </div>
  <div class="entry-sub">[University from original]</div>
</div>

</body>
</html>

=== OUTPUT ===
If mismatch: {{"mismatched": true}}
If match: Complete HTML document only (no markdown, no explanations)"""

    response = llm.invoke([{"role": "user", "content": prompt}])
    content = response.content.strip()

    # Strip <think>...</think> tags (chain-of-thought leakage)
    import re
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL | re.IGNORECASE).strip()

    # Clean markdown
    if content.startswith("```json"):
        content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        try:
            data = json.loads(content)
            if data.get("mismatched"):
                return {
                    "error": "mismatch",
                    "match_analysis": {"mismatched": True},
                    "pdf_path": None
                }
        except:
            pass

    if content.startswith("```html"):
        content = content[7:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    
    # Ensure HTML structure if missing
    if not content.startswith("<!DOCTYPE"):
        content = f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>body{{font-family:Calibri,Arial,sans-serif;font-size:11pt;line-height:1.15;max-width:8.5in;margin:0.75in auto}}h1{{font-size:22pt;font-weight:bold;margin:0 0 6pt 0;text-align:center}}.contact{{font-size:9.5pt;text-align:center;margin-bottom:14pt}}h2{{font-size:13pt;font-weight:bold;margin:16pt 0 8pt 0;border-bottom:1px solid #000;padding-bottom:3pt;text-transform:uppercase}}.entry{{margin-bottom:12pt}}.entry-header{{display:flex;justify-content:space-between;font-weight:bold;font-size:11pt}}ul{{margin:6pt 0;padding-left:18pt}}li{{font-size:11pt;margin-bottom:3pt}}</style></head><body>{content}</body></html>"
    
    # Save and generate PDF
    os.makedirs(output_dir, exist_ok=True)
    file_id = str(uuid.uuid4())
    html_path = os.path.join(output_dir, f"{file_id}.html")
    pdf_path = os.path.join(output_dir, f"{file_id}.pdf")
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    # Generate PDF
    pdf_generated = False
    try:
        import threading
        def gen_pdf():
            nonlocal pdf_generated
            try:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    page.goto(f"file://{os.path.abspath(html_path)}", wait_until="networkidle", timeout=30000)
                    page.pdf(path=pdf_path, format="A4", print_background=True)
                    browser.close()
                    if os.path.exists(pdf_path):
                        pdf_generated = True
            except Exception as err:
                print(f"[PDF] Error: {err}")
        
        t = threading.Thread(target=gen_pdf)
        t.start()
        t.join(timeout=60)
    except Exception as e:
        print(f"[PDF] Error: {e}")
    
    return {
        "error": None,
        "match_analysis": {"mismatched": False},
        "pdf_path": pdf_path if pdf_generated else None
    }
