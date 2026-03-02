import json
import sys
import time
from pathlib import Path

import tokenizer
from scrapers import reddit_scraper
from text_cleaners import reddit_text_cleaner


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
    persona_rules = load_persona_specifications()
    start = time.time()
    cleaned_data = []
    if parameters[0] == "reddit":
        scraped_data = reddit_scraper.parse(parameters[1])
        cleaned_data = reddit_text_cleaner.clean(scraped_data)

    tokenized_data = tokenizer.tokenize(cleaned_data)
    end = time.time()
    print(f"Time taken to run the code was {end - start} seconds")
    save_output(tokenized_data)


def load_persona_specifications():
    """Load the persona specification file"""
    base_dir = Path(__file__).parent
    resource_file = base_dir / 'resources' / 'persona_specifications.json'

    with resource_file.open('r', encoding='utf-8') as f:
        data = json.load(f)

    return data


def save_output(analyzed_data: dict):
    """Save the analyzed data into a JSON file
    :param analyzed_data: the analyzed data to be saved"""

    base_dir = Path(__file__).parent
    resource_file = base_dir / "resources" / "matched_personas.json"

    resource_file.parent.mkdir(parents=True, exist_ok=True)

    with resource_file.open("w", encoding="utf-8") as f:
        json.dump(analyzed_data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
