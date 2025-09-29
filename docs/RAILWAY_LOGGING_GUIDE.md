# Railway Logging Guide

## The Problem You Encountered

Your INFO logs were showing up as "Error" in Railway's dashboard, even though they had the correct `"level": "INFO"` in the JSON output.

## Root Cause

**Railway classifies logs based on which stream they're written to:**
- **stderr → Error** (marked with red error badge)
- **stdout → Info** (no special marking)

Python's `logging.StreamHandler()` by default writes **ALL logs to stderr** (including INFO, WARNING, ERROR). This caused Railway to mark everything as an error.

## The Solution

Starting in **v1.3.3**, the structured-logger uses **stdout by default** for all logs. This makes Railway parse the JSON `level` field correctly instead of assuming everything is an error.

## Two Configuration Options

### Option 1: All Logs to stdout (Default - Recommended for Railway)

```python
from structured_logger import get_logger, LoggerConfig

# Default behavior - Railway-compatible
config = LoggerConfig(use_stdout_for_all=True)  # or just LoggerConfig()
logger = get_logger(__name__, config=config)

logger.info("Creating MongoDB connection")  # ✅ Shows as INFO in Railway
logger.error("Connection failed")            # ✅ Shows as ERROR in Railway
```

**Stream behavior:**
```bash
$ python app.py 1>stdout.log 2>stderr.log
$ cat stdout.log
{"level": "INFO", "message": "Creating MongoDB connection", ...}
{"level": "ERROR", "message": "Connection failed", ...}

$ cat stderr.log
# Empty
```

**Railway behavior:**
- ✅ INFO logs show as informational
- ✅ ERROR logs show as errors (based on JSON level field)
- ✅ Correct log level classification

### Option 2: Errors to stderr (Unix Convention)

```python
from structured_logger import get_logger, LoggerConfig

# Unix convention - separate streams
config = LoggerConfig(use_stdout_for_all=False)
logger = get_logger(__name__, config=config)

logger.info("Creating MongoDB connection")  # Goes to stdout
logger.error("Connection failed")            # Goes to stderr
```

**Stream behavior:**
```bash
$ python app.py 1>stdout.log 2>stderr.log
$ cat stdout.log
{"level": "INFO", "message": "Creating MongoDB connection", ...}
{"level": "WARNING", "message": "Slow query", ...}

$ cat stderr.log
{"level": "ERROR", "message": "Connection failed", ...}
{"level": "CRITICAL", "message": "System failure", ...}
```

**Railway behavior:**
- ✅ INFO/WARNING logs show as informational
- ⚠️ ERROR/CRITICAL logs show as errors (Railway sees stderr)
- ⚠️ This is actually correct behavior, but differs from Option 1

## Which Option Should You Use?

### Use Option 1 (Default) if:
- ✅ You're deploying to Railway
- ✅ You're deploying to Heroku
- ✅ You want the platform to parse JSON log levels
- ✅ You want all logs in one stream for easier processing
- ✅ You're following 12-factor app principles

### Use Option 2 if:
- ✅ You're in a traditional Unix environment
- ✅ You want to redirect errors separately (`2>errors.log`)
- ✅ You're running locally and want to see errors in red
- ⚠️ **NOT recommended for Railway** (but it will work correctly)

## Migration from v1.3.2 or Earlier

**No code changes needed!** The default behavior now uses stdout for all logs:

```python
# This code works in both old and new versions
from structured_logger import get_logger

logger = get_logger(__name__)
logger.info("Application started")
logger.error("Something went wrong")
```

**What changed:**
- **v1.3.2 and earlier:** All logs went to stderr → Railway marked everything as error ❌
- **v1.3.3 and later:** All logs go to stdout → Railway parses JSON levels correctly ✅

## Understanding Railway's Log Classification

Railway uses a simple rule:
1. **Stream-based classification:**
   - Anything on stderr = Error
   - Anything on stdout = Info

2. **JSON parsing (when on stdout):**
   - Railway parses the `level` field in JSON
   - Shows appropriate severity in the UI

This is why Option 1 (stdout for all) works best with Railway.

## Examples

### Example 1: Basic Railway Deployment

```python
from structured_logger import get_logger

# Use defaults - Railway-compatible
logger = get_logger(__name__)

logger.info("Server starting on port 8000")
logger.info("Database connected")
logger.error("Failed to load config file")
```

**Railway Output:**
- ✅ "Server starting" → INFO
- ✅ "Database connected" → INFO
- ✅ "Failed to load config file" → ERROR

### Example 2: FastAPI with Uvicorn

```python
from structured_logger import get_logger, setup_uvicorn_logging, LoggerConfig

# Setup uvicorn logging
config = LoggerConfig(
    override_uvicorn_loggers=True,
    use_stdout_for_all=True  # Railway-compatible
)
setup_uvicorn_logging(config=config)

# Your app logger
logger = get_logger(__name__, config=config)

logger.info("FastAPI application started")
```

### Example 3: Unix-style Separation (Local Development)

```python
from structured_logger import get_logger, LoggerConfig

# Separate errors to stderr
config = LoggerConfig(use_stdout_for_all=False)
logger = get_logger(__name__, config=config)

logger.info("Processing request")  # stdout
logger.error("Request failed")      # stderr
```

Run with:
```bash
# Separate normal logs from errors
python app.py >app.log 2>errors.log

# Or just see errors
python app.py >/dev/null 2>&1 | grep ERROR
```

## Technical Details

### LevelBasedStreamHandler

When `use_stdout_for_all=False`, the logger uses a custom `LevelBasedStreamHandler` that:
- Routes INFO, DEBUG, WARNING to stdout
- Routes ERROR, CRITICAL to stderr
- Maintains proper log ordering
- Thread-safe stream switching

### Default Behavior

The default `use_stdout_for_all=True` uses Python's standard `StreamHandler(sys.stdout)` for all logs.

## Troubleshooting

### Problem: Logs still showing as errors in Railway

**Check:**
1. Are you using v1.3.3 or later?
   ```python
   import structured_logger
   print(structured_logger.__version__)  # Should be >= 1.3.3
   ```

2. Are you using the default configuration?
   ```python
   config = LoggerConfig()
   print(config.use_stdout_for_all)  # Should be True
   ```

3. Are you forcing a custom handler somewhere?

### Problem: Want to see errors in red locally

Use development format with `use_stdout_for_all=False`:

```python
config = LoggerConfig(use_stdout_for_all=False)
logger = get_logger(__name__, config=config, force_dev=True)
```

Then errors will go to stderr and show in red in most terminals.

## Best Practices

1. **For Railway/Heroku:** Use default settings (stdout for all)
2. **For local development:** Use `force_dev=True` for readable output
3. **For production:** Use JSON format with `force_json=True`
4. **For log aggregation:** Use stdout for all logs (easier to process)
5. **For traditional Unix:** Use `use_stdout_for_all=False` if needed

## Summary

The key insight is that **Railway uses the output stream (stdout vs stderr) to classify log severity**, not the content of the logs. By default, structured-logger now uses stdout for all logs, allowing Railway to parse the JSON `level` field correctly.

If you need Unix-style separation (errors to stderr), you can enable it with `use_stdout_for_all=False`, but this is not recommended for Railway deployments.
