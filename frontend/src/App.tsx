import { useState, useEffect } from 'react';
import { Routes, Route, NavLink } from 'react-router-dom';
import './App.css';
import Applications from './components/Applications';
import Settings from './components/Settings';
import Home from './pages/Home';

interface Application {
  id: number;
  job_id: number;
  company: string;
  job_title: string;
  job_url: string;
  applied_at: string;
  status: string;
  notes?: string;
}

interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
}

function App() {
  const [userEmail, setUserEmail] = useState<string | null>(localStorage.getItem('userEmail'));
  const [resume, setResume] = useState<File | null>(null);
  const [resumePreview, setResumePreview] = useState<string | null>(null);
  const [applications, setApplications] = useState<Application[]>([]);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [tailoredResumePath, setTailoredResumePath] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [showEmailModal, setShowEmailModal] = useState(false);

  // Toast notification helper
  const showToast = (message: string, type: 'success' | 'error' | 'info' | 'warning' = 'info', duration: number = 5000) => {
    const id = `toast-${Date.now()}-${Math.random()}`;
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, duration);
  };

  const removeToast = (id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  useEffect(() => {
    if (userEmail) {
      loadApplications();
    }
  }, [userEmail]);

  const loadApplications = async () => {
    if (!userEmail) return;
    try {
      const res = await fetch(`/api/applications?email=${encodeURIComponent(userEmail)}`);
      const data = await res.json();
      setApplications(data);
    } catch (err) {
      console.error('Failed to load applications', err);
    }
  };

  const handleResumeUpload = async (file: File) => {
    setResume(file);
    const previewUrl = URL.createObjectURL(file);
    setResumePreview(previewUrl);

    try {
      const formData = new FormData();
      formData.append('file', file);
      if (userEmail) formData.append('email', userEmail);

      const uploadRes = await fetch('/api/resume/upload', { method: 'POST', body: formData });
      if (uploadRes.ok) {
        const result = await uploadRes.json();
        setResume((prev) => {
          if (prev) {
            return Object.assign(prev, { backendPath: result.file_path });
          }
          return prev;
        });
        showToast('Resume uploaded successfully', 'success');
      }
    } catch (err) {
      console.error('[DEBUG] Upload error:', err);
      showToast('Failed to upload resume', 'error');
    }
  };

  const handleRemoveResume = () => {
    if (resumePreview) URL.revokeObjectURL(resumePreview);
    setResume(null);
    setResumePreview(null);
    showToast('Resume removed', 'info');
  };

  const handleConnectEmail = () => {
    setShowEmailModal(true);
  };

  const handleEmailSubmit = (email: string) => {
    localStorage.setItem('userEmail', email);
    setUserEmail(email);
    setShowEmailModal(false);
    showToast(`Connected to ${email}`, 'success');
  };

  const handleLogout = () => {
    localStorage.removeItem('userEmail');
    setUserEmail(null);
    setResume(null);
    if (resumePreview) URL.revokeObjectURL(resumePreview);
    setResumePreview(null);
    showToast('Logged out successfully', 'info');
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-brand">
          <h1>Anti-Berojgar</h1>
        </div>
        <div className="header-actions">
          {userEmail ? (
            <>
              <span className="user-email">{userEmail}</span>
              <button className="btn btn-ghost btn-sm" onClick={handleLogout}>Logout</button>
            </>
          ) : (
            <button className="btn btn-primary btn-sm" onClick={handleConnectEmail}>
              Connect Email
            </button>
          )}
        </div>
      </header>

      <nav className="nav">
        <NavLink to="/">Home</NavLink>
        <NavLink to="/applications">My Applications</NavLink>
        <NavLink to="/settings">Settings</NavLink>
      </nav>

      <main className="main">
        <Routes>
          <Route
            path="/"
            element={
              <Home
                hasResume={!!resume}
                resume={resume}
                userEmail={userEmail}
                onResumeUpload={handleResumeUpload}
                onResumeRemove={handleRemoveResume}
                onOpenPreview={() => setShowPreview(true)}
              />
            }
          />
          <Route 
            path="/applications" 
            element={
              <Applications 
                userEmail={userEmail} 
                applications={applications} 
                onLoad={loadApplications}
              /> 
            } 
          />
          <Route path="/settings" element={<Settings userEmail={userEmail} onEmailChange={setUserEmail} />} />
        </Routes>
      </main>

      {/* Email Connect Modal */}
      {showEmailModal && (
        <div className="modal-overlay" onClick={() => setShowEmailModal(false)}>
          <div className="modal-content modal-small" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>📧 Connect Your Email</h3>
              <button className="modal-close" onClick={() => setShowEmailModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <p className="modal-description">
                Enter your Gmail address to track job application responses. We'll monitor your inbox for updates.
              </p>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  const email = (e.currentTarget.elements[0] as HTMLInputElement).value;
                  if (email) handleEmailSubmit(email);
                }}
              >
                <input
                  type="email"
                  placeholder="your.email@gmail.com"
                  required
                  className="input-full"
                  autoFocus
                />
                <button type="submit" className="btn btn-primary btn-block" style={{ marginTop: '1rem' }}>
                  Connect Email
                </button>
              </form>
              <p className="modal-hint">
                🔒 Your email is stored locally and only used for application tracking
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Resume Preview Modal */}
      {showPreview && resume && resumePreview && (
        <div className="modal-overlay resume-preview" onClick={() => setShowPreview(false)}>
          <div className="modal-content resume-preview-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>📄 Resume Preview</h3>
              <button className="modal-close" onClick={() => setShowPreview(false)}>×</button>
            </div>
            <div className="modal-body">
              {resume.type === 'application/pdf' ? (
                <iframe src={resumePreview} title="Resume Preview" className="preview-frame" />
              ) : (
                <img src={resumePreview} alt="Resume Preview" className="preview-image" />
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-primary" onClick={() => setShowPreview(false)}>Close</button>
            </div>
          </div>
        </div>
      )}

      {/* Toast Notifications */}
      <div className="toast-container">
        {toasts.map(toast => (
          <div key={toast.id} className={`toast toast-${toast.type}`}>
            <div className="toast-content">
              <span className="toast-icon">
                {toast.type === 'success' && '✓'}
                {toast.type === 'error' && '✕'}
                {toast.type === 'warning' && '⚠'}
                {toast.type === 'info' && 'ℹ'}
              </span>
              <span className="toast-message">{toast.message}</span>
            </div>
            <button className="toast-close" onClick={() => removeToast(toast.id)}>×</button>
          </div>
        ))}
      </div>

      {/* Tailored Resume Download (sticky) */}
      {tailoredResumePath && (
        <div className="sticky-download">
          <div>
            <strong>✓ Resume Tailored!</strong>
            <span>Your customized resume is ready</span>
          </div>
          <a href={tailoredResumePath} target="_blank" rel="noopener noreferrer" className="btn btn-primary btn-sm">
            📥 Download PDF
          </a>
          <button className="btn btn-ghost btn-sm" onClick={() => setTailoredResumePath(null)}>×</button>
        </div>
      )}
    </div>
  );
}

export default App;
