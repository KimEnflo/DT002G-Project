import spacy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

nlp = spacy.load("en_core_web_lg")


def analyze_comment(comments: dict, persona_rules: dict,iteration:int, platform: str, use_context: bool) -> dict:
    """Analyze Reddit comments for persona matches and sentiment, including parent and quotes
    :param platform: The platform used to fetch the comments
    :param comments: Dictionary of cleaned comments, keyed by comment ID.
                     Each comment should have 'text', 'quotes', 'parent_text'.
    :param iteration: The iteration number
    :param persona_rules: Dictionary of persona rules with keywords.
    :param use_context: boolean to decide if context should be used or not
    :return: Dictionary of persona matches, split into positive, neutral, negative.
    """
    print("Starting Analyzing....")
    analyzer = SentimentIntensityAnalyzer()
    matched_personas = {
        persona: {
            "positive": [],
            "neutral": [],
            "negative": []
        }
        for persona in persona_rules
    }

    persona_docs = {
        persona: nlp(" ".join(k["term"] for k in rules["keywords"]))
        for persona, rules in persona_rules.items()
    }

    persona_keywords = {
        persona: rules["keywords"]
        for persona, rules in persona_rules.items()
    }

    data = {}
    title = comments.get("title", "")
    for user, user_comments in comments.get("comments", {}).items():
        for comment_id, comment_data in user_comments.items():

            if comment_data is None:
                continue

            if platform == "reddit":
                data = extract_reddit_comments(comment_data, title)

            parent_tokens = []
            if data["parent_text"]:
                parent_tokens = [t.lemma_.lower() for t in nlp(data["parent_text"])]

            for persona in persona_rules:
                match = find_match(data,iteration, parent_tokens, persona_docs[persona], persona_keywords[persona])

                if match:
                    main_compound = analyzer.polarity_scores(data["main_text"])["compound"]
                    context_compound = analyzer.polarity_scores(data["full_text"])["compound"]

                    polarity = main_compound if not use_context else combine_with_context(
                        main_compound,
                        context_compound)
                    sentiment = classify_sentiment(polarity)

                    matched_personas[persona][sentiment].append({
                        "user": user,
                        "comment": data["main_text"],
                        "polarity": polarity,
                        "parent": data["parent_text"],
                        "quotes": data["quotes"]
                    })

    return matched_personas


def find_match(data: dict, iteration:int,parent_tokens: list, persona_docs, keywords) -> bool:
    """Find matching persona for a comment
    :param data: Dictionary of comments, keyed by comment ID
    :param iteration: the iteration number
    :param parent_tokens: List of parent tokens
    :param persona_docs spacy doc
    :param keywords: List of keywords
    :return: Matching persona"""

    iteration_rules = {
        1:{
            "threshold" : 0.2,
            "min_main_sim" : 0.1,
            "require_main_signal": False,
            "parent_weight" : 0.1,
        },
        2: {
            "threshold": 0.3,
            "min_main_sim": 0.2,
            "require_main_signal": True,
            "parent_weight": 0.1,
        },
        3: {
            "threshold": 0.4,
            "min_main_sim": 0.3,
            "require_main_signal": True,
            "parent_weight": 0.05,
        }
    }

    tokens = data["tokens"]

    main_token_set = set(tokens)
    main_text = data["main_text"].lower()
    main_text_padded = f" {main_text} "

    parent_token_set = set(parent_tokens)
    parent_text = data["parent_text"].lower()
    parent_text_padded = f" {parent_text} "

    main_hits = sum(
        kw["weight"]
        for kw in keywords
        if (
            f" {kw['term']} " in main_text_padded
            if " " in kw["term"]
            else kw["term"] in main_token_set
        )
    )

    parent_hits = sum(
        kw["weight"]
        for kw in keywords
        if (
            f" {kw['term']} " in parent_text_padded
            if " " in kw["term"]
            else kw["term"] in parent_token_set
        )
    )

    total_weight = sum(kw["weight"] for kw in keywords)

    keyword_score = 0 if total_weight == 0 else \
        (
            0.9 * (main_hits / max(total_weight, 1)) +
            0.1 * (parent_hits / max(total_weight, 1))
        )

    main_doc = nlp(data["main_text"])
    parent_doc = nlp(data["parent_text"]) if data["parent_text"] else None

    main_sim = main_doc.similarity(persona_docs)
    parent_sim = parent_doc.similarity(persona_docs) if parent_doc else 0

    if iteration_rules[iteration]["require_main_signal"]:
        if main_hits == 0 and main_sim < iteration_rules[iteration]["min_main_sim"]:
            return False

    parent_weight = iteration_rules[iteration]["parent_weight"]\
        if (main_hits > 0 or main_sim > iteration_rules[iteration]["min_main_sim"]) else 0

    sim_score = (1 - parent_weight) * main_sim + parent_weight * parent_sim

    final_score = 0.5 * keyword_score + 0.7 * sim_score if iteration == 1\
        else 0.5 * keyword_score + 0.5 * sim_score

    return final_score > iteration_rules[iteration]["threshold"]


def classify_sentiment(polarity: float, threshold: float = 0.10) -> str:
    """Classify sentiment based on polarity and threshold
    :param polarity: Polarity score
    :param threshold: Threshold for polarity score
    :return: Sentiment label"""
    if abs(polarity) < threshold:
        return "neutral"
    elif polarity > 0:
        return "positive"
    else:
        return "negative"


def extract_reddit_comments(comment_data: dict, title: str) -> dict:
    """extract Reddit comments for persona matches, including parent and quotes
    :param title: Title of the thread
    :param comment_data: Dictionary of cleaned comments, keyed by comment ID.
    :return: Dictionary of persona matches, split into positive, neutral, negative."""
    main_text = comment_data.get('text', '')
    parent_text = comment_data.get('parent_text', '')
    quotes = [q.get('text', '') for q in comment_data.get('quotes', [])]

    context_text = " ".join([title, parent_text] + quotes) if parent_text or quotes else ""

    full_text_for_sentiment = " ".join([main_text, context_text]).strip()

    tokens = [t.lemma_.lower() for t in nlp(main_text)]

    return {
        "main_text": main_text,
        "full_text": full_text_for_sentiment,
        "tokens": tokens,
        "parent_text": parent_text,
        "quotes": quotes
    }


def combine_with_context(main_compound, context_compound, context_weight: float = 0.4) -> int:
    """
    Context adjusts intensity only if context sentiment is strong.
    :param main_compound: Compound score of main text
    :param context_compound: Compound score of context text
    :param context_weight: Weight of parent + quotes in sentiment analysis (0.0 - 1.0)
    :return: Intensity adjusted compound score
    """
    polarity = main_compound

    if abs(context_compound) > 0.2:
        if main_compound * context_compound > 0:
            polarity += context_weight * context_compound
        else:
            polarity -= context_weight * context_compound

    return polarity
