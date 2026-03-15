# Running Tests

## Quick Start

```bash
# From the backend directory
python tests/run_tests.py

# Or directly with pytest
pytest tests/test_unit.py -v
```

## Test Categories

### Unit Tests (`tests/test_unit.py`)

| Test Class | Tests | What It Covers |
|------------|-------|----------------|
| `TestResumeTailoring` | 1 | PDF-only validation |
| `TestJobMatching` | 2 | Experience gap analysis, Skills matching logic |
| `TestApplicationStatus` | 1 | Time-based status (Tracking → Follow Up → Ghosted) |
| `TestEmailTracking` | 3 | Gmail link generation, Email subject parsing, Status mapping |
| `TestGmailIntegration` | 2 | IMAP connection validation, Thread-to-application matching |
| `TestAPIValidation` | 2 | Resume file validation, Delete ownership verification |
| `TestAgentRouting` | 1 | Mode routing (tailor vs track) |

**Total: 12 tests covering the complete tracking workflow**

---

## Complete Email Tracking Flow (Tested)

```
1. User adds job application → Status: "Pending"
2. User connects Gmail (IMAP) → Status: "Tracking"
3. Background agent runs hourly:
   ├─ Fetch Gmail threads via IMAP
   ├─ Parse email subjects (Interview/Offered/Rejected)
   ├─ Match email to application (by company/title)
   ├─ Update status + store gmail_message_id
   └─ Frontend shows 📧 link when status = Interview/Offered/Rejected
4. Time-based updates:
   ├─ 5+ days no response → "Follow Up"
   └─ 7+ days no response → "Ghosted"
```

### What's Tested

✅ **Email Subject Parsing**
- "Interview Invitation" → Interview status
- "Job Offer" → Offered status  
- "Thank You for Your Interest" → Rejected status

✅ **Gmail Link Generation**
- Link appears when: `gmail_message_id` exists AND status is Interview/Offered/Rejected
- Link format: `https://mail.google.com/mail/u/0/#all/{message_id}`

✅ **Status Transitions**
- Pending → Tracking (when Gmail connected)
- Tracking → Interview/Offered/Rejected (when email found)
- Tracking → Follow Up (5 days) → Ghosted (7 days)

✅ **Thread Matching**
- Matches email subject to company name or job title
- Stores message ID for Gmail deep link

---

## What Requires Manual Testing

The following scenarios need real Gmail credentials:

- **Live IMAP connection** - Requires valid Gmail + App Password
- **Actual email parsing** - Need real interview/rejection emails
- **End-to-end tracking** - Full agent workflow with live Gmail

To test manually:
1. Go to Settings
2. Connect Gmail with App Password
3. Add job applications
4. Wait for background agent (runs hourly)
5. Check if 📧 link appears when email received

## CI/CD Integration

Tests run automatically on:
- Pull requests to `main`
- Push to `main` branch

See `.github/workflows/tests.yml` for configuration.

## Manual Testing

### Test Resume Tailoring

```bash
python -c "
from agent.tailor import tailor_resume_html
import asyncio

result = asyncio.run(tailor_resume_html(
    'uploads/test_resume.pdf',
    'Job description here...'
))
print(result)
"
```

### Test Email Tracking

```bash
python -c "
from agent.email_tracker import fetch_recent_application_threads

threads = fetch_recent_application_threads(
    'your-email@gmail.com',
    'your-app-password'
)
print(f'Found {len(threads)} threads')
"
```

## Skipping Tests

Some tests require a test database:

```bash
# Run only tests that don't need database
pytest tests/test_unit.py -v -k "not Database"

# Run only database tests
pytest tests/test_unit.py -v -k "Database"
```

## Troubleshooting

### "Module not found"
```bash
pip install -r requirements.txt
```

### "Database connection failed"
Tests marked with `@pytest.mark.skip` require a test database. Set up:

```bash
export TEST_DATABASE_URL="postgresql://user:pass@localhost:5432/antiberojgar_test"
```

### "Playwright not installed"
```bash
playwright install chromium
```
