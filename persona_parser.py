import time

from bs4 import BeautifulSoup
import sys
import tokenizer
from scrapers import reddit_scraper
import re
import asyncio
from playwright.sync_api import Page, expect

from tokenizer import clean_text


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
    scraped_data = []
    if parameters[0] == "reddit":
        scraped_data = reddit_scraping(parameters[1])
    print("scraped data" + str(len(scraped_data)) + " " + "Starting cleaning")
    clean_data = tokenizer.tokenize(scraped_data)
    end = time.time()
    print(f"Time taken to run the code was {end-start} seconds")
    # print(clean_data)

def reddit_scraping(url):
    """Reddit scraping function
    url: the url to parse"""
    comments = reddit_scraper.parse(url)
    return comments

if __name__ == "__main__":
    main()

