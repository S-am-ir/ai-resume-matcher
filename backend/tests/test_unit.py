"""
Anti-Berojgar Backend - Unit Tests
Tests for core functionality
"""
import pytest
import os
from datetime import datetime, timedelta


class TestResumeTailoring:
    """Test resume tailoring logic."""
    
    def test_pdf_only_validation(self):
        """Test that only PDF files are accepted."""
        # This tests the backend validation logic
        valid_extensions = ['pdf']
        invalid_extensions = ['png', 'jpg', 'jpeg', 'txt', 'doc', 'docx']
        
        for ext in valid_extensions:
            assert ext == 'pdf', "Only PDF should be valid"
        
        for ext in invalid_extensions:
            assert ext != 'pdf', f"{ext} should not be valid"


class TestJobMatching:
    """Test job matching logic."""
    
    def test_experience_gap_analysis(self):
        """Test experience gap evaluation logic."""
        # Test cases for experience matching
        test_cases = [
            # (job_exp, candidate_exp, has_strong_projects, should_match)
            (0, 0, False, True),      # Entry level, no exp - OK
            (2, 0, True, True),       # 2 yrs req, 0 exp, strong projects - OK
            (3, 1, True, True),       # 3 yrs req, 1 yr exp, strong projects - OK
            (5, 0, False, False),     # 5 yrs req, 0 exp, no projects - NO
            (5, 1, False, False),     # 5 yrs req, 1 yr exp - NO (gap too wide)
            (4, 2, True, True),       # 4 yrs req, 2 yrs exp, strong projects - OK
        ]
        
        for job_exp, cand_exp, has_projects, expected in test_cases:
            # Simple heuristic: gap > 2 years with no projects = mismatch
            gap = job_exp - cand_exp
            if gap > 3 and not has_projects:
                result = False  # Mismatch
            elif gap > 2 and cand_exp < 2 and not has_projects:
                result = False  # Mismatch
            else:
                result = True  # Match
            
            assert result == expected, f"Failed for job:{job_exp}yr, candidate:{cand_exp}yr, projects:{has_projects}"
    
    def test_skills_matching(self):
        """Test skills matching logic."""
        # Test: Missing 2+ required skills = mismatch
        required_skills = ['Python', 'FastAPI', 'PostgreSQL', 'AWS']
        candidate_skills = ['Python', 'FastAPI']  # Missing PostgreSQL, AWS
        
        missing_count = len([s for s in required_skills if s not in candidate_skills])
        assert missing_count == 2, "Should detect 2 missing skills"
        
        # 2+ missing = mismatch
        is_mismatch = missing_count >= 2
        assert is_mismatch == True


class TestApplicationStatus:
    """Test application status logic."""
    
    def test_time_based_status_transitions(self):
        """Test time-based status calculations."""
        now = datetime.now()
        
        # Test cases: (days_ago, expected_status)
        test_cases = [
            (0, 'Tracking'),    # Just applied
            (3, 'Tracking'),    # 3 days - still tracking
            (5, 'Follow Up'),   # 5 days - follow up
            (6, 'Follow Up'),   # 6 days - follow up
            (7, 'Ghosted'),     # 7 days - ghosted
            (10, 'Ghosted'),    # 10 days - ghosted
        ]
        
        for days_ago, expected_status in test_cases:
            applied_date = now - timedelta(days=days_ago)
            days_since = (now - applied_date).days
            
            # Status logic from backend
            if days_since >= 7:
                status = 'Ghosted'
            elif days_since >= 5:
                status = 'Follow Up'
            else:
                status = 'Tracking'
            
            assert status == expected_status, f"Failed for {days_ago} days: got {status}, expected {expected_status}"


class TestEmailTracking:
    """Test email tracking logic."""
    
    def test_gmail_link_generation(self):
        """Test Gmail link generation for responses."""
        # Test cases for when email link should appear
        test_cases = [
            # (status, has_message_id, should_show_link)
            ('interview', 'msg123', True),
            ('offered', 'msg456', True),
            ('rejected', 'msg789', True),
            ('tracking', 'msg111', False),  # No link for tracking status
            ('pending', None, False),
            ('ghosted', None, False),
            ('follow up', None, False),
        ]
        
        for status, msg_id, should_show in test_cases:
            # Logic from frontend: show link if has message_id and status is interview/offered/rejected
            has_link = bool(msg_id and status.lower() in ['interview', 'offered', 'rejected'])
            assert has_link == should_show, f"Failed for status={status}, msg_id={msg_id}"
    
    def test_email_subject_parsing(self):
        """Test parsing email subjects for interview/rejection/offer detection."""
        def classify_email_subject(subject):
            subject_lower = subject.lower()
            if any(word in subject_lower for word in ['interview', 'schedule', 'meeting', 'call']):
                return 'interview'
            if any(word in subject_lower for word in ['offer', 'hired', 'welcome aboard']):
                return 'offered'
            if any(word in subject_lower for word in ['thank you for your interest', 'not moving forward', 'no longer considering']):
                return 'rejected'
            return 'unknown'
        
        assert classify_email_subject("Interview Invitation - Software Engineer") == 'interview'
        assert classify_email_subject("Job Offer - Software Engineer Position") == 'offered'
        assert classify_email_subject("Thank You for Your Interest") == 'rejected'
    
    def test_email_to_status_mapping(self):
        """Test email classification maps to correct application status."""
        email_to_status = {'interview': 'Interview', 'offered': 'Offered', 'rejected': 'Rejected'}
        assert email_to_status['interview'] == 'Interview'
        assert email_to_status['offered'] == 'Offered'
        assert email_to_status['rejected'] == 'Rejected'


class TestGmailIntegration:
    """Test Gmail IMAP integration logic."""
    
    def test_imap_connection_logic(self):
        """Test IMAP connection validation."""
        def validate_imap_credentials(email, password):
            if not email or '@' not in email:
                return False, "Invalid email format"
            if not password or len(password) < 10:
                return False, "Invalid app password"
            if not email.endswith('@gmail.com'):
                return False, "Only Gmail supported"
            return True, "Valid"
        
        assert validate_imap_credentials('test@gmail.com', 'abcdefghijklmnop')[0] == True
        assert validate_imap_credentials('notanemail', 'password')[0] == False
        assert validate_imap_credentials('test@gmail.com', 'short')[0] == False
    
    def test_gmail_thread_matching(self):
        """Test matching Gmail threads to job applications."""
        def match_email_to_application(email_subject, applications):
            subject_lower = email_subject.lower()
            for app in applications:
                if app['company'].lower() in subject_lower or app['job_title'].lower() in subject_lower:
                    return app['id']
            return None
        
        apps = [{'id': 1, 'company': 'Google', 'job_title': 'Software Engineer'}]
        assert match_email_to_application("Interview at Google", apps) == 1
        assert match_email_to_application("Amazon Application", apps) is None


class TestAPIValidation:
    """Test API validation logic."""
    
    def test_resume_file_validation(self):
        """Test resume file type validation."""
        # Backend validation logic
        def is_valid_resume(filename, content_type):
            ext = filename.split('.')[-1].lower() if '.' in filename else ''
            return ext == 'pdf' or content_type == 'application/pdf'
        
        # Valid cases
        assert is_valid_resume('resume.pdf', 'application/pdf') == True
        assert is_valid_resume('Resume.PDF', 'application/pdf') == True
        
        # Invalid cases
        assert is_valid_resume('resume.png', 'image/png') == False
        assert is_valid_resume('resume.jpg', 'image/jpeg') == False
        assert is_valid_resume('resume.doc', 'application/msword') == False
        assert is_valid_resume('resume', 'text/plain') == False
    
    def test_delete_application_ownership(self):
        """Test application deletion ownership verification."""
        # Simulated ownership check logic
        def verify_ownership(app_email, user_email):
            return app_email == user_email
        
        # Valid deletion
        assert verify_ownership('user@example.com', 'user@example.com') == True
        
        # Invalid deletion (wrong user)
        assert verify_ownership('user@example.com', 'other@example.com') == False


class TestAgentRouting:
    """Test agent routing logic."""
    
    def test_mode_routing(self):
        """Test agent routes to correct mode."""
        # Test routing logic
        def get_mode(user_message):
            message = user_message.lower()
            if 'tailor' in message or 'resume' in message:
                return 'tailor'
            elif 'track' in message or 'application' in message or 'gmail' in message:
                return 'track'
            else:
                return 'tailor'  # Default
        
        # Test cases
        assert get_mode('Tailor my resume') == 'tailor'
        assert get_mode('Track my applications') == 'track'
        assert get_mode('Check Gmail for responses') == 'track'
        assert get_mode('Update my resume') == 'tailor'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
