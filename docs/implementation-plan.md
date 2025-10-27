# OCRBox Implementation Plan

## Architecture Overview

Python-based Docker service with:

- **Dropbox App Folder** integration (OAuth with allowlist validation)
- **Development mode** for local folder watching
- **Gemini API** for OCR processing
- **Telegram notifications** (primary), email notifications (prepared)
- **JSON file storage** for OAuth tokens with file permissions
- **SQLite** for processed files tracking (idempotency)
- **Environment variable** configuration throughout

## Project Structure

```
ocrbox/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── docs/
│   └── implementation-plan.md
├── src/
│   ├── __init__.py
│   ├── main.py              # Service entry point & orchestration
│   ├── config.py            # Environment variable parsing & validation
│   ├── dropbox_oauth.py     # OAuth flow, allowlist checking, token storage
│   ├── dropbox_watcher.py   # Monitor Dropbox App Folders for new files
│   ├── local_watcher.py     # Development mode: local folder watching
│   ├── file_processor.py    # Core processing: OCR → text output → archive
│   ├── gemini_client.py     # Gemini API integration with retry logic
│   ├── notifications.py     # Telegram (+ email interface for future)
│   └── storage.py           # Processed files tracking (SQLite)
└── data/                    # Docker volume mount point
    ├── tokens/              # OAuth tokens (JSON files, one per user)
    ├── processed.db         # Processed files tracking (SQLite)
    ├── output/              # Extracted text files
    ├── archive/             # Processed images
    └── watch/               # Dev mode: input folder
```

## Key Components

### 1. Configuration (`src/config.py`)

Environment variables for:

- `MODE`: `dropbox` or `local` (dev mode)
- `GEMINI_API_KEY`: Google Gemini API key
- `DROPBOX_APP_KEY`, `DROPBOX_APP_SECRET`: OAuth credentials
- `DROPBOX_REDIRECT_URI`: OAuth callback URL
- `ALLOWED_ACCOUNTS`: Comma-separated Dropbox account IDs/emails
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`: Notification settings
- `EMAIL_*`: SMTP settings (for future email notifications)
- `LOG_LEVEL`: Logging verbosity

### 2. Dropbox OAuth (`src/dropbox_oauth.py`)

- OAuth 2.0 authorization flow (PKCE for security)
- Web server endpoint for OAuth callback
- Account validation via `/users/get_current_account`
- Allowlist checking against `ALLOWED_ACCOUNTS`
- Token persistence to JSON files (one per user)
- Token refresh handling

### 3. File Processing Pipeline (`src/file_processor.py`)

**Workflow:**

1. Detect new image file (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`)
2. Download/read image bytes
3. Call Gemini OCR via `gemini_client.py`
4. Save extracted text as `.txt` in output directory
5. Move original image to archive directory
6. Send notification on success/failure
7. Mark as processed (idempotency check)

**Idempotency:** Track processed files in SQLite to prevent reprocessing

### 4. Gemini Client (`src/gemini_client.py`)

- Initialize Gemini API client with API key
- Send image for OCR using `gemini-1.5-flash` or `gemini-1.5-pro`
- Retry logic with exponential backoff for transient errors
- Error handling and logging

### 5. Notification System (`src/notifications.py`)

**Phase 1: Telegram**

- Send processing results via Telegram Bot API
- Format: filename, status, excerpt of extracted text, timestamp
- Error notifications with details

**Phase 2: Email (prepared interface)**

- Abstract notification interface
- Email implementation ready to activate via config

### 6. Dropbox Watcher (`src/dropbox_watcher.py`)

- Poll each authorized user's App Folder for new files
- Use Dropbox `/list_folder` and `/list_folder/continue` APIs
- Detect new files since last check (cursor-based)
- Download files for processing
- Upload processed `.txt` files back to App Folder (optional)

### 7. Local Watcher (`src/local_watcher.py`)

**Development Mode:**

- Watch `data/watch/` directory for new files
- Process immediately when detected
- Use `watchdog` library for filesystem events
- Output to `data/output/`, archive to `data/archive/`

### 8. Storage (`src/storage.py`)

**Token Storage (JSON files):**
- One JSON file per authorized user in `data/tokens/`
- File permissions: 600 (owner read/write only)
- Contains: account_id, account_email, access_token, refresh_token, timestamps

**Processed Files Database (SQLite):**
- `processed_files`: file_id, file_path, processed_at, status, account_id, file_hash, output_path
- Ensures idempotent processing (files never processed twice)

### 9. Main Service (`src/main.py`)

- Parse config and validate environment
- Initialize storage, notification clients
- Run OAuth server (if tokens missing) OR start file watcher
- Mode selection: Dropbox or local
- Graceful shutdown handling
- Logging setup (stdout for Docker)

### 10. Docker Setup

**Dockerfile:**

- Python 3.11+ base image
- Install dependencies from `requirements.txt`
- Non-root user for security
- Volume mounts for data persistence

**docker-compose.yml:**

- Service definition with environment variables
- Volume mappings: `./data:/app/data`
- Port mapping for OAuth callback (e.g., 8080)
- Restart policy: `unless-stopped`

### 11. Documentation (`README.md`)

- Overview and features
- Setup instructions (Dropbox App creation, OAuth flow)
- Environment variable reference
- Docker deployment guide
- Usage examples
- Troubleshooting

## Dependencies (`requirements.txt`)

- `google-generativeai` (Gemini SDK)
- `dropbox` (Dropbox SDK)
- `requests` (HTTP requests for Telegram)
- `watchdog` (local file watching)
- `python-dotenv` (env file loading)
- `Pillow` (image handling)

## Security Considerations

- OAuth tokens stored as JSON files with restrictive permissions (600)
- No hardcoded secrets
- App secrets never exposed to clients
- Allowlist enforced at token exchange time
- Docker runs as non-root user
- Environment variables for all sensitive data
- PKCE used for OAuth flow security

## OAuth Token Storage - Simplified Approach

**Why JSON files over SQLite for tokens:**
- Simpler to implement and debug (just cat the file)
- Easy to backup (copy files)
- Easy to revoke (delete file)
- Sufficient security with proper file permissions
- No database management overhead
- Still using SQLite for processed files tracking (appropriate use case)

**Token File Format:**
```json
{
  "account_id": "dbid:AAH4f99T0taONIb...",
  "account_email": "user@example.com",
  "access_token": "sl.xxxxx",
  "refresh_token": "yyyy",
  "authorized_at": "2025-10-27T14:20:00Z",
  "updated_at": "2025-10-27T14:20:00Z"
}
```

## Testing Strategy

1. **Local mode first**: Test OCR pipeline without Dropbox
2. **Dropbox OAuth**: Test authorization flow with test account
3. **Allowlist validation**: Verify unauthorized accounts are rejected
4. **Notifications**: Test Telegram message delivery
5. **Idempotency**: Process same file twice, verify no duplication
6. **Error handling**: Simulate API failures, verify retries and notifications

## Implementation Status

✅ Configuration module with environment variable parsing
✅ Storage layer (JSON tokens + SQLite processed files)
✅ Gemini OCR client with retry logic
✅ Notification system (Telegram + Email interface)
✅ File processor with idempotency
✅ Local folder watcher for development
✅ Dropbox OAuth with allowlist validation
✅ Dropbox watcher for multi-tenant monitoring
✅ Main orchestrator with graceful shutdown
✅ Docker setup (Dockerfile + docker-compose)
✅ Comprehensive documentation

## Usage Examples

### Local Mode (Development)

```bash
# Configure
export MODE=local
export GEMINI_API_KEY=your_key
export TELEGRAM_ENABLED=true
export TELEGRAM_BOT_TOKEN=your_token
export TELEGRAM_CHAT_ID=your_chat_id

# Run
docker-compose up

# Add files
cp screenshot.png data/watch/

# Check output
cat data/output/screenshot.txt
```

### Dropbox Mode (Production)

```bash
# Configure
export MODE=dropbox
export GEMINI_API_KEY=your_key
export DROPBOX_APP_KEY=your_app_key
export DROPBOX_APP_SECRET=your_app_secret
export ALLOWED_ACCOUNTS=user@example.com

# Run
docker-compose up

# Visit http://localhost:8080 to authorize

# Monitor
docker-compose logs -f
```

## Future Enhancements

- Web dashboard for monitoring and management
- REST API for programmatic access
- Support for additional OCR engines
- PDF document support
- Webhook notifications
- Custom output formatting/templates
- Batch processing optimizations

