# Changelog

All notable changes to OCRBox will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2025-10-29

### 🎉 Major Features

#### Smart Tagging & Categorization
- **Automatic tagging** with confidence scores powered by LLM
- **Hybrid tag system**: Default tags from `tags.txt` + learned tags from user filenames
- **Category-first filenames**: `[tag1][tag2]_descriptive-title.txt` format
- **Confidence thresholds**: Configurable minimum confidence for primary (80%) and additional (70%) tags
- **Tag learning**: System automatically discovers new tags from user-modified filenames in `/Outbox/`

#### Improved Folder Structure
- **`/Inbox/`**: Drop images here for processing (replaces root folder)
- **`/Outbox/`**: Tagged and titled text files (replaces `/ocr_output/`)
- **`/Archive/`**: Processed original images (replaces `/processed/`)
- **`/Logs/`**: Detailed processing logs with 4 subdirectories:
  - `llm_responses/`: Raw LLM JSON responses with confidence scores
  - `processing/`: Processing audit trail (timing, status, paths)
  - `categories/`: Tag assignment history with confidence
  - `errors/`: Error logs with stack traces

#### Enhanced LLM Output
- **Structured JSON response**: `text`, `title`, `tags[]` with confidence scores
- **Markdown formatting**: Headers (`##`), bullet lists (`*`), numbered lists (`1. 2. 3.`)
- **Auto-generated titles**: Descriptive 5-30 character titles sanitized for filenames
- **Smart text extraction**: Logical paragraphs instead of preserving visual layout

#### Multi-User Support
- **Persistent OAuth server**: `OAUTH_ALWAYS_ENABLED` flag keeps server running
- **Concurrent authorization**: Multiple users can authorize without service interruption
- **Per-user folder structure**: Automatic initialization on first authorization

### Added
- `TagManager` class for loading and learning tags
- `FilenameGenerator` class for sanitized, category-first filenames
- `LogWriter` class for detailed logging in 4 categories
- Enhanced SQLite schema with v2 metadata (tags, confidence, title, duration)
- Default `tags.txt` file with 10 common categories
- Comprehensive v2 configuration options (9 new env vars)
- Tag confidence validation and filtering
- Support for 1-3 tags per file (configurable)
- Title length limits (5-30 characters, configurable)

### Changed
- **Breaking**: Folder structure completely redesigned for v2
- **Breaking**: Output filename format changed to `[tags]_title.txt`
- LLM prompt redesigned for markdown output and tag selection
- Gemini client now returns structured JSON with tags and confidence
- Notifications include tags with confidence scores
- File processor refactored for tag pipeline integration
- Local watcher updated to use Inbox directory
- Dropbox watcher creates v2 folder structure and `tags.txt`

### Enhanced
- More detailed logging throughout the pipeline
- Better error handling with comprehensive error logs
- Improved notification messages with tag information
- SQLite schema expanded to track v2 metadata

### Documentation
- Updated README with v2 features and folder structure
- Updated QUICKSTART with v2 setup instructions
- Created MULTI_USER_SETUP guide for OAuth configuration
- Updated `.env.example` with v2 configuration options
- Enhanced inline code documentation

## [1.0.0] - 2025-10-27

## [1.0.0] - 2025-10-27

### Added

- Initial release of OCRBox
- Google Gemini OCR integration (gemini-1.5-flash and gemini-1.5-pro support)
- Local folder watching mode for development
- Dropbox App Folder integration with OAuth 2.0
- Multi-tenant support with allowlist validation
- JSON-based token storage with file permissions
- SQLite database for processed files tracking (idempotency)
- Telegram notification support
- Email notification support (prepared interface)
- Automatic retry logic with exponential backoff
- Docker containerization with docker-compose
- Comprehensive documentation (README, Architecture, Quick Start)
- Setup and testing scripts
- Graceful shutdown handling
- Environment-based configuration
- File archiving after successful processing
- PKCE OAuth flow for enhanced security

### Security

- OAuth tokens stored with 600 permissions
- Non-root Docker user (UID 1000)
- Allowlist-based access control
- CSRF protection in OAuth flow
- PKCE code challenge for OAuth

### Documentation

- Comprehensive README with setup instructions
- Architecture documentation
- Quick start guide
- Contributing guidelines
- Implementation plan
- Example environment configuration

[1.0.0]: https://github.com/yourusername/ocrbox/releases/tag/v1.0.0
