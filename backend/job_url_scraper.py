"""
Job URL scraper - extracts job details from a URL.
Uses Playwright for rendering + JobSpy as fallback + LLM for site-agnostic parsing.
Production-ready with proper error handling and retries.
"""
from playwright.async_api import async_playwright
from typing import Optional, Dict
import asyncio


async def scrape_job_from_url(url: str) -> Optional[Dict]:
    """
    Scrape job details from a job posting URL.
    
    IMPORTANT: Must be a DIRECT job posting URL, not a search URL.
    Valid: https://www.linkedin.com/jobs/view/123456789
    Invalid: https://www.linkedin.com/jobs/search/?keywords=...
    """
    if not url:
        return None
    
    # Validate URL format
    if '/jobs/search/' in url or '?' in url.split('/')[-1]:
        print(f"[JobScraper] Invalid URL format - this is a search URL, not a job posting")
        return None
    
    if not (url.startswith('http://') or url.startswith('https://')):
        print(f"[JobScraper] Invalid URL - must start with http:// or https://")
        return None
    
    max_retries = 2
    last_error = None
    
    for attempt in range(max_retries):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-accelerated-2d-canvas",
                        "--disable-gpu",
                    ]
                )
                
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                )
                
                page = await context.new_page()
                
                await page.set_extra_http_headers({
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                })
                
                print(f"[JobScraper] Loading: {url}")
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(3000)
                
                page_content = await page.content()
                
                # Check for login wall
                if "sign in" in page_content.lower() or "log in" in page_content.lower() or "access denied" in page_content.lower():
                    print(f"[JobScraper] Login wall detected")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 * (attempt + 1))
                        continue
                    break
                
                # Detect site
                if "linkedin.com/jobs/view" in url:
                    print("[JobScraper] LinkedIn job posting")
                    job_data = await _scrape_linkedin(page, url)
                elif "indeed.com/viewjob" in url or "indeed.co" in url:
                    print("[JobScraper] Indeed job posting")
                    job_data = await _scrape_indeed(page, url)
                elif "glassdoor.com/job" in url:
                    print("[JobScraper] Glassdoor job posting")
                    job_data = await _scrape_glassdoor(page, url)
                else:
                    print("[JobScraper] Unknown site - using LLM")
                    job_data = await _scrape_with_llm(page, url)
                
                await browser.close()
                
                if job_data:
                    print(f"[JobScraper] Success: {job_data.get('job_title')} at {job_data.get('company')}")
                    return job_data
                    
        except Exception as e:
            last_error = e
            print(f"[JobScraper] Error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 * (attempt + 1))
    
    print(f"[JobScraper] All methods failed")
    return None


async def _scrape_linkedin(page, url: str) -> Optional[Dict]:
    """Scrape LinkedIn job posting."""
    try:
        # Wait for job container
        await page.wait_for_selector(".job-details-jobs-unified-top-card__primary-title", timeout=10000)
        
        # Extract job title
        title_el = await page.query_selector(".job-details-jobs-unified-top-card__primary-title")
        job_title = await title_el.inner_text() if title_el else ""
        
        # Extract company
        company_el = await page.query_selector(".job-details-jobs-unified-top-card__company-name")
        company = await company_el.inner_text() if company_el else ""
        
        # Extract location
        location_el = await page.query_selector(".job-details-jobs-unified-top-card__bullet")
        location = await location_el.inner_text() if location_el else ""
        
        # Extract description
        desc_el = await page.query_selector(".job-details-about-job__main")
        description = await desc_el.inner_text() if desc_el else ""
        
        if job_title and company:
            return {
                "job_title": job_title.strip(),
                "company": company.strip(),
                "location": location.strip() if location else "Remote",
                "job_url": url,
                "job_description": description.strip()[:5000],  # Limit description length
                "site": "linkedin"
            }
    except Exception as e:
        print(f"[LinkedIn Scraper] Error: {e}")
    
    return None


async def _scrape_indeed(page, url: str) -> Optional[Dict]:
    """Scrape Indeed job posting."""
    try:
        # Wait for job title
        await page.wait_for_selector("h1.jobsearch-JobInfoHeader-title", timeout=10000)
        
        # Extract job title
        title_el = await page.query_selector("h1.jobsearch-JobInfoHeader-title")
        job_title = await title_el.inner_text() if title_el else ""
        
        # Extract company
        company_el = await page.query_selector("div.jobsearch-InlineCompanyRating")
        company = await company_el.inner_text() if company_el else ""
        
        # Extract location
        location_el = await page.query_selector("div.jobsearch-JobInfoHeader-subtitle")
        location = await location_el.inner_text() if location_el else ""
        
        # Extract description
        desc_el = await page.query_selector("#jobDescriptionText")
        description = await desc_el.inner_text() if desc_el else ""
        
        if job_title:
            return {
                "job_title": job_title.strip(),
                "company": company.strip() if company else "Unknown",
                "location": location.strip() if location else "Remote",
                "job_url": url,
                "job_description": description.strip()[:5000],
                "site": "indeed"
            }
    except Exception as e:
        print(f"[Indeed Scraper] Error: {e}")
    
    return None


async def _scrape_glassdoor(page, url: str) -> Optional[Dict]:
    """Scrape Glassdoor job posting."""
    try:
        # Wait for job container
        await page.wait_for_selector("[data-test='jobTitle']", timeout=10000)

        # Extract job title
        title_el = await page.query_selector("[data-test='jobTitle']")
        job_title = await title_el.inner_text() if title_el else ""

        # Extract company
        company_el = await page.query_selector("[data-test='employer']")
        company = await company_el.inner_text() if company_el else ""

        # Extract location
        location_el = await page.query_selector("[data-test='location']")
        location = await location_el.inner_text() if location_el else ""

        # Extract description
        desc_el = await page.query_selector("[data-test='jobDescription']")
        description = await desc_el.inner_text() if desc_el else ""

        if job_title:
            return {
                "job_title": job_title.strip(),
                "company": company.strip() if company else "Unknown",
                "location": location.strip() if location else "Remote",
                "job_url": url,
                "job_description": description.strip()[:5000],
                "site": "glassdoor"
            }
    except Exception as e:
        print(f"[Glassdoor Scraper] Error: {e}")

    return None


async def _scrape_ziprecruiter(page, url: str) -> Optional[Dict]:
    """Scrape ZipRecruiter job posting."""
    try:
        # Wait for job container
        await page.wait_for_selector("h1", timeout=10000)

        # Extract job title - usually in h1
        title_el = await page.query_selector("h1")
        job_title = await title_el.inner_text() if title_el else ""

        # Extract company - look for company links or specific classes
        company_el = await page.query_selector("[class*='company'], .company-name, a[href*='/companies/']")
        company = await company_el.inner_text() if company_el else ""

        # Extract location
        location_el = await page.query_selector("[class*='location'], .job-location")
        location = await location_el.inner_text() if location_el else ""

        # Extract description
        desc_el = await page.query_selector("[class*='description'], .job-description, #job_description")
        description = await desc_el.inner_text() if desc_el else ""

        if job_title:
            return {
                "job_title": job_title.strip(),
                "company": company.strip() if company else "Unknown",
                "location": location.strip() if location else "Remote",
                "job_url": url,
                "job_description": description.strip()[:5000],
                "site": "ziprecruiter"
            }
    except Exception as e:
        print(f"[ZipRecruiter Scraper] Error: {e}")

    return None


async def _scrape_with_llm(page, url: str) -> Optional[Dict]:
    """
    Use LLM to parse job posting from unknown sites.
    This is the most robust fallback for company career pages.
    """
    try:
        # Get page content
        page_content = await page.content()
        
        # Get page title
        page_title = await page.title()
        
        # Use LLM to extract job information
        from .llm import get_main_llm
        llm = get_main_llm()
        
        # Truncate content if too long (LLM token limits)
        max_content_length = 15000
        if len(page_content) > max_content_length:
            # Keep beginning and end of content
            page_content = page_content[:max_content_length // 2] + "\n...[truncated]...\n" + page_content[-max_content_length // 2:]
        
        from langchain_core.messages import SystemMessage, HumanMessage
        
        system_prompt = """You are a job posting extractor. Analyze the HTML content and extract:
1. job_title: The position title
2. company: Company name
3. location: Job location (city, country, or "Remote")
4. job_description: Full job description text

Output ONLY valid JSON in this format:
{"job_title": "...", "company": "...", "location": "...", "job_description": "..."}

If you cannot find job information, return: {"error": "not_a_job_posting"}"""

        user_prompt = f"""Page Title: {page_title}

URL: {url}

HTML Content:
{page_content[:10000]}

Extract job information as JSON:"""

        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        # Parse JSON response
        import json
        import re
        
        content = response.content.strip()
        
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group()
        
        result = json.loads(content)
        
        if "error" in result:
            print("[LLM Scraper] Page doesn't appear to be a job posting")
            return None
        
        # Validate required fields
        if not result.get("job_title"):
            print("[LLM Scraper] No job title found")
            return None
        
        return {
            "job_title": result["job_title"].strip(),
            "company": result.get("company", "Unknown").strip(),
            "location": result.get("location", "Remote").strip(),
            "job_url": url,
            "job_description": result.get("job_description", "")[:5000].strip(),
            "site": "llm_parsed"
        }
        
    except Exception as e:
        print(f"[LLM Scraper] Error: {e}")
        return None


async def _scrape_generic(page, url: str) -> Optional[Dict]:
    """Scrape generic company career page."""
    try:
        # Try common selectors for job pages
        selectors = {
            "title": ["h1", "[class*='title']", "[data-test='title']"],
            "company": ["[class*='company']", "[data-test='company']", "meta[name='company']"],
            "location": ["[class*='location']", "[data-test='location']"],
            "description": ["[class*='description']", "[class*='job-description']", "main"]
        }
        
        job_title = ""
        company = ""
        location = ""
        description = ""
        
        # Try to extract title
        for selector in selectors["title"]:
            el = await page.query_selector(selector)
            if el:
                job_title = await el.inner_text()
                break
        
        # Try to extract company
        for selector in selectors["company"]:
            el = await page.query_selector(selector)
            if el:
                company = await el.inner_text()
                break
        
        # Try to extract location
        for selector in selectors["location"]:
            el = await page.query_selector(selector)
            if el:
                location = await el.inner_text()
                break
        
        # Try to extract description
        for selector in selectors["description"]:
            el = await page.query_selector(selector)
            if el:
                description = await el.inner_text()
                break
        
        if job_title:
            return {
                "job_title": job_title.strip(),
                "company": company.strip() if company else "Unknown",
                "location": location.strip() if location else "Remote",
                "job_url": url,
                "job_description": description.strip()[:5000],
                "site": "company_page"
            }
    except Exception as e:
        print(f"[Generic Scraper] Error: {e}")
    
    return None
