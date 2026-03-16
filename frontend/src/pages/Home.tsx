import { useState, useEffect, DragEvent } from 'react';
import { invokeAgent, getApplications, saveJobLead } from '../api';

interface HomeProps {
  userEmail: string | null;
  resume: File | null;
  onResumeUpload: (file: File) => void;
  onResumeRemove: () => void;
  hasResume: boolean;
  onOpenPreview: () => void;
}

interface ManualJob {
  title: string;
  company: string;
  url: string;
  description: string;
}

interface MatchWarning {
  type: string;
  reason: string;
  score: number;
}

interface Stats {
  applications: number;
  interviews: number;
}

export default function Home({
  userEmail,
  resume,
  onResumeUpload,
  onResumeRemove,
  hasResume,
  onOpenPreview
}: HomeProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [jobDescription, setJobDescription] = useState('');
  const [isTailoring, setIsTailoring] = useState(false);
  const [tailoredResumeUrl, setTailoredResumeUrl] = useState<string | null>(null);
  const [manualJob, setManualJob] = useState<ManualJob>({ title: '', company: '', url: '', description: '' });
  const [isAddingJob, setIsAddingJob] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [matchWarning, setMatchWarning] = useState<MatchWarning | null>(null);
  const [stats, setStats] = useState<Stats>({ applications: 0, interviews: 0 });

  // Fetch real stats when component mounts or userEmail changes
  useEffect(() => {
    if (userEmail) {
      getApplications(userEmail)
        .then(apps => {
          setStats({
            applications: apps.length,
            interviews: apps.filter((a: any) => a.status?.toLowerCase() === 'interview').length
          });
        })
        .catch(err => console.error('Failed to fetch stats:', err));
    }
  }, [userEmail]);

  const handleFileChange = async (e: DragEvent<HTMLDivElement> | React.ChangeEvent<HTMLInputElement>) => {
    const files = (e as DragEvent<HTMLDivElement>).dataTransfer?.files || (e as React.ChangeEvent<HTMLInputElement>).target.files;
    const file = files?.[0];
    if (!file) return;

    // Validate PDF only
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
      setError('Please upload a PDF file only. Other formats are not supported.');
      return;
    }

    setIsUploading(true);
    setError(null);
    try {
      // Just pass the file to parent - App.tsx handles upload
      onResumeUpload(file);
    } catch (err) {
      setError('Failed to upload resume');
      console.error('Upload failed:', err);
    } finally {
      setIsUploading(false);
      if ('target' in e) {
        (e.target as HTMLInputElement).value = '';
      }
    }
  };

  const handleTailor = async () => {
    if (!jobDescription.trim()) {
      setError('Please paste the job description');
      return;
    }

    setIsTailoring(true);
    setTailoredResumeUrl(null);
    setError(null);
    setMatchWarning(null);

    try {
      const result = await invokeAgent(
        [{ role: 'user', content: 'Tailor my resume for this job' }],
        userEmail || undefined,
        resume && 'backendPath' in resume ? { visual_path: resume.backendPath } : undefined,
        jobDescription
      );
      console.log('[TAILOR] Agent response:', result);
      console.log('[TAILOR] match_analysis:', result.match_analysis);
      console.log('[TAILOR] mismatched value:', result.match_analysis?.mismatched);
      console.log('[TAILOR] tailored_resume_path:', result.tailored_resume_path);

      if (result.status === 'error') {
        throw new Error(result.message || 'Failed to tailor resume');
      }

      // Check for mismatch
      if (result.match_analysis && result.match_analysis.mismatched === true) {
        console.log('[TAILOR] Mismatch detected!');
        setMatchWarning({
          type: 'mismatch',
          reason: 'The job description does not match your resume background.',
          score: 0
        });
        setError('Job description does not match your resume.');
        return;
      }

      if (result.tailored_resume_path) {
        console.log('[TAILOR] Setting download URL:', result.tailored_resume_path);
        setTailoredResumeUrl(result.tailored_resume_path);
      } else {
        setError('Failed to generate tailored resume.');
      }
    } catch (err) {
      console.error('[TAILOR] Error:', err);
      setError(err instanceof Error ? err.message : 'Failed to tailor resume');
    } finally {
      setIsTailoring(false);
    }
  };

  const handleAddManualJob = async () => {
    if (!manualJob.title.trim()) {
      setError('Please enter a job title');
      return;
    }

    setIsAddingJob(true);
    setError(null);

    try {
      const result = await saveJobLead({
        user_email: userEmail,
        company: manualJob.company || 'Unknown',
        job_title: manualJob.title,
        job_url: manualJob.url || null,
        job_description: manualJob.description || null,
        location: null,
        salary_info: null
      });
      if (!result.status || result.status !== 'success') {
        throw new Error(result.detail || 'Failed to add job');
      }

      // Reset form
      setManualJob({ title: '', company: '', url: '', description: '' });

      // Refresh stats immediately
      if (userEmail) {
        getApplications(userEmail).then(apps => {
          setStats({
            applications: apps.length,
            interviews: apps.filter((a: any) => a.status?.toLowerCase() === 'interview').length
          });
        });
      }
      
      // Show success message with Gmail configuration notice
      alert('✅ Job added successfully!\n\n📧 Status: Pending (Gmail not configured)\n\nTo enable automatic tracking:\n1. Go to Settings\n2. Connect your Gmail\n3. Add App Password\n\nStatus will change to "Tracking" after Gmail is connected.');
      
      // Redirect to applications page
      window.location.href = '/applications';
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add job');
    } finally {
      setIsAddingJob(false);
    }
  };

  return (
    <div className="home-page">
      <div className="page-header">
        <h1 className="page-title">Welcome back</h1>
        <p className="page-subtitle">Tailor your resume and track job applications with AI</p>
      </div>

      {error && (
        <div className="toast toast-error" style={{ position: 'relative', marginBottom: 'var(--space-lg)' }}>
          <span className="toast-icon">✕</span>
          <span className="toast-message">{error}</span>
          <button className="toast-close" onClick={() => setError(null)}>×</button>
        </div>
      )}

      <div className="bento-grid">
        {/* LEFT: Resume + Tailor */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">
              <span className="card-icon">📄</span>
              Resume & Job Match
            </h2>
          </div>
          <div className="card-body">
            <div className="resume-upload">
              {!hasResume ? (
                <div
                  className="upload-dropzone"
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => { e.preventDefault(); handleFileChange(e); }}
                >
                  <div className="upload-icon">📁</div>
                  <h3 className="upload-title">Upload your resume</h3>
                  <p className="upload-subtitle">Drag & drop or click to browse</p>
                  <label className="btn btn-primary btn-lg">
                    Choose File
                    <input
                      type="file"
                      accept=".pdf"
                      onChange={handleFileChange}
                      disabled={isUploading}
                      style={{ display: 'none' }}
                    />
                  </label>
                  <div className="upload-formats">
                    <span className="format-badge">PDF ONLY</span>
                  </div>
                </div>
              ) : (
                <div className="uploaded-state">
                  <div className="uploaded-header">
                    <span>✓</span>
                    <span>Resume uploaded</span>
                  </div>
                  <div className="uploaded-actions">
                    <button className="btn btn-secondary btn-sm" onClick={onOpenPreview}>
                      👁️ Preview
                    </button>
                    <button className="btn btn-danger btn-sm" onClick={onResumeRemove}>
                      🗑️ Remove
                    </button>
                  </div>
                </div>
              )}
            </div>

            <div style={{ marginTop: 'var(--space-xl)', borderTop: `1px solid var(--border-primary)` }} />

            <div className="jd-input-container" style={{ marginTop: 'var(--space-xl)' }}>
              <div>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: 'var(--space-sm)' }}>
                  Job Description
                </label>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem', marginBottom: 'var(--space-md)' }}>
                  Checks if you match the job, then tailors your resume
                </p>
                <textarea
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  placeholder="Paste the full job description here..."
                  rows={8}
                  className="jd-textarea"
                />
              </div>

              {matchWarning && (
                <div style={{ 
                  marginTop: 'var(--space-md)', 
                  padding: 'var(--space-md)', 
                  background: 'var(--danger-bg)', 
                  border: '1px solid var(--danger)', 
                  borderRadius: 'var(--radius-md)' 
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
                    <span style={{ fontSize: '1.25rem' }}>🚫</span>
                    <strong style={{ color: 'var(--danger)' }}>Not a Good Fit</strong>
                  </div>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--text-primary)', marginTop: 'var(--space-sm)' }}>
                    {matchWarning.reason}
                  </p>
                </div>
              )}

              <button
                className="btn btn-primary btn-block btn-lg"
                onClick={handleTailor}
                disabled={!hasResume || isTailoring || !jobDescription.trim()}
              >
                {isTailoring ? (
                  <><span className="spinner"></span> Checking & Tailoring...</>
                ) : (
                  '✨ Check & Tailor Resume'
                )}
              </button>

              {tailoredResumeUrl && (
                <div className="toast toast-success" style={{ position: 'relative', marginTop: 'var(--space-md)' }}>
                  <span className="toast-icon">✓</span>
                  <span className="toast-message">Resume tailored!</span>
                  <a href={tailoredResumeUrl} target="_blank" rel="noopener noreferrer" className="btn btn-success btn-sm">
                    📥 Download
                  </a>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* RIGHT: Add Job Manually */}
        <div>
          <div className="card" style={{ minHeight: '520px' }}>
            <div className="card-header">
              <h2 className="card-title">
                <span className="card-icon">🔗</span>
                Add Job to Track
              </h2>
            </div>
            <div className="card-body">
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: 'var(--space-md)' }}>
                Fill in the details below for AI-powered application tracking via Gmail
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
                <div>
                  <label style={{ display: 'block', fontWeight: 600, marginBottom: 'var(--space-xs)', fontSize: '0.875rem' }}>
                    Job Title <span style={{ color: 'var(--danger)' }}>*</span>
                  </label>
                  <input
                    type="text"
                    value={manualJob.title}
                    onChange={(e) => setManualJob({ ...manualJob, title: e.target.value })}
                    placeholder="e.g., Software Engineer"
                    className="url-input"
                    style={{ width: '100%' }}
                    required
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontWeight: 600, marginBottom: 'var(--space-xs)', fontSize: '0.875rem' }}>
                    Company <span style={{ color: 'var(--text-muted)' }}>(optional)</span>
                  </label>
                  <input
                    type="text"
                    value={manualJob.company}
                    onChange={(e) => setManualJob({ ...manualJob, company: e.target.value })}
                    placeholder="e.g., Acme Corp or Freelance"
                    className="url-input"
                    style={{ width: '100%' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontWeight: 600, marginBottom: 'var(--space-xs)', fontSize: '0.875rem' }}>
                    Job URL <span style={{ color: 'var(--text-muted)' }}>(optional)</span>
                  </label>
                  <input
                    type="url"
                    value={manualJob.url}
                    onChange={(e) => setManualJob({ ...manualJob, url: e.target.value })}
                    placeholder="https://linkedin.com/jobs/view/..."
                    className="url-input"
                    style={{ width: '100%' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontWeight: 600, marginBottom: 'var(--space-xs)', fontSize: '0.875rem' }}>
                    Job Description <span style={{ color: 'var(--text-muted)' }}>(optional)</span>
                  </label>
                  <textarea
                    value={manualJob.description}
                    onChange={(e) => setManualJob({ ...manualJob, description: e.target.value })}
                    placeholder="Paste job description for better AI tracking..."
                    rows={4}
                    className="jd-textarea"
                    style={{ minHeight: '80px' }}
                  />
                </div>

                <button
                  className="btn btn-primary btn-block"
                  onClick={handleAddManualJob}
                  disabled={!userEmail || isAddingJob || !manualJob.title}
                >
                  {isAddingJob ? <><span className="spinner"></span> Adding...</> : '➕ Add Job'}
                </button>

                {userEmail && (
                  <div style={{ marginTop: 'var(--space-md)', padding: 'var(--space-sm)', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', textAlign: 'center' }}>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      🔗 Jobs will be tracked via <strong>{userEmail}</strong>
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Quick Stats Card */}
          <div className="card" style={{ marginTop: 'var(--space-lg)' }}>
            <div className="card-header">
              <h2 className="card-title">
                <span className="card-icon">📊</span>
                Quick Stats
              </h2>
            </div>
            <div className="card-body">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-md)' }}>
                <div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 'var(--space-xs)' }}>Applications</p>
                  <p style={{ fontSize: '1.5rem', fontWeight: 700 }}>{stats.applications}</p>
                </div>
                <div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 'var(--space-xs)' }}>Interviews</p>
                  <p style={{ fontSize: '1.5rem', fontWeight: 700 }}>{stats.interviews}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
