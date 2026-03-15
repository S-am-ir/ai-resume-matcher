import { useState, DragEvent } from 'react';

interface DashboardProps {
  resume: File | null;
  onResumeUpload: (file: File) => void;
  onPreviewResume: () => void;
  onRemoveResume: () => void;
}

export default function Dashboard({
  resume,
  onResumeUpload,
  onPreviewResume,
  onRemoveResume
}: DashboardProps) {
  const [dragOver, setDragOver] = useState(false);

  const handleDrag = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragOver(true);
    } else if (e.type === 'dragleave') {
      setDragOver(false);
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.type === 'application/pdf' || file.type.startsWith('image/') || file.name.endsWith('.pdf') || file.name.endsWith('.png') || file.name.endsWith('.jpg') || file.name.endsWith('.jpeg')) {
        onResumeUpload(file);
      }
    }
  };

  const handleFileChange = (e: DragEvent<HTMLDivElement> | React.ChangeEvent<HTMLInputElement>) => {
    const files = (e as DragEvent<HTMLDivElement>).dataTransfer?.files || (e as React.ChangeEvent<HTMLInputElement>).target.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.type === 'application/pdf' || file.type.startsWith('image/') || file.name.endsWith('.pdf') || file.name.endsWith('.png') || file.name.endsWith('.jpg') || file.name.endsWith('.jpeg')) {
        onResumeUpload(file);
      }
    }
  };

  return (
    <div className="dashboard">
      <div className="welcome-card">
        <h1>Welcome to Anti-Berojgar</h1>
        <p>Your AI-powered resume tailoring and application tracking assistant.</p>
      </div>

      <div className="features-grid">
        {/* Resume Upload */}
        <div className="feature-card">
          <div className="feature-icon">📄</div>
          <h3>Upload Resume</h3>
          {!resume ? (
            <div
              className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <p>Drag & drop your resume here</p>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>or</p>
              <label className="btn btn-primary">
                Browse Files
                <input type="file" accept=".pdf,.png,.jpg,.jpeg" onChange={handleFileChange} style={{ display: 'none' }} />
              </label>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>PDF, PNG, JPG</p>
            </div>
          ) : (
            <div className="resume-uploaded">
              <div style={{ padding: '1rem', background: 'var(--success-light)', borderRadius: 'var(--radius-md)', marginBottom: '1rem' }}>
                <strong style={{ color: 'var(--success)' }}>✓ Resume Uploaded</strong>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', flexDirection: 'column' }}>
                <button className="btn btn-ghost" onClick={onPreviewResume}>👁️ Preview</button>
                <button className="btn btn-ghost" onClick={onRemoveResume}>🗑️ Remove</button>
              </div>
            </div>
          )}
        </div>

        {/* Tailor Resume */}
        <div className="feature-card">
          <div className="feature-icon">✨</div>
          <h3>Tailor Resume</h3>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
            Paste a job description to customize your resume for that specific role.
          </p>
          <p style={{ fontSize: '0.875rem', color: resume ? 'var(--success)' : 'var(--warning)' }}>
            {resume ? '✓ Ready to tailor' : '⚠️ Upload resume first'}
          </p>
        </div>

        {/* Track Applications */}
        <div className="feature-card">
          <div className="feature-icon">📊</div>
          <h3>Track Applications</h3>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
            Monitor your job applications and get notified when companies respond.
          </p>
          <a href="/applications" className="btn btn-primary">View Applications →</a>
        </div>
      </div>
    </div>
  );
}
