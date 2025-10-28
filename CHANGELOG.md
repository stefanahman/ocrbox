# Changelog

All notable changes to OCRBox will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Automatic folder structure initialization in Dropbox App Folder
- Creates `/ocr_output/` and `/processed/` folders on first poll
- Creates helpful `README.txt` in App Folder with usage instructions
- Filters out files in `/processed/` and `/ocr_output/` from processing queue

### Changed
- **Dropbox workflow now uploads results back to Dropbox**:
  - Extracted text files uploaded to `/ocr_output/` folder
  - Processed images moved to `/processed/` folder (instead of just marking in DB)
  - Original files no longer accumulate in root folder
- Supports generic image types beyond just screenshots (photos, scans, etc.)

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

[1.0.0]: https://github.com/stefanahman/ocrbox/releases/tag/v1.0.0
