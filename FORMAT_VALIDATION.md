# Railway vs Sentry Format Validation

This document confirms that Railway and Sentry receive **different, appropriate formats** that are optimized for each platform's specific use case.

## ✅ Format Confirmation

### Railway Format (JSON Logs)

**What Railway receives:**
```json
{
  "time": "2025-09-26 12:29:38,069",
  "level": "ERROR", 
  "message": "Payment processing failed",
  "module": "my_app",
  "user_id": "user_12345",
  "company_id": "company_67890",
  "request_id": "req_abcdef",
  "extra": {
    "transaction_id": "txn_xyz123",
    "amount": 99.99,
    "currency": "USD",
    "error_code": "CARD_DECLINED",
    "retry_count": 2
  }
}
```

**Railway Format Characteristics:**
- ✅ **Format**: Structured JSON (one JSON object per log line)
- ✅ **Purpose**: Log aggregation, searching, analytics
- ✅ **Structure**: Flat JSON with nested `extra` field for additional context
- ✅ **Time**: Human-readable timestamp
- ✅ **Context**: All log context preserved in JSON structure
- ✅ **Searchable**: Easy to query with log aggregation tools

### Sentry Format (Native Events)

**What Sentry receives:**
```python
# Sentry receives native SDK calls, NOT JSON
sentry_sdk.capture_message(
    message="Payment processing failed",
    level="error"
)

# With structured context:
scope.set_tag("user_id", "user_12345")
scope.set_tag("company_id", "company_67890") 
scope.set_tag("request_id", "req_abcdef")

scope.set_extra("transaction_id", "txn_xyz123")
scope.set_extra("amount", "99.99")
scope.set_extra("currency", "USD")
scope.set_extra("error_code", "CARD_DECLINED")
scope.set_extra("retry_count", "2")
```

**Sentry Format Characteristics:**
- ✅ **Format**: Native Sentry events (not JSON strings)
- ✅ **Purpose**: Error monitoring, alerting, debugging
- ✅ **Structure**: Message + Tags (for filtering) + Extras (for context)
- ✅ **Tags**: Optimized for Sentry's filtering and grouping
- ✅ **Extras**: Rich debugging context
- ✅ **Integration**: Works with Sentry's advanced error analysis features

## 🔄 Exception Handling Differences

### Railway Exception Format
```json
{
  "time": "2025-09-26 12:29:38,069",
  "level": "ERROR",
  "message": "Database connection failed", 
  "module": "my_app",
  "exception": "Traceback (most recent call last):\n  File \"/app/main.py\", line 42, in connect\n    conn = database.connect()\nConnectionError: Unable to connect to database",
  "user_id": "user123",
  "extra": {
    "database": "primary",
    "retry_count": 3
  }
}
```
- Stack trace as **string** in JSON
- Good for **log searching** and text analysis
- Preserves full context in structured format

### Sentry Exception Format
```python
# Sentry receives the actual exception object
sentry_sdk.capture_exception(exception_object)
```
- Sends **actual Python exception object**
- Sentry extracts stack trace, local variables, source code context
- Enables **advanced error analysis**, grouping, fingerprinting
- Provides release tracking and performance monitoring

## 🚀 Implementation Details

### How It Works

1. **Single Log Call**: 
   ```python
   logger.error("Payment failed", extra={"user_id": "user123"})
   ```

2. **Dual Output**:
   - **Railway Handler**: Formats as JSON and sends to console/file
   - **Sentry Handler**: Extracts context and sends native Sentry event

3. **No Interference**: Each handler processes the log record independently

### Configuration Example

```python
from structured_logger import get_logger, LoggerConfig, SentryConfig

# Configure both formats
sentry_config = SentryConfig(
    dsn=os.getenv("SENTRY_DSN"),
    min_level=logging.ERROR,  # Only errors to Sentry
    tag_fields=["user_id", "company_id", "request_id"],
    extra_fields=["module", "funcName", "lineno"]
)

logger_config = LoggerConfig(
    enable_sentry=True,
    sentry_config=sentry_config,
    custom_fields=["user_id", "company_id", "request_id"]
)

logger = get_logger("my_app", config=logger_config)
```

## ✅ Validation Results

| Aspect | Railway | Sentry | ✓ Different |
|--------|---------|--------|-------------|
| **Format** | JSON strings | Native SDK events | ✅ |
| **Purpose** | Log aggregation | Error monitoring | ✅ |
| **Structure** | Flat JSON + extras | Message + tags + extras | ✅ |
| **Exceptions** | String stack trace | Exception object | ✅ |
| **Optimization** | Searchable logs | Error analysis | ✅ |
| **Time Format** | Human readable | Sentry native | ✅ |
| **Context** | JSON nested | Tags/extras | ✅ |

## 🎯 Benefits of Different Formats

### Railway Benefits
- **Log Aggregation**: JSON format perfect for tools like Grafana, ELK stack
- **Searching**: Easy to query structured JSON logs
- **Analytics**: Can analyze log patterns and trends
- **Debugging**: Full context preserved in searchable format

### Sentry Benefits  
- **Error Monitoring**: Native integration with Sentry's error tracking
- **Alerting**: Automatic error detection and notifications
- **Grouping**: Intelligent error grouping and fingerprinting
- **Context**: Rich debugging context with source code integration
- **Performance**: Performance monitoring and release tracking

## 🔒 No Format Conflicts

✅ **Confirmed**: The formats are completely different and optimized for each platform  
✅ **Confirmed**: No interference between Railway and Sentry outputs  
✅ **Confirmed**: Single logger call produces both formats automatically  
✅ **Confirmed**: Each format is appropriate for its intended use case  

The integration successfully provides the best of both worlds: structured JSON logs for Railway and native error events for Sentry.
