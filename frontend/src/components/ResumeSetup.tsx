import React, { useState, useRef } from 'react';
import '../App.css';

interface TargetRole {
  id: string;
  title: string;
  companies: string[];
  keywords: string[];
}

export const ResumeSetup: React.FC<{ userEmail: string | null }> = ({ userEmail }) => {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [targetRoles, setTargetRoles] = useState<TargetRole[]>([]);
  const [newRole, setNewRole] = useState({ title: '', companies: '', keywords: '' });
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleFileSelect = (file: File) => {
    if (file.type === 'application/pdf' || file.type.includes('document')) {
      setUploadedFile(file);
      simulateUpload();
    } else {
      alert('Please upload a PDF or document file');
    }
  };

  const simulateUpload = () => {
    let progress = 0;
    const interval = setInterval(() => {
      progress += 10;
      setUploadProgress(progress);
      if (progress >= 100) {
        clearInterval(interval);
      }
    }, 100);
  };

  const handleAddRole = () => {
    if (newRole.title) {
      const role: TargetRole = {
        id: Date.now().toString(),
        title: newRole.title,
        companies: newRole.companies.split(',').map(c => c.trim()).filter(Boolean),
        keywords: newRole.keywords.split(',').map(k => k.trim()).filter(Boolean),
      };
      setTargetRoles([...targetRoles, role]);
      setNewRole({ title: '', companies: '', keywords: '' });
    }
  };

  const handleRemoveRole = (id: string) => {
    setTargetRoles(targetRoles.filter(r => r.id !== id));
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Resume Setup</h1>
        <p>Upload your resume and configure target roles for AI tailoring</p>
      </div>

      {!userEmail && (
        <div className="notification warning">
          ⚠ Please connect your email to save your resume
        </div>
      )}

      <div className="resume-sections">
        <section className="resume-upload-section">
          <h2>📄 Upload Resume</h2>
          <div
            className={`drop-zone ${isDragging ? 'dragging' : ''} ${uploadedFile ? 'has-file' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            {uploadedFile ? (
              <div className="file-info">
                <span className="file-icon">📎</span>
                <div className="file-details">
                  <p className="file-name">{uploadedFile.name}</p>
                  <p className="file-size">{(uploadedFile.size / 1024).toFixed(2)} KB</p>
                </div>
                {uploadProgress < 100 && (
                  <div className="upload-progress">
                    <div className="progress-bar" style={{ width: `${uploadProgress}%` }}></div>
                    <span>{uploadProgress}%</span>
                  </div>
                )}
                {uploadProgress === 100 && (
                  <span className="upload-complete">✓ Uploaded</span>
                )}
              </div>
            ) : (
              <div className="drop-content">
                <span className="drop-icon">📁</span>
                <p>Drag & drop your resume here</p>
                <p className="drop-subtext">or click to browse</p>
                <p className="drop-formats">Supported: PDF, DOC, DOCX</p>
              </div>
            )}
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.doc,.docx"
              onChange={(e) => e.target.files && handleFileSelect(e.target.files[0])}
              style={{ display: 'none' }}
            />
          </div>
          {uploadedFile && uploadProgress === 100 && (
            <div className="upload-actions">
              <button className="btn btn-secondary">Preview</button>
              <button className="btn btn-danger">Remove</button>
            </div>
          )}
        </section>

        <section className="target-roles-section">
          <h2>🎯 Target Roles</h2>
          <p className="section-description">
            Define your target job roles so the AI can tailor your resume accordingly
          </p>

          <div className="add-role-form">
            <div className="form-row">
              <div className="form-group">
                <label>Role Title</label>
                <input
                  type="text"
                  value={newRole.title}
                  onChange={(e) => setNewRole({ ...newRole, title: e.target.value })}
                  placeholder="e.g., Senior Frontend Developer"
                />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Target Companies (comma-separated)</label>
                <input
                  type="text"
                  value={newRole.companies}
                  onChange={(e) => setNewRole({ ...newRole, companies: e.target.value })}
                  placeholder="e.g., Google, Microsoft, Amazon"
                />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Key Skills/Keywords (comma-separated)</label>
                <textarea
                  value={newRole.keywords}
                  onChange={(e) => setNewRole({ ...newRole, keywords: e.target.value })}
                  placeholder="e.g., React, TypeScript, Node.js, AWS"
                  rows={2}
                />
              </div>
            </div>
            <button className="btn btn-primary" onClick={handleAddRole}>
              + Add Target Role
            </button>
          </div>

          <div className="roles-list">
            {targetRoles.length === 0 ? (
              <div className="empty-state">
                <p>No target roles added yet</p>
              </div>
            ) : (
              targetRoles.map((role) => (
                <div key={role.id} className="role-card">
                  <div className="role-header">
                    <h3>{role.title}</h3>
                    <button
                      className="remove-btn"
                      onClick={() => handleRemoveRole(role.id)}
                    >
                      ×
                    </button>
                  </div>
                  <div className="role-content">
                    {role.companies.length > 0 && (
                      <div className="role-section">
                        <strong>Companies:</strong>
                        <div className="tags">
                          {role.companies.map((company, i) => (
                            <span key={i} className="tag">{company}</span>
                          ))}
                        </div>
                      </div>
                    )}
                    {role.keywords.length > 0 && (
                      <div className="role-section">
                        <strong>Keywords:</strong>
                        <div className="tags">
                          {role.keywords.map((keyword, i) => (
                            <span key={i} className="tag keyword">{keyword}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        <section className="resume-preview-section">
          <h2>👁️ AI Preview</h2>
          <p className="section-description">
            See how your resume will be tailored for different roles
          </p>
          <div className="preview-placeholder">
            <p>Upload a resume and add target roles to see AI-powered previews</p>
          </div>
        </section>
      </div>
    </div>
  );
};
