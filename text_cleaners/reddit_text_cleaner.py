import html
import re
from typing import Any

import markdown2
from bs4 import BeautifulSoup

def clean(comments: list) -> dict:
    """Clean the data and map it to a dictionary
    :param: comments: list of comments
    :returns: dictionary with cleaned data"""
    dictionary = {}
    for index, comment in enumerate(comments):

        if not filter_comments(comment["body"]):
            continue

        clean_comments = clean_text(comment,dictionary)
        if clean_comments:
            dictionary[comment["id"]] = clean_comments

    return dictionary


def clean_text(comment: dict,previous:dict) -> dict[str, str | list[Any]] | None:
    """clean the comment by removing whitespaces and urls
    :param: comment: comment body text
    :returns: dictionary with cleaned data or None for dropped comments"""

    raw_comment = html.unescape(comment["body"])
    lines = raw_comment.splitlines()
    quotes = []
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        level = 0
        while level < len(line) and line[level] == ">":
            level += 1

        raw_text = line[level:].strip() if level else line

        # Remove URLs
        raw_text = re.sub(r'https?://[^\s\])}]*', '', raw_text)
        raw_text = re.sub(r'\b(?:www\.)?\w+\.\w{2,}\S*', '', raw_text)

        html_text = markdown2.markdown(raw_text)
        text = BeautifulSoup(html_text, "html.parser").get_text(strip=True)
        text = re.sub(r'\s+', ' ', text)

        if not text:
            continue

        if level > 0:
            quotes.append({"level": level, "text": text})
        else:
            cleaned_lines.append(text)
    parent_text = ""
    parent_id = comment["parent_id"]
    if parent_id.startswith("t1_"):
        parent_comment_id = parent_id[3:]

        parent_comment = previous.get(parent_comment_id)

        if parent_comment:
            parent_text = parent_comment["text"]

    result = {
        "text": " ".join(cleaned_lines),
        "quotes": quotes,
        "parent_text": parent_text
    }
    if not result["text"] and not result["quotes"]:
        return None

    return result


def filter_comments(comment: str) -> bool:
    """Filter out deleted, removed comments, bot comments and GIFs
    :param: comment: comment body text
    :returns: boolean with True or False"""
    filters = ("[deleted]", "[removed]", "i am a bot", "![gif]", "this is a bot", "removed by reddit")
    return not any(x in comment.lower() for x in filters)
