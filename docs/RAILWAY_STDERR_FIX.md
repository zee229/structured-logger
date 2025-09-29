# Railway stderr Fix - v1.3.3

## Problem Description

Users were experiencing an issue where **all logs were being marked as "Error" in Railway**, regardless of their actual log level (INFO, WARNING, ERROR, etc.).

### Symptoms:
- INFO level logs appeared as "Error" in Railway dashboard
- Railway's log viewer showed `level: error` in attributes for all logs
- Logs were correctly formatted with proper level (e.g., `"level": "INFO"` in JSON)
- The issue affected both JSON and development format logs

### Example:
```
Raw log: 2025-09-29 19:38:27,241 [INFO] app.db.mongo: Creating new MongoDB client connection
Railway attributes: level: error  ❌ INCORRECT
```

## Root Cause Analysis

The issue was caused by Python's `logging.StreamHandler()` default behavior:

1. **By default, `StreamHandler()` writes to `sys.stderr`** (not `sys.stdout`)
2. **Railway treats anything written to stderr as an error**, regardless of the actual log level
3. This means even INFO and DEBUG logs were being classified as errors by Railway

### Why stderr?
Python's logging module uses stderr by default because:
- It's the conventional stream for diagnostic/logging output
- It allows separating program output (stdout) from diagnostic messages (stderr)
- However, this causes issues with platforms like Railway that use stderr to classify log severity

## Solution

The fix explicitly configures all `StreamHandler` instances to write to **stdout** instead of stderr:

```python
# Before (implicit stderr):
handler = logging.StreamHandler()

# After (explicit stdout):
handler = logging.StreamHandler(sys.stdout)
```

### Changes Made:

1. **Added `sys` import** to logger.py
2. **Updated all StreamHandler instantiations** to use `sys.stdout`:
   - In `_override_uvicorn_loggers()` function
   - In `get_logger()` function
   - In `setup_root_logger()` function
   - In `_setup_advanced_handler()` function

## Code Changes

### File: `src/structured_logger/logger.py`

**1. Added import:**
```python
import sys
```

**2. Updated StreamHandler instantiations (5 locations):**
```python
# Use stdout to prevent Railway from treating all logs as errors
handler = logging.StreamHandler(sys.stdout)
```

## Behavior Changes

### Before Fix:
```bash
# All logs went to stderr
$ python app.py 2>stderr.log 1>stdout.log
$ cat stderr.log
{"level": "INFO", "message": "..."}   # INFO logs in stderr ❌
{"level": "ERROR", "message": "..."}  # ERROR logs in stderr ❌

# Railway marked everything as Error
```

### After Fix:
```bash
# All logs go to stdout
$ python app.py 2>stderr.log 1>stdout.log
$ cat stdout.log
{"level": "INFO", "message": "..."}   # INFO logs in stdout ✅
{"level": "ERROR", "message": "..."}  # ERROR logs in stdout ✅

$ cat stderr.log
# Empty - no logs in stderr ✅

# Railway correctly identifies log levels
```

## Impact on Railway

After this fix, Railway will:
- ✅ Correctly identify INFO logs as informational
- ✅ Correctly identify WARNING logs as warnings
- ✅ Correctly identify ERROR logs as errors
- ✅ Parse log levels from the JSON `level` field instead of using stderr as a signal

## Backward Compatibility

- ✅ **Fully backward compatible** - existing code continues to work
- ✅ **No breaking changes** - all existing functionality preserved
- ✅ **No API changes** - no changes to public interfaces
- ℹ️ **Output stream change** - logs now go to stdout instead of stderr (this is the intended fix)

### Potential Considerations:

1. **If you were redirecting stderr to capture logs**, you'll need to redirect stdout instead:
   ```bash
   # Before:
   python app.py 2>logs.txt
   
   # After:
   python app.py >logs.txt
   # or
   python app.py 1>logs.txt
   ```

2. **If you were separating application output from logs**, you may need to adjust:
   ```bash
   # Separate app output (stdout) from logs (stderr) - NO LONGER WORKS
   python app.py >output.txt 2>logs.txt
   
   # Now both go to stdout, so you'll need application-level separation
   ```

3. **Most users won't notice any difference** - stdout vs stderr is transparent in most environments

## Testing

Verified the fix works correctly:

```python
import sys
import os
from structured_logger import get_logger, LoggerConfig

os.environ['RAILWAY_ENVIRONMENT'] = 'production'
config = LoggerConfig()
logger = get_logger('app.test', config=config, force_json=True)

logger.info('INFO message')
logger.warning('WARNING message')
logger.error('ERROR message')
```

**Output verification:**
```bash
# All logs go to stdout
$ python test.py 1>stdout.log 2>stderr.log

$ cat stdout.log
{"level": "INFO", "message": "INFO message", ...}
{"level": "WARNING", "message": "WARNING message", ...}
{"level": "ERROR", "message": "ERROR message", ...}

$ cat stderr.log
# Empty ✅
```

## Version

This fix is included in **structured-logger v1.3.3**.

## Migration Guide

**No migration needed!** Your existing code will work as-is. The only change is that logs now go to stdout instead of stderr, which is the intended behavior for Railway compatibility.

```python
# This code works exactly the same before and after the fix
from structured_logger import get_logger

logger = get_logger('my_app')
logger.info('Application started')
logger.error('Something went wrong')
```

The difference is that Railway will now correctly identify the log levels instead of marking everything as an error.

## Related Issues

This fix complements the v1.3.2 fix for the `error` field handling. Together, these fixes ensure:
1. ✅ The `error` field in extra data doesn't cause TypeErrors (v1.3.2)
2. ✅ Railway correctly identifies log levels (v1.3.3)

## Additional Notes

### Why stdout instead of stderr?

While stderr is the traditional stream for logging, modern cloud platforms like Railway, Heroku, and others use stderr as a signal for error severity. By using stdout:

1. **Better platform compatibility** - Works correctly with Railway, Heroku, etc.
2. **Explicit log levels** - Platforms parse the JSON `level` field instead of inferring from stream
3. **Simpler log aggregation** - All logs in one stream, easier to process
4. **Industry trend** - Many modern logging libraries (e.g., structlog, python-json-logger) default to stdout

### Configuration Option

Starting in v1.3.3, you can choose between two behaviors:

### Option 1: All logs to stdout (Default - Railway-compatible)

```python
from structured_logger import get_logger, LoggerConfig

# Default behavior - all logs go to stdout
config = LoggerConfig(use_stdout_for_all=True)  # or just LoggerConfig()
logger = get_logger(__name__, config=config)

logger.info("INFO to stdout")
logger.error("ERROR to stdout")
```

**Use this for:**
- Railway deployments
- Heroku deployments
- Any platform that uses stderr to classify log severity
- When you want Railway to parse JSON log levels correctly

### Option 2: Errors to stderr (Unix convention)

```python
from structured_logger import get_logger, LoggerConfig

# Unix convention - ERROR/CRITICAL to stderr, others to stdout
config = LoggerConfig(use_stdout_for_all=False)
logger = get_logger(__name__, config=config)

logger.info("INFO to stdout")
logger.error("ERROR to stderr")  # This will be marked as error in Railway
```

**Use this for:**
- Traditional Unix environments
- When you want to separate errors from normal logs
- Local development with shell redirection
- **NOT recommended for Railway** (will mark all errors as errors in UI)

## Alternative Solutions Considered

1. **Keep using stderr for all logs** - Not viable, Railway would continue marking all logs as errors
2. **Use different streams per log level (now available as option)** - Added as `use_stdout_for_all=False`
3. **Configure Railway to ignore stderr** - Not possible, Railway's behavior is fixed
4. **Use stdout for all logs (default solution)** - Simple, effective, industry standard

## References

- [Python logging.StreamHandler documentation](https://docs.python.org/3/library/logging.handlers.html#logging.StreamHandler)
- [Railway logging documentation](https://docs.railway.app/reference/logs)
- [Twelve-Factor App: Logs](https://12factor.net/logs) - Recommends treating logs as event streams to stdout
