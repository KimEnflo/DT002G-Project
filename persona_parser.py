import json
import time
from pathlib import Path

import comment_analyzer
import keyword_extractor

def main():
    """Main function acting as the start of the program"""
    # In the recreation package all datasets are gathered and cleaned.
    # The method runs every thread for 3 iterations with and without context recreating the results.
    run_all()


def run_all(use_context: bool = True):
    """
    Run the program for all datasets three times each.
    :param use_context: If context should be included or not
    :return:
    """
    data_sets_path = Path("resources/data_sets/context")
    datasets = list(data_sets_path.glob("thread_*.json"))
    save_path = Path("resources/matched_personas/rule-based")

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
                    print(f"  Iteration {iteration} done in {time.time() - start:.2f}s")

            except Exception as e:
                print(f"  Error on {title}: {e}")
                raise
        use_context = False
        i+=1

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
