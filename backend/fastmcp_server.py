from mcp.server.fastmcp import FastMCP
from jobspy import scrape_jobs
import pandas as pd
from typing import Optional, List, Dict, Any

from config import settings

# Initialize FastMCP Server
mcp = FastMCP(
    "AntiBerojgar-JobSearch",
    host="0.0.0.0",
    port=settings.MCP_JOBS_PORT,
    json_response=True
)
VALID_COUNTRIES = [
    # South Asia
    "nepal", "india", "pakistan", "bangladesh", "sri lanka", "bhutan", "maldives", "afghanistan",
    # Southeast Asia
    "singapore", "malaysia", "thailand", "indonesia", "vietnam", "philippines", "myanmar", "cambodia", "laos", "brunei", "timor-leste",
    # East Asia
    "japan", "south korea", "china", "hong kong", "taiwan", "macau", "mongolia",
    # Middle East
    "uae", "united arab emirates", "qatar", "bahrain", "kuwait", "oman", "saudi arabia", "israel", "jordan", "lebanon", "iraq", "iran", "turkey",
    # Europe
    "uk", "united kingdom", "germany", "france", "netherlands", "ireland", "switzerland", "sweden", "norway", "denmark", "finland", "belgium",
    "austria", "poland", "czech republic", "czechia", "romania", "bulgaria", "hungary", "greece", "portugal", "spain", "italy", "ukraine",
    "slovakia", "slovenia", "croatia", "estonia", "latvia", "lithuania", "cyprus", "malta", "luxembourg", "iceland", "serbia", "bosnia", "albania",
    # North America
    "usa", "united states", "canada", "mexico",
    # South America
    "brazil", "argentina", "chile", "colombia", "peru", "costa rica", "panama", "uruguay", "ecuador", "venezuela", "bolivia", "paraguay",
    # Africa
    "south africa", "egypt", "nigeria", "kenya", "ghana", "morocco", "ethiopia", "tanzania", "uganda", "rwanda", "tunisia", "algeria", "libya",
    # Oceania
    "australia", "new zealand", "fiji", "papua new guinea",
    # Central Asia
    "kazakhstan", "uzbekistan", "turkmenistan", "kyrgyzstan", "tajikistan",
    # Russia & CIS
    "russia", "belarus", "armenia", "azerbaijan", "georgia", "moldova"
]

# Indeed country domains mapping (for better localization)
INDEED_COUNTRY_DOMAINS = {
    "nepal": "indeed.com.np",
    "india": "indeed.co.in",
    "uk": "indeed.co.uk",
    "united kingdom": "indeed.co.uk",
    "canada": "ca.indeed.com",
    "australia": "au.indeed.com",
    "germany": "de.indeed.com",
    "france": "fr.indeed.com",
    "singapore": "sg.indeed.com",
    "malaysia": "my.indeed.com",
    "thailand": "th.indeed.com",
    "indonesia": "id.indeed.com",
    "vietnam": "vn.indeed.com",
    "philippines": "ph.indeed.com",
    "japan": "jp.indeed.com",
    "south korea": "kr.indeed.com",
    "uae": "ae.indeed.com",
    "united arab emirates": "ae.indeed.com",
    "qatar": "qatar.indeed.com",
    "bahrain": "bh.indeed.com",
    "kuwait": "kw.indeed.com",
    "oman": "om.indeed.com",
    "saudi arabia": "sa.indeed.com",
    "south africa": "za.indeed.com",
    "nigeria": "ng.indeed.com",
    "kenya": "ke.indeed.com",
    "egypt": "eg.indeed.com",
    "brazil": "br.indeed.com",
    "mexico": "mx.indeed.com",
    "argentina": "ar.indeed.com",
    "chile": "cl.indeed.com",
    "colombia": "co.indeed.com",
    "peru": "pe.indeed.com",
    "poland": "pl.indeed.com",
    "netherlands": "nl.indeed.com",
    "belgium": "be.indeed.com",
    "switzerland": "ch.indeed.com",
    "austria": "at.indeed.com",
    "sweden": "se.indeed.com",
    "norway": "no.indeed.com",
    "denmark": "dk.indeed.com",
    "finland": "fi.indeed.com",
    "ireland": "ie.indeed.com",
    "new zealand": "nz.indeed.com",
    "hong kong": "hk.indeed.com",
    "taiwan": "tw.indeed.com",
    "israel": "il.indeed.com",
    "turkey": "tr.indeed.com",
    "usa": "indeed.com",
    "united states": "indeed.com",
}

# Country name normalization (common abbreviations → full names for JobSpy API)
COUNTRY_NAME_MAP = {
    "uae": "united arab emirates",
    "uk": "united kingdom",
    "usa": "united states",
    "us": "united states",
    "turkiye": "turkey",
}

@mcp.tool()
def search_jobs(
    query: str,
    location: Optional[str] = None,
    job_type: Optional[str] = "fulltime",
    is_remote: bool = True,  # Changed default to True for global remote
    results_wanted: int = 20,
    country_override: Optional[str] = None,  # NEW: Explicit country override
) -> List[Dict[str, Any]]:
    """
    Search for jobs across LinkedIn, Indeed, and Glassdoor with GLOBAL coverage.

    Args:
        query: Job title/keywords (e.g., "Python AI Engineer", "Junior Backend Developer")
        location: Geographic location. For Nepal use "Nepal", for specific cities use "Kathmandu, Nepal"
        job_type: "fulltime", "parttime", "contract", "internship"
        is_remote: True for remote/worldwide jobs (default). False for location-specific.
        results_wanted: Number of jobs to return (10-50 recommended)
        country_override: Optional explicit country code (e.g., "nepal", "india") to override auto-detection

    Returns:
        List of job dictionaries with: id, site, job_url, title, company, location, job_type, date_posted, description
    """
    try:
        # NEW: Handle country override explicitly
        if country_override:
            loc = country_override.lower().strip()
            print(f"[JobSpy] Using country override: {loc}")
        elif is_remote:
            # For remote: use location if provided, otherwise worldwide
            if location:
                loc = location.lower().strip()
                print(f"[JobSpy] Remote search with location context: {loc}")
            else:
                # Worldwide remote - but we'll search multiple countries
                loc = None
                print(f"[JobSpy] Worldwide remote search")
        elif location:
            loc = location.lower().strip()
            print(f"[JobSpy] Location-specific search: {loc}")
        else:
            loc = None
            print(f"[JobSpy] Default worldwide search")

        # Validate country if provided
        if loc and loc not in VALID_COUNTRIES:
            print(f"[JobSpy] Warning: '{loc}' not in validated list, but attempting anyway")

        # Build site_name list dynamically
        site_name = ["linkedin", "indeed", "glassdoor"]

        # For Nepal + South Asia, prioritize Indeed (works best in region)
        if loc in ["nepal", "india", "pakistan", "bangladesh", "sri lanka"]:
            site_name = ["indeed", "linkedin", "glassdoor"]  # Indeed first for better coverage

        jobs: pd.DataFrame = scrape_jobs(
            site_name=site_name,
            search_term=query,
            location=loc,
            results_wanted=results_wanted,
            hours_old=720,  # 30 days - more inclusive for junior roles globally
            is_remote=is_remote,
            job_type=job_type,
            # NEW: Pass country_indeed for better Indeed localization
            country_indeed=loc if loc in INDEED_COUNTRY_DOMAINS else None,
        )

        if jobs.empty:
            print(f"[JobSpy] No results found for query: {query}")
            return []

        # Select important columns
        columns_to_keep = [
            "id", "site", "job_url", "title", "company", "location",
            "job_type", "date_posted", "description"
        ]

        actual_columns = [col for col in columns_to_keep if col in jobs.columns]
        jobs_cleaned = jobs[actual_columns].fillna("")

        result = jobs_cleaned.to_dict(orient="records")
        print(f"[JobSpy] Found {len(result)} jobs for: {query}")
        return result

    except Exception as e:
        print(f"[JobSpy] ERROR: {str(e)}")
        return [{"error": str(e), "query": query}]


@mcp.tool()
def search_jobs_direct(
    query: str,
    location: Optional[str] = None,
    country: Optional[str] = None,
    job_type: Optional[str] = "fulltime",
    is_remote: bool = True,
    results_wanted: int = 15,
) -> List[Dict[str, Any]]:
    """
    DIRECT SCRAPER FALLBACK - Uses Playwright to scrape LinkedIn/Indeed directly.
    Use this when JobSpy returns limited results or for better country coverage.
    
    Especially useful for: Nepal, India, and other countries where JobSpy has limited coverage.

    Args:
        query: Job title/keywords
        location: Geographic location (e.g., "Kathmandu", "Delhi")
        country: Country code for Indeed domain (e.g., "nepal", "india", "singapore")
        job_type: "fulltime", "parttime", "contract", "internship"
        is_remote: True for remote jobs
        results_wanted: Number of jobs to return

    Returns:
        List of job dictionaries from LinkedIn and Indeed
    """
    try:
        from direct_scraper import scrape_jobs_sync
        
        print(f"[DirectScraper] Searching for: {query} in {country or 'worldwide'}")
        
        jobs = scrape_jobs_sync(
            query=query,
            location=location,
            country=country,
            is_remote=is_remote,
            results_wanted=results_wanted,
        )
        
        print(f"[DirectScraper] Found {len(jobs)} jobs")
        return jobs
        
    except Exception as e:
        print(f"[DirectScraper] ERROR: {str(e)}")
        return [{"error": str(e), "query": query}]


@mcp.tool()
def search_jobs_multi_country(
    query: str,
    countries: List[str],
    job_type: Optional[str] = "fulltime",
    is_remote: bool = True,
    results_per_country: int = 10,
) -> List[Dict[str, Any]]:
    """
    Search jobs across MULTIPLE countries simultaneously.
    Useful for global remote workers targeting specific regions.

    Args:
        query: Job title/keywords
        countries: List of countries to search (e.g., ["nepal", "india", "singapore", "uae"])
        job_type: "fulltime", "parttime", "contract", "internship"
        is_remote: Filter for remote jobs
        results_per_country: Jobs to fetch per country (default 10)

    Returns:
        Combined list of jobs from all countries
    """
    all_jobs = []

    for country in countries:
        # Normalize country name (uae → united arab emirates)
        country_normalized = COUNTRY_NAME_MAP.get(country.lower(), country.lower())
        country_lower = country_normalized
        
        print(f"[MultiCountry] Searching {country_lower} for: {query}")

        try:
            jobs = scrape_jobs(
                site_name=["indeed", "linkedin"],
                search_term=query,
                location=country_lower,
                results_wanted=results_per_country,
                hours_old=720,
                is_remote=is_remote,
                job_type=job_type,
                country_indeed=country_lower if country_lower in INDEED_COUNTRY_DOMAINS else None,
            )

            if not jobs.empty:
                jobs_cleaned = jobs.fillna("")
                country_jobs = jobs_cleaned.to_dict(orient="records")

                # Tag with country for tracking
                for job in country_jobs:
                    job['search_country'] = country_lower

                all_jobs.extend(country_jobs)
                print(f"[MultiCountry] Found {len(country_jobs)} jobs in {country_lower}")

        except Exception as e:
            print(f"[MultiCountry] Error in {country_lower}: {e}")
            continue

    print(f"[MultiCountry] Total: {len(all_jobs)} jobs from {len(countries)} countries")
    return all_jobs


if __name__ == "__main__":
    print(f"[MCP JobSearch] running on port {settings.MCP_JOBS_PORT}")
    mcp.run(transport="streamable-http")
