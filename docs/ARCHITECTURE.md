# OCRBox Architecture

This document provides a detailed overview of OCRBox's architecture and design decisions.

## System Overview

OCRBox is a Python-based microservice designed for automatic OCR processing of images. It supports two operational modes:

1. **Local Mode**: For development and testing with filesystem watching
2. **Dropbox Mode**: For production with multi-tenant cloud integration

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      OCRBox Service                         │
│                                                              │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │   Config     │────────→│    Main      │                 │
│  │   Module     │         │ Orchestrator │                 │
│  └──────────────┘         └──────┬───────┘                 │
│                                   │                          │
│                    ┌──────────────┼──────────────┐          │
│                    ↓              ↓              ↓          │
│         ┌──────────────┐  ┌──────────────┐  ┌─────────┐   │
│         │    Local     │  │   Dropbox    │  │ Storage │   │
│         │   Watcher    │  │   Watcher    │  │ Manager │   │
│         └──────┬───────┘  └──────┬───────┘  └────┬────┘   │
│                │                  │               │         │
│                └──────────┬───────┘               │         │
│                           ↓                       │         │
│                  ┌────────────────┐               │         │
│                  │      File      │←──────────────┘         │
│                  │   Processor    │                         │
│                  └────────┬───────┘                         │
│                           │                                  │
│                ┌──────────┼──────────┐                      │
│                ↓          ↓          ↓                      │
│         ┌──────────┐ ┌────────┐ ┌──────────┐              │
│         │  Gemini  │ │Storage │ │Notifier  │              │
│         │  Client  │ │   DB   │ │ Manager  │              │
│         └──────────┘ └────────┘ └──────────┘              │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Configuration Module (`config.py`)

**Responsibility**: Environment-based configuration management

**Key Features**:
- Validates all required environment variables
- Provides type-safe configuration objects
- Sets up logging infrastructure
- Creates necessary directories

**Design Decision**: Environment variables over config files for Docker-native deployment and 12-factor app compliance.

### 2. Storage Layer (`storage.py`)

**Two-tier storage approach**:

#### Token Storage (JSON Files)
- One JSON file per authorized user
- File permissions: 600 (owner-only access)
- Simple backup and recovery
- Easy manual inspection and revocation

**Why JSON over database?**
- Simpler for small number of tokens
- No database overhead
- Easy to debug (just cat the file)
- Sufficient security with file permissions

#### Processed Files Database (SQLite)
- Tracks processed files for idempotency
- Supports queries for statistics
- Lightweight and embedded

**Why SQLite?**
- No separate database server needed
- ACID compliance
- Good for append-heavy workload
- Built-in Python support

### 3. Gemini Client (`gemini_client.py`)

**Responsibility**: OCR processing via Gemini API

**Features**:
- Exponential backoff retry logic
- Support for multiple models (flash/pro)
- Image format handling via Pillow
- Comprehensive error handling

**Design Decisions**:
- Retry logic at client level (not processor) for flexibility
- Safety settings permissive for OCR content
- Model selection via configuration for cost/quality tradeoffs

### 4. File Processor (`file_processor.py`)

**Responsibility**: Core OCR pipeline orchestration

**Pipeline Stages**:
1. Validation (file type, already processed)
2. Hash computation (duplicate detection)
3. OCR extraction
4. Output file creation
5. Archive original
6. Update database
7. Send notification

**Key Features**:
- Idempotent processing (never process twice)
- Automatic filename conflict resolution
- Support for both file paths and byte streams
- Account-based tracking for multi-tenant

**Design Decision**: Two processing methods (`process_file` and `process_bytes`) to support both local files and Dropbox downloads efficiently.

### 5. Local Watcher (`local_watcher.py`)

**Responsibility**: Filesystem monitoring for development mode

**Implementation**:
- Uses `watchdog` library for efficient file system events
- Processes existing files on startup
- Debouncing to ensure file write completion
- Single-threaded for simplicity

**Design Decision**: Event-based watching over polling for better resource efficiency in local mode.

### 6. Dropbox OAuth (`dropbox_oauth.py`)

**Responsibility**: Secure OAuth 2.0 authorization with allowlist

**Features**:
- PKCE flow for enhanced security
- Built-in HTTP server for callback
- Account validation via Dropbox API
- Allowlist enforcement
- Automatic token refresh

**Security Measures**:
- CSRF protection via state parameter
- PKCE (code challenge) against interception
- Allowlist checked at authorization time
- Tokens never exposed to client

**Design Decision**: Embedded HTTP server instead of external webhook service for simplicity and self-containment.

### 7. Dropbox Watcher (`dropbox_watcher.py`)

**Responsibility**: Multi-tenant Dropbox App Folder monitoring

**Features**:
- Cursor-based delta sync (only fetch new files)
- Per-account polling
- Automatic token refresh on expiry
- Concurrent account processing

**Design Decisions**:
- Polling over webhooks for reliability and simplicity
- Cursor persistence for efficiency
- Per-account error isolation

### 8. Notification System (`notifications.py`)

**Responsibility**: Multi-channel notifications

**Architecture**:
- Abstract `NotificationProvider` base class
- Concrete implementations: Telegram, Email
- Manager pattern for multi-provider support

**Notification Types**:
- Success notifications (with text excerpt)
- Error notifications (with error details)
- Batch summaries

**Design Decision**: Provider pattern for easy extension to new notification channels.

### 9. Main Orchestrator (`main.py`)

**Responsibility**: Service lifecycle management

**Features**:
- Mode-based component initialization
- Graceful shutdown handling
- Signal handling (SIGINT, SIGTERM)
- Startup validation
- Comprehensive logging

**Startup Flow**:
```
1. Load configuration
2. Validate environment
3. Initialize components
4. Check for tokens (Dropbox mode)
5. Run OAuth if needed
6. Start appropriate watcher
7. Main loop
```

## Data Flow

### Local Mode

```
New file in watch/ 
    → File system event
    → Local Watcher detects
    → File Processor
    → Gemini OCR
    → Save to output/
    → Move to archive/
    → Update database
    → Send notification
```

### Dropbox Mode

```
User uploads to Dropbox App Folder
    → Dropbox stores file
    ↓
[Poll interval expires]
    → Dropbox Watcher queries changes
    → Download new file bytes
    → File Processor
    → Gemini OCR
    → Save to output/
    → Update database
    → Send notification
    → (Optional) Upload result to Dropbox
```

## Security Architecture

### Authentication & Authorization

1. **Dropbox OAuth**:
   - Standard OAuth 2.0 with PKCE
   - App-scoped access (only App Folder)
   - Refresh token for long-term access

2. **Allowlist Validation**:
   - Checked at authorization time
   - Supports account IDs and emails
   - Rejects unauthorized accounts immediately

3. **Token Storage**:
   - File permissions: 600
   - Separate file per user
   - No encryption (host is trusted)

### Data Privacy

- **Local Processing**: All OCR happens on local machine
- **Minimal Data Transfer**: Only image bytes sent to Gemini
- **No External Storage**: Results stay on local filesystem
- **User Isolation**: Each user's App Folder is separate

### Docker Security

- Non-root user (UID 1000)
- Volume mounts for data persistence
- No host network access
- Minimal base image

## Scalability Considerations

### Current Design

- Single-threaded processing
- Sequential file processing
- In-memory cursors
- Single container deployment

**Suitable for**: 
- Small teams (< 10 users)
- Moderate volume (< 100 files/day per user)
- Single-server deployment

### Future Scalability Options

**Horizontal Scaling**:
- Worker pool for parallel processing
- Distributed task queue (Celery, RQ)
- Load balancer for OAuth endpoints

**Performance Optimization**:
- Batch processing for multiple files
- Caching for repeated images
- Async I/O for Dropbox API

**High Availability**:
- Health check endpoints
- Automatic restart on failure
- Database replication

## Error Handling Strategy

### Transient Errors
- Automatic retry with exponential backoff
- Max retry limit to prevent infinite loops
- Detailed logging for debugging

### Permanent Errors
- Mark file as failed in database
- Send error notification
- Continue processing other files

### Graceful Degradation
- Notification failures don't stop processing
- One account failure doesn't affect others
- Missing optional config disables features

## Monitoring & Observability

### Logging Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: Normal operation events
- **WARNING**: Potential issues
- **ERROR**: Error events that don't stop service
- **CRITICAL**: Fatal errors requiring intervention

### Key Metrics to Monitor

- Files processed per hour
- OCR success rate
- Average processing time
- API error rate
- Notification delivery rate

### Health Indicators

- Service uptime
- Authorized accounts count
- Disk space in output/archive
- Database size growth

## Technology Choices

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Language | Python | Best Gemini SDK, rapid development |
| OCR Engine | Gemini | State-of-art accuracy, easy API |
| Token Storage | JSON files | Simple, sufficient for scale |
| Processed Tracking | SQLite | Embedded, ACID, queryable |
| File Watching | watchdog | Cross-platform, event-based |
| Notifications | Telegram/Email | Popular, easy to integrate |
| Containerization | Docker | Portable, isolated, reproducible |

## Future Architecture Considerations

### Potential Enhancements

1. **Web Dashboard**:
   - FastAPI/Flask backend
   - React/Vue frontend
   - WebSocket for real-time updates

2. **REST API**:
   - Direct upload endpoint
   - Status checking
   - Result retrieval

3. **Plugin System**:
   - Custom OCR engines
   - Output formatters
   - Post-processing hooks

4. **Database Migration**:
   - PostgreSQL for multi-instance
   - Shared state across workers
   - Advanced querying

## Deployment Patterns

### Single-Server Deployment (Current)

```
┌──────────────────────────┐
│      Docker Host         │
│  ┌────────────────────┐  │
│  │   OCRBox Container │  │
│  │                    │  │
│  │  ┌──────────────┐  │  │
│  │  │    Service   │  │  │
│  │  └──────────────┘  │  │
│  └────────────────────┘  │
│           │              │
│    ┌──────▼──────┐       │
│    │   Volumes   │       │
│    │  (data/)    │       │
│    └─────────────┘       │
└──────────────────────────┘
```

### Future: Multi-Worker Deployment

```
         ┌──────────────┐
         │ Load Balancer│
         └──────┬───────┘
                │
    ┌───────────┼───────────┐
    ↓           ↓           ↓
┌────────┐  ┌────────┐  ┌────────┐
│Worker 1│  │Worker 2│  │Worker 3│
└───┬────┘  └───┬────┘  └───┬────┘
    │           │           │
    └───────────┼───────────┘
                ↓
         ┌─────────────┐
         │  PostgreSQL │
         └─────────────┘
```

## References

- [Gemini API Documentation](https://ai.google.dev/docs)
- [Dropbox API Reference](https://www.dropbox.com/developers/documentation)
- [OAuth 2.0 Specification](https://oauth.net/2/)
- [12-Factor App Methodology](https://12factor.net/)

