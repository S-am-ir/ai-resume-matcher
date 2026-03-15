import React, { useState, useEffect } from 'react';

interface SettingsProps {
  userEmail: string | null;
  onEmailChange: (email: string | null) => void;
}

export default function Settings({ userEmail, onEmailChange }: SettingsProps) {
  const [imapPassword, setImapPassword] = useState('');
  const [isConfigured, setIsConfigured] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);

  useEffect(() => {
    if (userEmail) {
      fetch(`/api/settings/email?email=${encodeURIComponent(userEmail)}`)
        .then(res => res.json())
        .then(data => setIsConfigured(data.has_password))
        .catch(console.error);
    }
  }, [userEmail]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userEmail || !imapPassword.trim()) return;

    setIsSaving(true);
    setSaveMessage(null);
    try {
      const response = await fetch('/api/settings/email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_email: userEmail,
          imap_password: imapPassword
        })
      });
      
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.detail || 'Failed to save');
      }
      
      setIsConfigured(true);
      setImapPassword('');
      setSaveMessage({ type: 'success', text: 'Gmail connected successfully! Auto-tracking is now active.' });
    } catch (err) {
      setSaveMessage({ type: 'error', text: err instanceof Error ? err.message : 'Failed to save settings' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDisconnect = () => {
    if (confirm('Are you sure you want to disconnect your email? Auto-tracking will stop.')) {
      onEmailChange(null);
      setIsConfigured(false);
      setSaveMessage({ type: 'success', text: 'Email disconnected. Auto-tracking stopped.' });
    }
  };

  const handleReset = async () => {
    if (confirm('Reset tracking? This will:\n\n• Clear Gmail configuration\n• Set all jobs back to "Pending"\n• Stop auto-tracking\n\nYou can re-connect Gmail later.')) {
      try {
        const response = await fetch('/api/users/reset-tracking', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_email: userEmail, imap_password: '' })
        });
        
        const result = await response.json();
        
        if (response.ok) {
          setIsConfigured(false);
          setSaveMessage({ type: 'success', text: result.message });
        } else {
          setSaveMessage({ type: 'error', text: result.detail || 'Failed to reset' });
        }
      } catch (err) {
        setSaveMessage({ type: 'error', text: 'Failed to reset tracking' });
      }
    }
  };

  const handleDeleteAccount = async () => {
    if (confirm('⚠️ WARNING: This will PERMANENTLY delete:\n\n• Your account\n• All job applications\n• All tracking data\n• Gmail configuration\n\nThis CANNOT be undone!')) {
      const confirmText = prompt('Type "DELETE" to confirm:');
      if (confirmText === 'DELETE') {
        try {
          const response = await fetch(`/api/users/${encodeURIComponent(userEmail || '')}`, {
            method: 'DELETE'
          });
          
          const result = await response.json();
          
          if (response.ok) {
            onEmailChange(null);
            alert('Account deleted successfully.');
            window.location.href = '/';
          } else {
            setSaveMessage({ type: 'error', text: result.detail || 'Failed to delete' });
          }
        } catch (err) {
          setSaveMessage({ type: 'error', text: 'Failed to delete account' });
        }
      }
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle">Configure your Gmail for automatic application tracking</p>
      </div>

      {/* Gmail Configuration Card */}
      <div className="card" style={{ maxWidth: '700px', margin: '0 auto' }}>
        <div className="card-header">
          <h2 className="card-title">
            <span className="card-icon">📧</span>
            Gmail Integration
          </h2>
        </div>

        <div className="card-body">
          {userEmail ? (
            <>
              {/* Connection Status */}
              <div style={{ 
                padding: 'var(--space-md)', 
                background: isConfigured ? 'var(--success-bg)' : 'var(--warning-bg)', 
                borderRadius: 'var(--radius-md)',
                marginBottom: 'var(--space-lg)',
                border: `1px solid ${isConfigured ? 'var(--success)' : 'var(--warning)'}`
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', marginBottom: 'var(--space-xs)' }}>
                  <span style={{ fontSize: '1.5rem' }}>{isConfigured ? '✅' : '⚠️'}</span>
                  <div>
                    <div style={{ fontWeight: 600, color: isConfigured ? 'var(--success)' : 'var(--warning)' }}>
                      {isConfigured ? 'Gmail Connected' : 'Gmail Not Configured'}
                    </div>
                    <div style={{ fontSize: '0.8125rem', opacity: 0.8 }}>
                      {isConfigured ? 'Auto-tracking is active' : 'Auto-tracking is disabled'}
                    </div>
                  </div>
                </div>
                {isConfigured && (
                  <div style={{ fontSize: '0.8125rem', marginTop: 'var(--space-sm)', paddingTop: 'var(--space-sm)', borderTop: `1px solid var(--success)` }}>
                    <strong>Connected:</strong> {userEmail}
                  </div>
                )}
              </div>

              {/* Success/Error Messages */}
              {saveMessage && (
                <div style={{ 
                  padding: 'var(--space-md)', 
                  background: saveMessage.type === 'success' ? 'var(--success-bg)' : 'var(--danger-bg)', 
                  borderRadius: 'var(--radius-md)',
                  marginBottom: 'var(--space-lg)',
                  border: `1px solid ${saveMessage.type === 'success' ? 'var(--success)' : 'var(--danger)'}`,
                  color: saveMessage.type === 'success' ? 'var(--success)' : 'var(--danger)'
                }}>
                  {saveMessage.text}
                </div>
              )}

              {/* Configuration Form */}
              {!isConfigured && (
                <form onSubmit={handleSave}>
                  <div style={{ marginBottom: 'var(--space-lg)' }}>
                    <label style={{ display: 'block', fontWeight: 600, marginBottom: 'var(--space-sm)' }}>
                      Gmail App Password
                    </label>
                    <input
                      type="password"
                      value={imapPassword}
                      onChange={(e) => setImapPassword(e.target.value)}
                      placeholder="16-character code from Google"
                      style={{
                        width: '100%',
                        padding: 'var(--space-md)',
                        background: 'var(--bg-tertiary)',
                        border: '1px solid var(--border-primary)',
                        borderRadius: 'var(--radius-md)',
                        color: 'var(--text-primary)',
                        fontFamily: 'monospace',
                        fontSize: '0.9375rem',
                        marginBottom: 'var(--space-sm)'
                      }}
                    />
                    <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
                      Enter the 16-character App Password from Google (e.g., "abcd efgh ijkl mnop")
                    </p>
                  </div>

                  <div style={{ display: 'flex', gap: 'var(--space-md)' }}>
                    <button
                      type="submit"
                      className="btn btn-primary"
                      disabled={isSaving || !imapPassword.trim()}
                      style={{
                        background: 'var(--primary)',
                        color: 'white',
                        padding: 'var(--space-md) var(--space-lg)',
                        minWidth: '120px'
                      }}
                    >
                      {isSaving ? 'Connecting...' : 'Connect Gmail'}
                    </button>
                    <button
                      type="button"
                      className="btn btn-ghost"
                      onClick={() => window.open('https://myaccount.google.com/apppasswords', '_blank')}
                      style={{
                        background: 'var(--bg-tertiary)',
                        color: 'var(--text-primary)',
                        padding: 'var(--space-md) var(--space-lg)'
                      }}
                    >
                      Get App Password →
                    </button>
                  </div>
                </form>
              )}

              {/* Action Buttons */}
              {isConfigured && (
                <div style={{ display: 'flex', gap: 'var(--space-md)', flexWrap: 'wrap' }}>
                  <button
                    className="btn btn-danger"
                    onClick={handleDisconnect}
                    style={{
                      background: 'var(--danger-bg)',
                      color: 'var(--danger)',
                      border: '1px solid var(--danger)',
                      padding: 'var(--space-md) var(--space-lg)'
                    }}
                  >
                    Disconnect Gmail
                  </button>
                  <button
                    className="btn btn-ghost"
                    onClick={handleReset}
                    style={{
                      background: 'var(--warning-bg)',
                      color: 'var(--warning)',
                      border: '1px solid var(--warning)',
                      padding: 'var(--space-md) var(--space-lg)'
                    }}
                  >
                    🔄 Reset Tracking
                  </button>
                  <button
                    className="btn btn-ghost"
                    onClick={handleDeleteAccount}
                    style={{
                      background: 'var(--bg-tertiary)',
                      color: 'var(--danger)',
                      border: '1px solid var(--danger)',
                      padding: 'var(--space-md) var(--space-lg)'
                    }}
                  >
                    🗑️ Delete Account
                  </button>
                </div>
              )}
            </>
          ) : (
            <div style={{ textAlign: 'center', padding: 'var(--space-xl)' }}>
              <div style={{ fontSize: '3rem', marginBottom: 'var(--space-md)' }}>🔐</div>
              <h3 style={{ marginBottom: 'var(--space-sm)' }}>Connect Your Email First</h3>
              <p style={{ color: 'var(--text-secondary)', marginBottom: 'var(--space-lg)' }}>
                Click "Connect Email" in the header to get started with auto-tracking
              </p>
            </div>
          )}
        </div>
      </div>

      {/* How to Configure Card */}
      <div className="card" style={{ maxWidth: '700px', margin: 'var(--space-xl) auto 0' }}>
        <div className="card-header">
          <h2 className="card-title">
            <span className="card-icon">📋</span>
            How to Configure Gmail for Auto-Tracking
          </h2>
        </div>
        <div className="card-body">
          <div style={{ 
            padding: 'var(--space-md)', 
            background: 'var(--info-bg)', 
            border: '1px solid var(--info)', 
            borderRadius: 'var(--radius-md)',
            marginBottom: 'var(--space-lg)'
          }}>
            <strong>ℹ️ Why Connect Gmail?</strong>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: 'var(--space-xs)' }}>
              Once connected, the AI automatically monitors your Gmail every 60 minutes for interview invites, offers, and rejections. 
              Status updates happen automatically - no manual work needed! 📧 icon appears when you receive a response.
            </p>
          </div>

          <div style={{ display: 'grid', gap: 'var(--space-md)' }}>
            <div style={{ display: 'flex', gap: 'var(--space-md)', alignItems: 'flex-start' }}>
              <div style={{ 
                width: '32px', 
                height: '32px', 
                background: 'var(--primary-bg)', 
                borderRadius: 'var(--radius-full)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--primary)',
                fontWeight: 700,
                flexShrink: 0
              }}>1</div>
              <div>
                <div style={{ fontWeight: 600, marginBottom: 'var(--space-xs)' }}>Enable 2-Factor Authentication</div>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                  Go to{' '}
                  <a href="https://myaccount.google.com/security" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--primary)', textDecoration: 'underline' }}>
                    Google Account Security
                  </a>{' '}
                  → Enable 2-Step Verification (required for App Passwords)
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 'var(--space-md)', alignItems: 'flex-start' }}>
              <div style={{ 
                width: '32px', 
                height: '32px', 
                background: 'var(--primary-bg)', 
                borderRadius: 'var(--radius-full)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--primary)',
                fontWeight: 700,
                flexShrink: 0
              }}>2</div>
              <div>
                <div style={{ fontWeight: 600, marginBottom: 'var(--space-xs)' }}>Generate App Password</div>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                  Go to{' '}
                  <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--primary)', textDecoration: 'underline' }}>
                    App Passwords Page
                  </a>{' '}
                  → Select app: "Mail" → Select device: "Other" → Enter "Anti-Berojgar" → Click Generate
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 'var(--space-md)', alignItems: 'flex-start' }}>
              <div style={{ 
                width: '32px', 
                height: '32px', 
                background: 'var(--primary-bg)', 
                borderRadius: 'var(--radius-full)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--primary)',
                fontWeight: 700,
                flexShrink: 0
              }}>3</div>
              <div>
                <div style={{ fontWeight: 600, marginBottom: 'var(--space-xs)' }}>Copy 16-Character Password</div>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                  Google will show a 16-character code (e.g., "abcd efgh ijkl mnop"). Copy this - you'll only see it once!
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 'var(--space-md)', alignItems: 'flex-start' }}>
              <div style={{ 
                width: '32px', 
                height: '32px', 
                background: 'var(--primary-bg)', 
                borderRadius: 'var(--radius-full)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--primary)',
                fontWeight: 700,
                flexShrink: 0
              }}>4</div>
              <div>
                <div style={{ fontWeight: 600, marginBottom: 'var(--space-xs)' }}>Paste Above & Connect</div>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                  Paste the 16-character code in the form above and click "Connect Gmail". Auto-tracking will start immediately!
                </div>
              </div>
            </div>
          </div>

          {/* Security Note */}
          <div style={{ 
            marginTop: 'var(--space-lg)', 
            padding: 'var(--space-md)', 
            background: 'var(--bg-tertiary)', 
            borderRadius: 'var(--radius-md)',
            fontSize: '0.8125rem',
            color: 'var(--text-secondary)'
          }}>
            <strong>🔒 Security:</strong> App Passwords are read-only (can't send emails), are encrypted in our database, and can be revoked anytime from your Google Account.
          </div>
        </div>
      </div>
    </div>
  );
}
