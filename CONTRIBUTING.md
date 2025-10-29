# Contributing to OCRBox

Thank you for your interest in contributing to OCRBox! This document provides guidelines and instructions for contributing.

## 🤝 How to Contribute

### Reporting Issues

- Check existing issues before creating a new one
- Use a clear, descriptive title
- Provide detailed steps to reproduce the issue
- Include relevant logs and error messages
- Specify your environment (OS, Docker version, etc.)

### Suggesting Enhancements

- Use the issue tracker with the "enhancement" label
- Clearly describe the use case and benefits
- Consider backward compatibility

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/ocrbox.git
   cd ocrbox
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the existing code style
   - Add comments for complex logic
   - Update documentation as needed

4. **Test your changes**
   ```bash
   # Test local mode
   ./scripts/test-local.sh
   
   # Check for linting issues
   pylint src/
   
   # Run type checking
   mypy src/
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: brief description"
   ```

6. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a pull request on GitHub.

## 📝 Code Style

### Python

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Maximum line length: 100 characters
- Use docstrings for all public functions and classes

Example:
```python
def process_file(file_path: str, account_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """Process a single image file through OCR pipeline.
    
    Args:
        file_path: Path to image file
        account_id: Optional Dropbox account ID
        
    Returns:
        Tuple of (success, output_path)
    """
    pass
```

### Documentation

- Update README.md for user-facing changes
- Update docs/implementation-plan.md for architectural changes
- Add inline comments for complex logic
- Use clear commit messages

## 🧪 Testing

### Local Testing

1. Set up development environment:
   ```bash
   ./scripts/setup.sh
   ```

2. Configure `.env` for testing:
   ```env
   MODE=local
   GEMINI_API_KEY=your_test_key
   LOG_LEVEL=DEBUG
   ```

3. Run the service:
   ```bash
   docker-compose up
   ```

4. Test with sample images:
   ```bash
   cp test-images/sample.png data/watch/
   ```

### Dropbox Testing

1. Create a test Dropbox app
2. Use a separate test account
3. Test OAuth flow and file processing

## 🔧 Development Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Git

### Local Development (without Docker)

1. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pylint mypy  # Development tools
   ```

3. Run locally:
   ```bash
   export GEMINI_API_KEY=your_key
   export MODE=local
   python -m src.main
   ```

## 📋 Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code follows the project's style guidelines
- [ ] All tests pass
- [ ] New features include appropriate tests
- [ ] Documentation is updated
- [ ] Commit messages are clear and descriptive
- [ ] No unnecessary files are included
- [ ] The PR description explains what and why

## 🚀 Feature Ideas

Looking for something to work on? Check these:

- **Web Dashboard**: Monitoring and management UI
- **Additional OCR Engines**: Support for Tesseract, Azure Vision
- **PDF Support**: Extract text from PDF documents
- **Batch API**: REST API for batch processing
- **Custom Templates**: Configurable output formatting
- **Webhook Support**: Integration notifications
- **Multi-language**: Optimizations for specific languages

## 🐛 Debugging

### Enable Debug Logging

```env
LOG_LEVEL=DEBUG
```

### Access Container Shell

```bash
docker-compose exec ocrbox /bin/bash
```

### Check Database

```bash
docker-compose exec ocrbox python -c "
from src.storage import ProcessedFilesDB
db = ProcessedFilesDB('/app/data/processed.db')
print(db.get_stats())
"
```

## 📞 Getting Help

- 💬 [GitHub Discussions](https://github.com/yourusername/ocrbox/discussions)
- 🐛 [Issue Tracker](https://github.com/yourusername/ocrbox/issues)
- 📖 [Documentation](docs/)

## 📜 License

By contributing to OCRBox, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to OCRBox! 🎉

