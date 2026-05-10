from collections import defaultdict
from pathlib import Path

import persona_parser


def aggregate_user_personas(path: Path,title:str):
    """
      Aggregate comment-level persona matches to assign dominant persona(s) to each user,
    including counts per persona and total occurrences across all users.
    param: path the path to save the file
    param: title the title of the thread
    :return: Dictionary of users -> dominant persona(s)
    """
    save_path = Path(f"resources/aggregated_personas/aggregated_personas_{title}.json")
    matched_personas = persona_parser.load_file(path)

    user_counts = {}
    for persona, sentiment_dict in matched_personas.items():
        for sentiment, entries in sentiment_dict.items():
            persona_with_sentiment = f"{persona} ({sentiment})"
            for entry in entries:
                user = entry["user"]
                if user not in user_counts:
                    user_counts[user] = {}
                if persona_with_sentiment not in user_counts[user]:
                    user_counts[user][persona_with_sentiment] = 0
                user_counts[user][persona_with_sentiment] += 1

    user_personas = {}

    for user, counts in user_counts.items():
        max_count = max(counts.values())
        dominant_personas = {p: c for p, c in counts.items() if c == max_count}
        user_personas[user] = dominant_personas

    total_persona_counts = defaultdict(int)
    for counts in user_counts.values():
        for persona, count in counts.items():
            total_persona_counts[persona] += count

    output = {
        "users": user_personas,
        "totals": dict(total_persona_counts)
    }

    persona_parser.save_output(
        output,
        Path(save_path)
    )
