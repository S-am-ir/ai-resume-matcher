import React, { useState, useEffect } from 'react';
import '../App.css';

interface JobApplication {
  id: string;
  company: string;
  position: string;
  status: 'applied' | 'interview' | 'offer' | 'rejected' | 'pending';
  date: string;
  location: string;
  salary?: string;
  description?: string;
  resumeVersion?: string;
}

interface TailoringModalProps {
  application: JobApplication | null;
  onClose: () => void;
  onSave: (appId: string, tailoredResume: string) => void;
}

const TailoringModal: React.FC<TailoringModalProps> = ({ application, onClose, onSave }) => {
  const [tailoredContent, setTailoredContent] = useState('');
  const [keywords, setKeywords] = useState('');

  useEffect(() => {
    if (application) {
      setTailoredContent(`Tailored resume for ${application.position} at ${application.company}...`);
    }
  }, [application]);

  const handleSave = () => {
    if (application) {
      onSave(application.id, tailoredContent);
      onClose();
    }
  };

  if (!application) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Tailor Resume</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">
          <div className="form-group">
            <label>Position</label>
            <input type="text" value={application.position} disabled />
          </div>
          <div className="form-group">
            <label>Company</label>
            <input type="text" value={application.company} disabled />
          </div>
          <div className="form-group">
            <label>Keywords to Highlight</label>
            <textarea
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              placeholder="Enter keywords from job description..."
              rows={3}
            />
          </div>
          <div className="form-group">
            <label>Tailored Resume Content</label>
            <textarea
              value={tailoredContent}
              onChange={(e) => setTailoredContent(e.target.value)}
              placeholder="AI will generate tailored content..."
              rows={10}
            />
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSave}>Save Tailored Resume</button>
        </div>
      </div>
    </div>
  );
};

export const TrackApplications: React.FC<{ userEmail: string | null }> = ({ userEmail }) => {
  const [applications, setApplications] = useState<JobApplication[]>([]);
  const [filter, setFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedApplication, setSelectedApplication] = useState<JobApplication | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    // Load applications from localStorage or API
    const saved = localStorage.getItem('jobApplications');
    if (saved) {
      setApplications(JSON.parse(saved));
    } else {
      // Sample data
      const sampleData: JobApplication[] = [
        { id: '1', company: 'Tech Corp', position: 'Senior Developer', status: 'interview', date: '2024-01-15', location: 'Remote', salary: '$120k-150k' },
        { id: '2', company: 'StartupXYZ', position: 'Full Stack Engineer', status: 'applied', date: '2024-01-14', location: 'New York, NY' },
        { id: '3', company: 'Enterprise Inc', position: 'Backend Developer', status: 'pending', date: '2024-01-13', location: 'San Francisco, CA', salary: '$100k-130k' },
        { id: '4', company: 'Digital Solutions', position: 'React Developer', status: 'rejected', date: '2024-01-10', location: 'Remote' },
        { id: '5', company: 'Cloud Systems', position: 'DevOps Engineer', status: 'offer', date: '2024-01-08', location: 'Austin, TX', salary: '$130k-160k' },
      ];
      setApplications(sampleData);
    }
  }, []);

  const filteredApplications = applications.filter(app => {
    const matchesFilter = filter === 'all' || app.status === filter;
    const matchesSearch = app.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          app.position.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const handleTailorResume = (application: JobApplication) => {
    setSelectedApplication(application);
    setIsModalOpen(true);
  };

  const handleSaveTailoredResume = (appId: string, content: string) => {
    console.log('Saving tailored resume for', appId, content);
    // Save to backend or localStorage
  };

  const getStatusClass = (status: string) => {
    return `status-badge status-${status}`;
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Track Applications</h1>
        <p>Monitor and manage your job applications</p>
      </div>

      {!userEmail && (
        <div className="notification warning">
          ⚠ Please connect your email to sync applications
        </div>
      )}

      <div className="filters-section">
        <div className="search-box">
          <input
            type="text"
            placeholder="Search by company or position..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="filter-buttons">
          <button
            className={filter === 'all' ? 'active' : ''}
            onClick={() => setFilter('all')}
          >
            All ({applications.length})
          </button>
          <button
            className={filter === 'applied' ? 'active' : ''}
            onClick={() => setFilter('applied')}
          >
            Applied
          </button>
          <button
            className={filter === 'interview' ? 'active' : ''}
            onClick={() => setFilter('interview')}
          >
            Interview
          </button>
          <button
            className={filter === 'offer' ? 'active' : ''}
            onClick={() => setFilter('offer')}
          >
            Offer
          </button>
          <button
            className={filter === 'rejected' ? 'active' : ''}
            onClick={() => setFilter('rejected')}
          >
            Rejected
          </button>
        </div>
      </div>

      <div className="applications-grid">
        {filteredApplications.length === 0 ? (
          <div className="empty-state">
            <p>No applications found</p>
          </div>
        ) : (
          filteredApplications.map((app) => (
            <div key={app.id} className="application-card">
              <div className="card-header">
                <div className="company-info">
                  <h3>{app.company}</h3>
                  <p className="position">{app.position}</p>
                </div>
                <span className={getStatusClass(app.status)}>{app.status}</span>
              </div>
              <div className="card-body">
                <div className="detail-row">
                  <span>📍 {app.location}</span>
                  <span>📅 {app.date}</span>
                </div>
                {app.salary && (
                  <div className="detail-row">
                    <span>💰 {app.salary}</span>
                  </div>
                )}
              </div>
              <div className="card-footer">
                <button
                  className="btn btn-sm btn-primary"
                  onClick={() => handleTailorResume(app)}
                >
                  Tailor Resume
                </button>
                <button className="btn btn-sm btn-secondary">View Details</button>
              </div>
            </div>
          ))
        )}
      </div>

      {isModalOpen && (
        <TailoringModal
          application={selectedApplication}
          onClose={() => setIsModalOpen(false)}
          onSave={handleSaveTailoredResume}
        />
      )}
    </div>
  );
};
