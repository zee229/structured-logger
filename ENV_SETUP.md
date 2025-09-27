# Environment Configuration Setup

This document explains how to set up environment variables for development and testing.

## Quick Setup

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your actual values:**
   ```bash
   # Edit the file with your preferred editor
   nano .env
   # or
   code .env
   ```

## Environment Files

### `.env.example`
Template file with all available environment variables. **This is committed to git.**

### `.env.test` 
Test-specific environment variables. **This is committed to git** and used automatically by pytest.

### `.env`
Your local development environment variables. **This is gitignored** and should contain your actual secrets.

## Available Environment Variables

### Sentry Configuration
```bash
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=development  # or production, staging, etc.
SENTRY_RELEASE=1.1.0
```

### Logging Configuration
```bash
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR
ENABLE_JSON_LOGGING=true        # true/false
```

### Test Configuration
```bash
TEST_USER_ID=test_user_123
TEST_COMPANY_ID=test_company_456
TEST_REQUEST_ID=test_request_789
```

## Testing with Environment Variables

### Run all tests:
```bash
make test
```

### Run environment-specific tests:
```bash
make test-env
```

### Run tests with real Sentry (requires SENTRY_DSN):
```bash
make test-sentry
```

### Run with custom environment:
```bash
SENTRY_DSN=your-dsn make test-sentry
```

## Pytest Configuration

The pytest configuration automatically:
1. Loads `.env.test` first (highest priority)
2. Loads `.env` as fallback (if it exists)
3. Sets `TESTING=true` and `ENVIRONMENT=test` for all tests

## Usage in Code

```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Use in your code
sentry_dsn = os.getenv("SENTRY_DSN")
log_level = os.getenv("LOG_LEVEL", "INFO")
```

## Production Deployment

### Railway
Set environment variables in Railway dashboard:
- `SENTRY_DSN`
- `LOG_LEVEL=INFO`
- `ENABLE_JSON_LOGGING=true`
- `ENVIRONMENT=production`

### Other Platforms
Set the same environment variables in your deployment platform's configuration.
