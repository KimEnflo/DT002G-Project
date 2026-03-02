import time

from bs4 import BeautifulSoup
import sys
import tokenizer
from scrapers import reddit_scraper
from text_cleaners import reddit_text_cleaner
import re
import asyncio
from playwright.sync_api import Page, expect

def main():
    """Main function acting as the start of the program"""
    try:
        if len(sys.argv) < 3:
            print("Usage: python -m persona_parser <parser> <url>")
            return

        args = (sys.argv[1], sys.argv[2])
        parse(args)
    except AssertionError as msg:
        print(msg)

def parse(parameters):
    """Main parsing function
    parameters: the console arguments <platform> <url>"""
    start = time.time()
    cleaned_data  = []
    if parameters[0] == "reddit":
        scraped_data = reddit_scraper.parse(parameters[1])
        cleaned_data = reddit_text_cleaner.clean(scraped_data)

    tokenized_data = tokenizer.tokenize(cleaned_data)
    end = time.time()
    print(f"Time taken to run the code was {end-start} seconds")
    for comment in tokenized_data:
        print(tokenized_data[comment])

if __name__ == "__main__":
    main()

