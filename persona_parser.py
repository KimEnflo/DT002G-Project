import argparse
import json
import time
from pathlib import Path

import winsound

import aggregate_personas
import comment_analyzer
import keyword_extractor
import visualize_output
from scrapers import reddit_scraper
from text_cleaners import reddit_text_cleaner


def main():
    """Main function acting as the start of the program"""
    parser = argparse.ArgumentParser(
        description="Persona parser for Reddit comments or other platforms."
    )

    parser.add_argument("platform", help="Platform to use")
    parser.add_argument("url", help="URL of the thread to parse")

    parser.add_argument(
        "--no-context",
        action="store_false",
        dest="context",
        help="Disable including parent/quote context (default: context included)"
    )

    parser.add_argument(
        "-p", "--platform",
        default="reddit",
        help="Specify platform (default: reddit)"
    )

    args = parser.parse_args()

    try:
        parse(args)
    except AssertionError as msg:
        print(msg)


def parse(args):
    """
    Main parsing function.
    :param args: argparse.Namespace with attributes:
                 - url: URL of the thread
                 - platform: platform name (default "reddit")
                 - context: bool, whether to include parent/quote context
    """
    run_all()
    # for iteration in range(3):
    #     title = ""
    #     cleaned_data = {}
    #     start = time.time()
    #     iteration += 1
    #     if args.platform.lower() == "reddit":
    #         scraped_data = reddit_scraper.parse(args.url)
    #         title = scraped_data["title"]
    #         cleaned_data = reddit_text_cleaner.clean(scraped_data)
    #         save_output(cleaned_data, Path(f"resources/data_sets/thread_{title}.json"))
    #         title = cleaned_data["title"]
    #     persona_rules = load_file(Path("persona_specifications.json")) if iteration == 0 \
    #         else load_file(
    #         Path(f"resources/persona_specifications"
    #              f"/{title}"
    #              f"/Iteration {iteration}"
    #              f"/persona_specifications.json"))
    #     analyzed_data = comment_analyzer.analyze_comment(
    #         cleaned_data,
    #         persona_rules,
    #         iteration,
    #         platform=args.platform,
    #         use_context=getattr(args, "context", False)
    # )
    #     end = time.time()
    #     save_output(analyzed_data, Path(f"resources/matched_personas/matched_personas_{title}.json"))
    #     aggregate_personas.aggregate_user_personas(title)
    #     data = keyword_extractor.extract_persona_keywords(analyzed_data, iteration, title)
    #     visualize_output.visualise_output(data)
    #     print(f"Time taken to run iteration{iteration} was {end - start} seconds")


def run_all(use_context: bool = True):
    """
    Run the program for all datasets three times each.
    :param use_context: If context should be included or not
    :return:
    """
    data_sets_path = Path("resources/data_sets/context")
    datasets = list(data_sets_path.glob("thread_*.json"))
    save_path = Path("resources/matched_personas/rule-based")
    duration = 1000
    freq = 440
    if not datasets:
        print(f"No datasets found in {data_sets_path}")
        return

    for i in range(2):
        save_directory = "/context" if use_context else "/no-context"
        full_path = Path(f"{save_path}{save_directory}")
        for dataset_path in datasets:
            title = dataset_path.stem.removeprefix("thread_")
            print(f"\n{'=' * 60}\nProcessing: {title}\n{'=' * 60}")

            try:
                for iteration in range(3):
                    start = time.time()
                    persona_rules = load_file(Path("persona_specifications.json")) if iteration == 0 \
                        else load_file(Path(
                        f"resources/persona_specifications/{title}/Iteration {iteration}/persona_specifications.json"
                    ))
                    iteration += 1
                    cleaned_data = load_file(dataset_path)
                    analyzed_data = comment_analyzer.analyze_comment(
                        cleaned_data, persona_rules, iteration,
                        platform="reddit", use_context=use_context,
                    )
                    path_extension =  Path(f"{full_path}/matched_personas_{title}.json")
                    save_output(analyzed_data,path_extension)
                    aggregate_personas.aggregate_user_personas(path_extension,title)
                    data = keyword_extractor.extract_persona_keywords(analyzed_data, iteration, title)
                    visualize_output.visualise_output(data)
                    print(f"  Iteration {iteration} done in {time.time() - start:.2f}s")

            except Exception as e:
                print(f"  Error on {title}: {e}")
                raise
        use_context = False
        i+=1
    winsound.Beep(freq, duration)

def load_file(path: Path) -> dict:
    """Load the JSON file from the given path
     :return: Dictionary of the data loaded"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def save_output(data: dict, output_path: Path):
    """Save data in a JSON file
    :param output_path: the path of the output file
    :param data: the analyzed data to be saved"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
