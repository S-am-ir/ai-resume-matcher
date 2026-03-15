import { useState, useEffect } from 'react';

interface Application {
  id: number;
  job_id: number;
  company: string;
  job_title: string;
  job_url: string;
  applied_at: string;
  status: string;
  notes?: string;
  gmail_message_id?: string;
  last_checked_at?: string;
}

interface ApplicationsProps {
  userEmail: string | null;
  applications: Application[];
  onLoad: () => void;
}

export default function Applications({ userEmail, applications, onLoad }: ApplicationsProps) {
  const [filter, setFilter] = useState('all');
  const [gmailConfigured, setGmailConfigured] = useState(false);

  // Auto-refresh applications every 60 seconds (agent tracks in background)
  useEffect(() => {
    if (userEmail) {
      const interval = setInterval(() => {
        onLoad();
      }, 60000); // Check every 60 seconds
      return () => clearInterval(interval);
    }
  }, [userEmail, onLoad]);

  // Check if Gmail is configured
  useEffect(() => {
    if (userEmail) {
      fetch(`/api/settings/email?email=${encodeURIComponent(userEmail)}`)
        .then(res => res.json())
        .then(data => setGmailConfigured(data.has_password))
        .catch(() => setGmailConfigured(false));
    }
  }, [userEmail]);

  const filteredApps = applications.filter(app => {
    if (filter === 'all') return true;
    return app.status.toLowerCase() === filter.toLowerCase();
  });

  const getStatusStyle = (status: string) => {
    switch (status.toLowerCase()) {
      case 'pending':
        return { bg: 'var(--bg-tertiary)', color: 'var(--text-muted)' };
      case 'tracking':
        return { bg: 'var(--warning-bg)', color: 'var(--warning)' };
      case 'interview':
        return { bg: 'var(--info-bg)', color: 'var(--info)' };
      case 'offered':
        return { bg: 'var(--success-bg)', color: 'var(--success)' };
      case 'rejected':
        return { bg: 'var(--danger-bg)', color: 'var(--danger)' };
      case 'ghosted':
        return { bg: 'var(--bg-tertiary)', color: 'var(--text-muted)' };
      case 'follow up':
        return { bg: 'var(--warning-bg)', color: 'var(--warning)' };
      default:
        return { bg: 'var(--info-bg)', color: 'var(--info)' };
    }
  };

  const getGmailLink = (app: Application) => {
    // Only show email link if agent found a response (gmail_message_id exists)
    if (app.gmail_message_id && ['interview', 'offered', 'rejected'].includes(app.status.toLowerCase())) {
      return `https://mail.google.com/mail/u/0/#all/${app.gmail_message_id}`;
    }
    return null;
  };

  const handleDelete = async (appId: number) => {
    if (!confirm('Are you sure you want to delete this application?')) return;
    
    try {
      const res = await fetch(`/api/applications/${appId}?email=${encodeURIComponent(userEmail || '')}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        onLoad(); // Refresh the list
      } else {
        alert('Failed to delete application');
      }
    } catch (err) {
      console.error('Delete error:', err);
      alert('Failed to delete application');
    }
  };

  if (!userEmail) {
    return (
      <div className="page-container">
        <div className="empty-state">
          <div className="empty-icon">🔐</div>
          <h3>Connect Email First</h3>
          <p>Connect your Gmail to enable AI-powered application tracking</p>
          <a href="/settings" className="btn btn-primary btn-lg">Go to Settings</a>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header-row">
        <div>
          <h1 className="page-title">My Applications</h1>
          <p className="page-subtitle" style={{ marginBottom: 'var(--space-md)' }}>AI-powered tracking via Gmail</p>
        </div>
        {/* Removed manual Check Gmail button - agent tracks automatically */}
      </div>

      {/* Filter Tabs */}
      <div className="filter-tabs" style={{ marginTop: 'var(--space-md)' }}>
        {['all', 'pending', 'tracking', 'interview', 'offered', 'rejected', 'ghosted', 'follow up'].map(status => (
          <button
            key={status}
            className={`filter-tab ${filter === status ? 'active' : ''}`}
            onClick={() => setFilter(status)}
          >
            {status.charAt(0).toUpperCase() + status.slice(1)}
            {status !== 'all' && (
              <span className="filter-count">
                {applications.filter(a => a.status.toLowerCase() === status).length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Info Banner - Different messages based on Gmail config */}
      <div style={{ 
        padding: 'var(--space-md)', 
        background: gmailConfigured ? 'var(--info-bg)' : 'var(--warning-bg)', 
        border: `1px solid ${gmailConfigured ? 'var(--info)' : 'var(--warning)'}`, 
        borderRadius: 'var(--radius-md)',
        marginBottom: 'var(--space-lg)',
        fontSize: '0.8125rem',
        color: 'var(--text-primary)'
      }}>
        {gmailConfigured ? (
          <div>
            <strong>ℹ️ AI Tracking Active:</strong> The system monitors your Gmail for responses. 
            Status updates automatically when interview invites, offers, or rejections are detected. 
            📧 Icon appears when you receive a response - click to view the email.
          </div>
        ) : (
          <div>
            <strong>⚠️ Gmail Not Configured:</strong> Automatic tracking is disabled. 
            Status updates will NOT happen automatically until you connect your Gmail.
            {' '}
            <a href="/settings" style={{ color: 'var(--primary)', fontWeight: 600, textDecoration: 'underline' }}>
              Go to Settings to enable auto-tracking →
            </a>
          </div>
        )}
      </div>

      {/* Applications Grid */}
      {filteredApps.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📭</div>
          <h3>No applications yet</h3>
          <p>
            {applications.length === 0
              ? "Add jobs from the home page to start tracking"
              : "No applications match this filter"}
          </p>
          {applications.length === 0 && (
            <a href="/" className="btn btn-primary btn-lg">Add Your First Job</a>
          )}
        </div>
      ) : (
        <div className="applications-grid">
          {filteredApps.map(app => {
            const statusStyle = getStatusStyle(app.status);
            const gmailLink = getGmailLink(app);
            
            // Calculate days since application
            const daysSinceApplied = app.applied_at 
              ? Math.floor((Date.now() - new Date(app.applied_at).getTime()) / (1000 * 60 * 60 * 24))
              : 0;

            return (
              <div key={app.id} className="application-card">
                <div className="app-header">
                  <div>
                    <h3 className="app-title">{app.job_title}</h3>
                    <p className="app-company">{app.company}</p>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
                    <span
                      className="status-badge"
                      style={{ background: statusStyle.bg, color: statusStyle.color }}
                    >
                      {app.status}
                    </span>
                    <button
                      onClick={() => handleDelete(app.id)}
                      title="Delete application"
                      style={{
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        fontSize: '1.25rem',
                        padding: 'var(--space-xs)',
                        opacity: 0.6,
                        transition: 'opacity 0.2s'
                      }}
                    >
                      🗑️
                    </button>
                  </div>
                </div>

                {app.job_url && (
                  <a href={app.job_url} target="_blank" rel="noopener noreferrer" className="app-link">
                    🔗 View Job Posting ↗
                  </a>
                )}

                {/* Email Response Icon - ONLY appears when agent found a response */}
                {gmailLink && (
                  <a 
                    href={gmailLink} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="app-link"
                    style={{ 
                      display: 'inline-flex', 
                      alignItems: 'center', 
                      gap: 'var(--space-xs)', 
                      marginTop: 'var(--space-sm)',
                      fontWeight: 600,
                      color: 'var(--primary)'
                    }}
                    title="View email response from company"
                  >
                    📧 View Response Email ↗
                  </a>
                )}

                {/* Follow Up or Ghosted Notice */}
                {(app.status.toLowerCase() === 'follow up' || app.status.toLowerCase() === 'ghosted') && (
                  <div style={{ 
                    fontSize: '0.75rem', 
                    color: 'var(--text-muted)', 
                    padding: 'var(--space-sm)',
                    background: 'var(--bg-tertiary)',
                    borderRadius: 'var(--radius-sm)',
                    marginTop: 'var(--space-sm)'
                  }}>
                    {app.status.toLowerCase() === 'follow up' 
                      ? `⏰ No response in ${daysSinceApplied} days. Consider sending a follow-up email.`
                      : `👻 No response in ${daysSinceApplied} days. This position may be closed.`
                    }
                  </div>
                )}

                {/* Notes from Agent */}
                {app.notes && (
                  <div style={{ 
                    fontSize: '0.75rem', 
                    color: 'var(--text-muted)', 
                    marginBottom: 'var(--space-md)',
                    padding: 'var(--space-sm)',
                    background: 'var(--bg-tertiary)',
                    borderRadius: 'var(--radius-sm)'
                  }}>
                    {app.notes.length > 100 ? app.notes.substring(0, 100) + '...' : app.notes}
                  </div>
                )}

                <div className="app-meta">
                  <span className="app-date">
                    📅 Applied {new Date(app.applied_at).toLocaleDateString('en-US', { 
                      month: 'short', 
                      day: 'numeric' 
                    })}
                  </span>
                  {app.last_checked_at && (
                    <span className="app-date" style={{ fontSize: '0.6875rem' }}>
                      Last checked: {new Date(app.last_checked_at).toLocaleTimeString('en-US', { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                      })}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
