export interface JobSearchFilters {
  keywords: string;
  location_type: 'remote' | 'remote_country' | 'onsite' | 'any';
  countries: string[];
  experience_levels: string[];
  job_types: string[];
  date_posted_hours: number;
  easy_apply_only: boolean;
}

export interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  description: string;
  job_url: string;
  url?: string;  // Alias for compatibility
  site?: string;
  job_type?: string;
  type?: string;  // Alias for job_type
  date_posted?: string;
  salary?: string;  // Alias for salary_info
  salary_info?: string;
  relevance_score?: number;
}

// Get API base URL from environment or use relative path
const getApiUrl = (path: string) => {
  const railwayUrl = import.meta.env.VITE_RAILWAY_URL;
  if (railwayUrl) {
    return `${railwayUrl}${path}`;
  }
  return path;
};

export const searchJobsNative = async (filters: JobSearchFilters) => {
  const res = await fetch(getApiUrl('/api/jobs/search'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(filters)
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Search failed');
  }
  return res.json();
}

export const invokeAgent = async (messages: any[], userEmail?: string, resumeData?: any, jobDescription?: string) => {
    const res = await fetch(getApiUrl('/api/agent/invoke'), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            messages,
            user_email: userEmail,
            user_resume_data: resumeData,
            job_description: jobDescription
        })
    });
    if (!res.ok) throw new Error("Failed to invoke agent API");
    return res.json();
}

export const getApplications = async (email: string) => {
    const res = await fetch(getApiUrl(`/api/applications?email=${encodeURIComponent(email)}`));
    if (!res.ok) throw new Error("Failed to fetch applications API");
    return res.json();
}

export const syncApplications = async (email: string) => {
    const res = await fetch(getApiUrl(`/api/applications/sync?email=${encodeURIComponent(email)}`), {
        method: 'POST'
    });
    if (!res.ok) throw new Error("Failed to sync applications");
    return res.json();
}

export const saveJobLead = async (jobLead: any) => {
    const res = await fetch(getApiUrl('/api/jobs/save'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(jobLead)
    });
    if (!res.ok) throw new Error("Failed to save job lead");
    return res.json();
}

export const getJobLeads = async (email: string) => {
    const res = await fetch(getApiUrl(`/api/jobs/leads?email=${encodeURIComponent(email)}`));
    if (!res.ok) throw new Error("Failed to fetch job leads");
    return res.json();
}
export const saveEmailSettings = async (userEmail: string, imapPassword: string) => {
    const res = await fetch(getApiUrl('/api/settings/email'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_email: userEmail, imap_password: imapPassword })
    });
    if (!res.ok) throw new Error("Failed to save email settings");
    return res.json();
}

export const getEmailSettings = async (email: string) => {
    const res = await fetch(getApiUrl(`/api/settings/email?email=${encodeURIComponent(email)}`));
    if (!res.ok) throw new Error("Failed to fetch email settings");
    return res.json();
}

export const uploadResume = async (file: File, userEmail?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (userEmail) formData.append('email', userEmail);

    const res = await fetch(getApiUrl('/api/resume/upload'), {
        method: 'POST',
        body: formData
    });
    if (!res.ok) throw new Error("Failed to upload resume");
    return res.json();
}

export interface TailorResult {
    status: string;
    tailored_resume_path?: string;
    message?: string;
}

export interface TailorRequest {
    email?: string;
    jobDescription: string;
}

export const tailorResume = async (params: TailorRequest): Promise<TailorResult> => {
    const res = await fetch(getApiUrl('/api/agent/invoke'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            messages: [{ role: 'user', content: 'Tailor my resume for this job' }],
            user_email: params.email,
            job_description: params.jobDescription
        })
    });
    if (!res.ok) throw new Error("Failed to tailor resume");
    return res.json();
}
