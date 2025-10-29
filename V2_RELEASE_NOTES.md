# OCRBox v2 Release Notes 🎉

## What's New in v2

OCRBox v2 is a major upgrade that transforms OCRBox from a simple OCR service into an **intelligent document organization system** with automatic tagging, smart titles, and comprehensive logging.

## 🌟 Major Features

### 1. Smart Tagging System
- **Automatic categorization** powered by Gemini LLM
- **Hybrid tag management**: Default tags + learned tags from your filenames
- **Confidence scores** (0-100) for each tag assignment
- **Configurable thresholds**: 80% for primary, 70% for additional tags
- **Tag learning**: System discovers new tags from user-modified filenames

### 2. Intelligent Filenames
- **Category-first format**: `[tag1][tag2]_descriptive-title.txt`
- **Auto-generated titles**: 5-30 character descriptive names
- **Sanitized output**: lowercase, hyphens, alphanumeric only
- **Alphabetical sorting**: Primary tag first for easy browsing

**Examples:**
- `[receipts]_starbucks-coffee.txt`
- `[receipts][shopping]_grocery-bill.txt`
- `[work][documents]_meeting-notes.txt`

### 3. Reorganized Folder Structure
```
/Inbox/       - Drop images here for processing
/Outbox/      - Tagged text files with smart names
  └─ tags.txt - Customize your categories
/Archive/     - Processed original images
/Logs/        - Detailed processing logs
  ├─ llm_responses/  - Raw LLM JSON with confidence
  ├─ processing/     - Audit trail (timing, paths)
  ├─ categories/     - Tag assignments
  └─ errors/         - Error logs with stack traces
```

### 4. Enhanced LLM Output
- **Structured JSON**: `text`, `title`, `tags[]` with confidence
- **Markdown formatting**: Headers (`##`), lists (`*`, `1. 2. 3.`)
- **Logical paragraphs**: No more preserved visual layouts
- **Better readability**: Clean, well-structured text

### 5. Multi-User Support
- **Persistent OAuth server**: `OAUTH_ALWAYS_ENABLED=true`
- **Concurrent authorization**: Multiple users can authorize anytime
- **No service interruption**: OAuth runs alongside file watcher

### 6. Comprehensive Logging
Four types of detailed logs in `/Logs/`:

1. **LLM Responses** (`llm_responses/`):
   - Raw JSON from Gemini API
   - All confidence scores
   - Complete structured output

2. **Processing Audit** (`processing/`):
   - Start/end timestamps
   - Processing duration
   - File paths (input → output → archive)
   - Success/failure status

3. **Category Assignment** (`categories/`):
   - Selected tags with confidence
   - Primary vs. additional tags
   - Tag validation results

4. **Errors** (`errors/`):
   - Exception details
   - Stack traces
   - Context information

## 📦 New Files & Components

### New Source Files
- `src/tag_manager.py` - Tag loading and learning
- `src/filename_generator.py` - Smart filename generation
- `src/log_writer.py` - Detailed logging system
- `src/file_processor_v2.py` - Refactored processing pipeline

### Updated Files
- `src/config.py` - 9 new v2 configuration options
- `src/gemini_client.py` - Structured output support
- `src/notifications.py` - Tag-aware notifications
- `src/dropbox_watcher.py` - v2 folder management
- `src/local_watcher.py` - Inbox/Outbox support
- `src/main.py` - Multi-user OAuth threading

### Updated Documentation
- `README.md` - v2 features and examples
- `docs/QUICKSTART.md` - v2 setup instructions
- `CHANGELOG.md` - Comprehensive v2 changelog
- `.env.example` - New configuration options

## ⚙️ New Configuration Options

```env
# v2 Tag Features
ENABLE_TAGS=true
ENABLE_AUTO_TITLES=true
ENABLE_TAG_LEARNING=true

# v2 Confidence Thresholds
PRIMARY_TAG_CONFIDENCE_THRESHOLD=80
ADDITIONAL_TAG_CONFIDENCE_THRESHOLD=70

# v2 Output Formatting
MAX_TITLE_LENGTH=30
MAX_TAGS_PER_FILE=3

# v2 Detailed Logging
ENABLE_DETAILED_LOGS=true

# OAuth Server
OAUTH_ALWAYS_ENABLED=true
```

## 🚀 Getting Started with v2

### Existing Users

1. **Update your `.env` file**:
   ```bash
   # Add v2 config options (see .env.example)
   ENABLE_TAGS=true
   OAUTH_ALWAYS_ENABLED=true
   ```

2. **Restart the service**:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

3. **Re-authorize users** (folder structure will auto-update):
   - Visit `http://localhost:8080`
   - Authorize with Dropbox
   - New `/Inbox/`, `/Outbox/`, `/Archive/`, `/Logs/` folders created

### New Users

Follow the [QUICKSTART guide](docs/QUICKSTART.md) for complete setup instructions.

## 📊 How Tagging Works

### 1. Upload Image
Drop an image in `/Inbox/`:
```
screenshot.png
```

### 2. LLM Analysis
Gemini extracts text and assigns tags:
```json
{
  "text": "Starbucks\nGrande Latte: $5.75\nTotal: $5.75",
  "title": "starbucks-coffee",
  "tags": [
    {"name": "receipts", "confidence": 95, "primary": true},
    {"name": "shopping", "confidence": 82, "primary": false}
  ]
}
```

### 3. Output File
Tagged file appears in `/Outbox/`:
```
[receipts][shopping]_starbucks-coffee.txt
```

### 4. Logs Created
- `/Logs/llm_responses/screenshot.json` - Full LLM output
- `/Logs/processing/screenshot.json` - Processing details
- `/Logs/categories/screenshot.json` - Tag decisions
- `/Logs/errors/screenshot.json` - (only if error)

## 🎓 Tag Learning Example

### Step 1: Process a File
OCRBox creates:
```
[receipts]_coffee.txt
```

### Step 2: You Rename It
In Dropbox, rename to:
```
[groceries][shopping]_weekly-coffee.txt
```

### Step 3: System Learns
Next file processing uses learned tags:
- Available tags now include: `groceries`, `shopping`
- LLM can select these for similar content

## 🔧 Customizing Tags

Edit `/Outbox/tags.txt` in Dropbox:

```text
# Your custom categories
receipts
groceries
bills
contracts
recipes
workout
medical
travel
family
projects
```

## 🎯 Use Cases

### Personal Finance
- Auto-tag receipts, invoices, bills
- Sort by category: `[receipts]`, `[bills]`, `[invoices]`
- Easy searching in `/Outbox/`

### Work Documents
- Tag meeting notes, contracts, reports
- Categories: `[work]`, `[personal]`, `[projects]`
- Organized by content type

### Health Records
- Categorize medical documents
- Tags: `[health]`, `[medical]`, `[prescriptions]`
- Quick access to specific records

### Travel
- Organize boarding passes, hotel bookings
- Tags: `[travel]`, `[booking]`, `[tickets]`
- Trip documentation made easy

## 📈 Performance

- **Processing time**: ~5-10 seconds per image
- **Tag assignment**: < 1 second
- **Learning overhead**: Negligible
- **Log writing**: Async, non-blocking

## 🔒 Privacy & Security

- All tag processing happens via Gemini API
- Only image bytes and extracted text sent to Google
- Tags stored locally in SQLite
- Logs written locally (or to Dropbox `/Logs/`)
- No third-party analytics or tracking

## 🐛 Known Limitations

1. **Tag learning accuracy**: Depends on consistent filename patterns
2. **Max tags**: Limited to 3 per file (configurable to 5)
3. **Title length**: Truncated to 30 characters (configurable)
4. **Language support**: Optimized for English (Gemini supports 100+ languages)

## 🛣️ Future Roadmap

Potential v3 features:
- [ ] Tag synonyms and aliases
- [ ] Multi-language tag sets
- [ ] Tag hierarchy (parent/child categories)
- [ ] Custom LLM prompts per tag
- [ ] Batch reprocessing with new tags
- [ ] Web UI for tag management
- [ ] Export logs to CSV/JSON
- [ ] Tag statistics and insights

## 💬 Feedback

Have ideas for v3? Open an issue or contribute!

## 📝 Migration from v1

### Breaking Changes
- Folder structure changed (automatic migration on re-auth)
- Output filename format changed
- No backward compatibility with v1 folder structure

### Migration Steps
1. Backup your data directory
2. Update to v2
3. Re-authorize users
4. Test with a sample image
5. Enjoy smart tagging!

---

**OCRBox v2** - Smart OCR with Intelligent Tagging 📸→📝🏷️

Released: October 29, 2025

