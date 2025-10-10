# WEKO3 UI Tests

This directory contains Playwright-based UI tests for the WEKO3 application.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:

```bash
playwright install
```

## Running Tests

### Locally

```bash
# Run all tests
pytest

# Run specific test file
pytest test_anonymous_page.py

# Run with specific browser
pytest --browser chromium

# Run tests in headed mode (visible browser)
pytest --headed
```

### Environment Variables

- `WEKO_BASE_URL`: Base URL of the WEKO application (default: https://weko3.example.org)
- `WEKO_TEST_EMAIL`: Email for user login (default: test@weko3.example.org)
- `WEKO_TEST_PASSWORD`: Password for user login (default: testpassword)

## CI/CD Integration

These tests are automatically run in GitHub Actions when:
- Pull requests are created
- Code is pushed to branches
- Manual workflow dispatch

The tests run against a containerized WEKO environment started via `install.sh`.
