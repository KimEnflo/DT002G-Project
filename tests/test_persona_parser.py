"""
Unit tests for the persona generation system.

These tests verify:
- Persona configuration loading
- Comment filtering logic
- Text preprocessing (URL removal, structure validation)
- Output file generation
- Keyword-based persona classification

Tests are designed to be isolated and do not require live Reddit data.
"""

import json
import persona_parser
import time
from text_cleaners import reddit_text_cleaner
from comment_analyzer import analyze_comment


# ------------------------------------------------------------
# Persona configuration loading
# ------------------------------------------------------------

def test_load_persona_file():
    """
    Verify that persona specification file is loaded correctly.

    Ensures:
    - The returned object is a dictionary
    - The configuration is not empty
    """
    data = persona_parser.load_persona_specifications()

    assert isinstance(data, dict)
    assert len(data) > 0


# ------------------------------------------------------------
# Comment filtering
# ------------------------------------------------------------

def test_filter_deleted_comment():
    """
    Verify that deleted or invalid comments are filtered out.
    """
    assert reddit_text_cleaner.filter_comments("[deleted]") is False
    assert reddit_text_cleaner.filter_comments("This is valid text") is True


# ------------------------------------------------------------
# Text preprocessing
# ------------------------------------------------------------

def test_url_removal():
    """
    Verify that URLs are removed during text cleaning.
    """
    result = reddit_text_cleaner.clean_text(
        {
            "body": "Check this out https://example.com",
            "parent_id": "",
            "id": "test"
        },
        previous={}
    )

    assert result is not None
    assert "https://example.com" not in result["text"]
    assert "example.com" not in result["text"]


def test_cleaner_returns_text_only():
    """
    Verify that clean_text returns structured output
    containing a text field of type string.
    """
    comment = {
        "body": "Some text",
        "id": "1",
        "parent_id": ""
    }

    result = reddit_text_cleaner.clean_text(comment, previous={})

    assert result is not None
    assert "text" in result
    assert isinstance(result["text"], str)


# ------------------------------------------------------------
# Output generation
# ------------------------------------------------------------

def test_save_output(tmp_path):
    """
    Verify that analyzed data is correctly written to a JSON file.

    Uses pytest tmp_path to ensure test isolation.
    """
    test_data = {"Test": {"positive": [], "neutral": [], "negative": []}}

    output_file = tmp_path / "output.json"

    persona_parser.save_output(test_data, output_file)

    assert output_file.exists()

    with output_file.open() as f:
        assert json.load(f) == test_data


# ------------------------------------------------------------
# Persona classification
# ------------------------------------------------------------

def test_keyword_matching():
    """
    Verify that keyword-based persona matching works correctly.
    """
    comments = {
        "1": {
            "text": "I love Python programming",
            "quotes": [],
            "parent_text": ""
        }
    }

    persona_rules = {
        "Programmer": {
            "keywords": ["python"]
        }
    }

    result = analyze_comment(comments, persona_rules, "reddit")

    assert "Programmer" in result

# ------------------------------------------------------------
# Performance test
# ------------------------------------------------------------

def test_performance_basic():
    comments = {
        str(i): {
            "text": "test python",
            "quotes": [],
            "parent_text": ""
        }
        for i in range(1000)
    }

    persona_rules = {
        "TestPersona": {
            "keywords": ["python"]
        }
    }

    start = time.time()

    analyze_comment(comments, persona_rules, "reddit")

    end = time.time()

    assert (end - start) < 60