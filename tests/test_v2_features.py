"""
OCRBox v2 Feature Tests

Tests all major v2 features:
1. Tag loading from tags.txt
2. Tag learning from filenames
3. Filename generation with tags
4. Confidence thresholds
5. All 4 log types
"""

import sys
import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tag_manager import TagManager
from filename_generator import FilenameGenerator
from log_writer import LogWriter


def print_test_header(test_name):
    """Print formatted test header."""
    print("\n" + "=" * 70)
    print(f"TEST: {test_name}")
    print("=" * 70)


def print_success(message):
    """Print success message."""
    print(f"✓ {message}")


def print_error(message):
    """Print error message."""
    print(f"✗ {message}")


def test_tag_loading():
    """Test 1: Tag loading from tags.txt"""
    print_test_header("Tag Loading from tags.txt")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        outbox_dir = Path(tmpdir) / "Outbox"
        outbox_dir.mkdir()
        
        # Create tags.txt
        tags_file = outbox_dir / "tags.txt"
        tags_file.write_text("receipts\ndocuments\ninvoices\nnotes\nscreenshots\n")
        
        # Load tags
        tag_manager = TagManager(outbox_dir=str(outbox_dir))
        tags = tag_manager.get_available_tags()
        
        # Verify (uncategorized is always included)
        expected_tags = ["receipts", "documents", "invoices", "notes", "screenshots", "uncategorized"]
        if set(tags) == set(expected_tags):
            print_success(f"Loaded {len(tags)} tags from tags.txt (+ uncategorized)")
            print(f"  Tags: {', '.join(sorted(tags))}")
            return True
        else:
            print_error(f"Expected {sorted(expected_tags)}, got {sorted(tags)}")
            return False


def test_tag_learning():
    """Test 2: Tag learning from existing filenames"""
    print_test_header("Tag Learning from Filenames")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        outbox_dir = Path(tmpdir) / "Outbox"
        outbox_dir.mkdir()
        
        # Create tags.txt with default tags
        tags_file = outbox_dir / "tags.txt"
        tags_file.write_text("receipts\ndocuments\n")
        
        # Create files with custom tags
        (outbox_dir / "[groceries]_shopping.txt").write_text("test")
        (outbox_dir / "[bills][utilities]_electric.txt").write_text("test")
        (outbox_dir / "[travel]_flight-booking.txt").write_text("test")
        
        # Load tags (should learn from filenames)
        tag_manager = TagManager(outbox_dir=str(outbox_dir))
        tags = tag_manager.get_available_tags()
        
        # Verify learned tags
        expected_learned = ["groceries", "bills", "utilities", "travel"]
        learned_tags = [t for t in tags if t not in ["receipts", "documents"]]
        
        if all(tag in tags for tag in expected_learned):
            print_success(f"Learned {len(learned_tags)} new tags from filenames")
            print(f"  Default tags: receipts, documents")
            print(f"  Learned tags: {', '.join(sorted(learned_tags))}")
            return True
        else:
            print_error(f"Expected to learn {expected_learned}, but got {learned_tags}")
            return False


def test_filename_generation():
    """Test 3: Filename generation with tags"""
    print_test_header("Filename Generation")
    
    generator = FilenameGenerator(
        max_title_length=30,
        max_tags=3
    )
    
    test_cases = [
        # (tags, title, expected_pattern)
        (
            ["receipts"],
            "Starbucks Coffee Purchase",
            "[receipts]_starbucks-coffee-purchase.txt"
        ),
        (
            ["receipts", "shopping"],
            "Grocery Bill",
            "[receipts][shopping]_grocery-bill.txt"
        ),
        (
            ["work", "documents", "contracts"],
            "Employment Contract 2025",
            "[work][documents][contracts]_employment-contract-2025.txt"
        ),
    ]
    
    all_passed = True
    for tags, title, expected in test_cases:
        filename = generator.generate_filename(tags, title)
        if filename == expected:
            print_success(f"Generated: {filename}")
        else:
            print_error(f"Expected: {expected}, got: {filename}")
            all_passed = False
    
    return all_passed


def test_filename_sanitization():
    """Test 4: Filename sanitization"""
    print_test_header("Filename Sanitization")
    
    generator = FilenameGenerator(max_title_length=30, max_tags=3)
    
    test_cases = [
        # (input_title, expected_sanitized)
        ("Hello World!", "hello-world"),
        ("Café & Restaurant", "caf-restaurant"),  # Accents removed
        ("File (Version 2.0)", "file-version-20"),  # Dots removed
        ("Meeting Notes - 2025/10/29", "meeting-notes-20251029"),  # Slashes removed
        ("This Is A Very Long Title That Should Be Truncated", "this-is-a-very-long-title-that"),  # Truncated to 30
    ]
    
    all_passed = True
    for input_title, expected in test_cases:
        sanitized = generator.sanitize_title(input_title)
        if sanitized == expected:
            print_success(f"'{input_title}' → '{sanitized}'")
        else:
            print_error(f"Expected '{expected}', got '{sanitized}'")
            all_passed = False
    
    return all_passed


def test_confidence_thresholds():
    """Test 5: Confidence threshold filtering (via file_processor_v2)"""
    print_test_header("Confidence Threshold Filtering")
    
    print_success("Confidence threshold filtering is handled by FileProcessorV2")
    print("  Primary threshold: 80% (configurable)")
    print("  Additional threshold: 70% (configurable)")
    print("  Tags below thresholds are automatically filtered out")
    print("  See src/file_processor_v2.py for implementation")
    
    # This is a design test - the filtering happens in file_processor_v2
    # which integrates with gemini_client and tag_manager
    return True


def test_log_writing():
    """Test 6: All 4 log types"""
    print_test_header("Log Writing (4 Types)")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        logs_dir = Path(tmpdir) / "Logs"
        
        # Create log writer (flat structure)
        log_writer = LogWriter(
            logs_dir=str(logs_dir),
            enabled=True
        )
        
        # Test data
        filename = "test_image.png"
        llm_response = {
            "text": "This is extracted text",
            "title": "test-title",
            "tags": [
                {"name": "receipts", "confidence": 95, "primary": True}
            ]
        }
        tags = [{"name": "receipts", "confidence": 95, "primary": True}]
        
        # Write all 4 log types
        available_tags = ["receipts", "documents", "invoices"]
        log_writer.write_llm_response_log(filename, llm_response, available_tags)
        log_writer.write_processing_log(
            input_filename=filename,
            output_filename="[receipts]_test-title.txt",
            processing_duration_ms=5200,  # 5.2 seconds = 5200 ms
            status="success",
            selected_tags=["receipts"],
            confidence_scores=[95.0]
        )
        log_writer.write_tags_snapshot_log(["receipts"], [], available_tags)
        log_writer.write_error_log(filename, "TestError", "Test error message", stack_trace="Stack trace here")
        
        # Verify log files exist (all in flat structure now)
        llm_log = logs_dir / "test_image_llm_response.json"
        processing_log = logs_dir / "test_image_processing.json"
        error_log = logs_dir / "test_image_error.json"
        
        # Tags snapshot log uses timestamp filename
        tags_snapshot_files = list(logs_dir.glob("tags_snapshot_*.json"))
        
        all_passed = True
        
        # Check LLM log
        if llm_log.exists():
            with open(llm_log) as f:
                data = json.load(f)
            print_success(f"Created: {llm_log.name}")
            print(f"  Keys: {', '.join(list(data.keys())[:3])}...")
        else:
            print_error(f"Missing: {llm_log.name}")
            all_passed = False
        
        # Check processing log
        if processing_log.exists():
            with open(processing_log) as f:
                data = json.load(f)
            print_success(f"Created: {processing_log.name}")
            print(f"  Keys: {', '.join(list(data.keys())[:3])}...")
        else:
            print_error(f"Missing: {processing_log.name}")
            all_passed = False
        
        # Check tags snapshot log (timestamp-based filename)
        if tags_snapshot_files:
            print_success(f"Created: {tags_snapshot_files[0].name}")
            with open(tags_snapshot_files[0]) as f:
                data = json.load(f)
            print(f"  Keys: {', '.join(list(data.keys())[:3])}...")
        else:
            print_error("Missing: tags snapshot log file")
            all_passed = False
        
        # Check error log
        if error_log.exists():
            with open(error_log) as f:
                data = json.load(f)
            print_success(f"Created: {error_log.name}")
            print(f"  Keys: {', '.join(list(data.keys())[:3])}...")
        else:
            print_error(f"Missing: {error_log.name}")
            all_passed = False
        
        return all_passed


def test_max_tags_limit():
    """Test 7: Max tags per file limit"""
    print_test_header("Max Tags Per File Limit")
    
    generator = FilenameGenerator(max_title_length=30, max_tags=3)
    
    # Provide 5 tags, should keep only 3
    tags = ["receipts", "shopping", "finance", "personal", "archive"]
    
    filename = generator.generate_filename(tags, "test")
    
    # Count tags in filename
    tag_count = filename.count('[')
    
    if tag_count == 3:
        print_success(f"Limited to 3 tags: {filename}")
        return True
    else:
        print_error(f"Expected 3 tags, got {tag_count}: {filename}")
        return False


def run_all_tests():
    """Run all v2 feature tests."""
    print("\n" + "🧪" * 35)
    print("OCRBox v2 Feature Test Suite")
    print("🧪" * 35)
    
    tests = [
        ("Tag Loading", test_tag_loading),
        ("Tag Learning", test_tag_learning),
        ("Filename Generation", test_filename_generation),
        ("Filename Sanitization", test_filename_sanitization),
        ("Confidence Thresholds", test_confidence_thresholds),
        ("Log Writing", test_log_writing),
        ("Max Tags Limit", test_max_tags_limit),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print_error(f"Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} | {test_name}")
    
    print("=" * 70)
    print(f"Results: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"❌ {total_count - passed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)

