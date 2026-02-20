from bs4 import BeautifulSoup
import sys
import tokenizer
from scrapers import reddit_scraper
import re
import asyncio
from playwright.sync_api import Page, expect

def main():
    """Main function acting as the start of the program"""
    try:
        if len(sys.argv) < 3:
            print("Usage: python -m persona_parser <parser> <url>")
            return
        args = (sys.argv[1], sys.argv[2] + ".json")
        parse(args)
    except AssertionError as msg:
        print(msg)

def parse(parameters):
    """Main parsing function
    parameters: the console arguments <platform> <url>"""
    if parameters[0] == "reddit":
        reddit_scraping(parameters[1])

def reddit_scraping(url):
    """Reddit scraping function
    url: the url to parse"""
    comments = reddit_scraper.parse(url)
    print(f"Found {len(comments)} comments")
    for comment in comments:
        print("Comment:", comment["body"])


if __name__ == "__main__":
    main()

