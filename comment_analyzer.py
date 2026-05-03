import re

import spacy
from spacy.tokens import Doc
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()
nlp = spacy.load("en_core_web_lg")


def analyze_comment(comments: dict, persona_rules: dict, iteration: int, platform: str, use_context: bool) -> dict:
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

            documents = (nlp(data["main_text"]), nlp(data["full_context"]) if data["full_context"] else None)

            main_doc_processed = process_text(documents[0])
            context_doc_processed = process_text(documents[1]) if documents[1] else ("", set())

            scores = []

            for persona in persona_rules:
                match_score = find_match_score(iteration,
                                               persona_docs[persona],
                                               persona_keywords[persona],
                                               documents,
                                               main_doc_processed,
                                               context_doc_processed)
                if match_score > 0:
                    scores.append((persona, match_score))

            if not scores:
                continue

            scores.sort(key=lambda x: x[1], reverse=True)

            best_persona, best_score = scores[0]

            if best_persona:
                polarity = calculate_sentiment_score(documents[0].text, documents[1].text, use_context)
                sentiment = classify_sentiment_label(polarity)

                matched_personas[best_persona][sentiment].append({
                    "user": user,
                    "comment": data["main_text"],
                    "polarity": polarity,
                    "parent": data["parent_text"],
                    "quotes": data["quotes"]
                })

    return matched_personas


def find_match_score(iteration: int,
                     persona_docs,
                     keywords: list,
                     documents: tuple[Doc, Doc],
                     processed_main_doc: tuple[str, set],
                     processed_context_doc: tuple[str, set]) -> float:
    """Find matching persona for a comment
    :param iteration: Iteration number
    :param persona_docs List of spacy Doc objects
    :param keywords: List of keywords
    :param documents: the unprocessed spacy documents (main,context)
    :param processed_main_doc: Tuple containing (text,tokens) from the main document
    :param processed_context_doc: Tuple containing (text,tokens) from the context document
    :return: Matching persona"""

    iteration_rules = {
        1: {
            "threshold": 0.2,
            "min_main_sim": 0.1,
            "require_main_signal": False,
            "context_weight": 0.1,
        },
        2: {
            "threshold": 0.3,
            "min_main_sim": 0.2,
            "require_main_signal": True,
            "context_weight": 0.1,
        },
        3: {
            "threshold": 0.4,
            "min_main_sim": 0.4,
            "require_main_signal": True,
            "context_weight": 0.05,
        }
    }

    main_hits = find_keyword_hits(keywords, *processed_main_doc)
    context_hits = find_keyword_hits(keywords, *processed_context_doc)

    total_weight = sum(kw["weight"] for kw in keywords)

    keyword_score = 0 if total_weight == 0 else \
        (
                0.9 * (main_hits / total_weight) +
                0.1 * (context_hits / total_weight)
        )

    main_sim = documents[0].similarity(persona_docs)
    context_sim = documents[1].similarity(persona_docs) if processed_context_doc else 0

    if iteration_rules[iteration]["require_main_signal"]:
        if main_hits == 0 and main_sim < iteration_rules[iteration]["min_main_sim"]:
            return 0

    context_weight = iteration_rules[iteration]["context_weight"] \
        if (main_hits > 0 or main_sim > iteration_rules[iteration]["min_main_sim"]) else 0

    sim_score = (1 - context_weight) * main_sim + context_weight * context_sim

    final_score = 0.5 * keyword_score + 0.7 * sim_score if iteration == 1 \
        else 0.5 * keyword_score + 0.5 * sim_score

    return final_score if final_score > iteration_rules[iteration]["threshold"] else 0


def process_text(doc: Doc) -> tuple[str, set]:
    """process the text  by padding it to prevent partial mismatches
    :param doc: Spacy Doc
    :return: tuple of padded text and tokens created from the comment
    """
    tokens = {t.lemma_.lower() for t in doc}
    text = doc.text.lower()
    return text, tokens


def find_keyword_hits(keywords: list, text: str, token_set: set) -> float:
    """Searches for keyword hits within the comment message and calculates score
    :param keywords: The keyword list used for the search
    :param text: The comment text
    :param token_set: Token set based on the comment
    :return: Score of keyword hits within the message
    """
    score = 0.0

    for kw in keywords:
        term = kw["term"]
        weight = kw["weight"]

        is_phrase = " " in term

        match = (
            phrase_in_text(term, text)
            if is_phrase
            else term in token_set
        )

        if match:
            score += weight if is_phrase else weight * 0.2

    return score


def phrase_in_text(term, text) -> bool:
    """
    :param term: The keyword term to search for
    :param text: The full comment text being searched
    :return: True if the term exist as a whole word
    """
    pattern = rf"\b{re.escape(term)}\b"
    return re.search(pattern, text) is not None


def calculate_sentiment_score(main_text, context_text, use_context: bool) -> float:
    """Calculates sentiment score for the persona
    :param main_text : main comment text
    :param context_text : quotation,title and parent context
    :param use_context: use context or not
    :return sentiment score"""
    main_compound = analyzer.polarity_scores(main_text)["compound"]
    context_compound = analyzer.polarity_scores(context_text)["compound"]

    return main_compound if not use_context else combine_with_context(
        main_compound,
        context_compound)


def classify_sentiment_label(polarity: float, threshold: float = 0.10) -> str:
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
    :param comment_data: Dictionary of cleaned comments, keyed by comment ID.
    :param title: Title of the thread
    :return: Dictionary containing main comment text and context text."""
    main_text = comment_data.get('text', '')
    parent_text = comment_data.get('parent_text', '')
    quotes = [q.get('text', '') for q in comment_data.get('quotes', [])]

    context_text = " ".join([title, parent_text] + quotes) if parent_text or quotes else ""

    full_text_for_sentiment = " ".join([main_text, context_text]).strip()

    return {
        "main_text": main_text,
        "full_context": full_text_for_sentiment,
        "parent_text": parent_text,
        "quotes": quotes
    }


def combine_with_context(main_compound, context_compound, context_weight: float = 0.4) -> float:
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
