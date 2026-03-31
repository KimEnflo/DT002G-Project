import hashlib
import spacy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

nlp = spacy.load("en_core_web_lg")


def analyze_comment(comments: dict, persona_rules: dict, platform: str, use_context: bool) -> dict:
    """Analyze Reddit comments for persona matches and sentiment, including parent and quotes
    :param platform: The platform used to fetch the comments
    :param comments: Dictionary of cleaned comments, keyed by comment ID.
                     Each comment should have 'text', 'quotes', 'parent_text'.
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

            for persona, info in persona_rules.items():
                keywords = [k.lower() for k in info["keywords"]]
                main_match = any(k in data["tokens"] for k in keywords)

                fallback_match = False
                if not main_match and len(data["tokens"]) <= 3:
                    fallback_match = any(k in parent_tokens for k in keywords)

                if main_match or fallback_match:
                    main_compound = analyzer.polarity_scores(data["main_text"])["compound"]
                    context_compound = analyzer.polarity_scores(data["full_text"])["compound"]

                    polarity = main_compound if not use_context else combine_with_context(
                        main_compound,
                        context_compound)
                    sentiment = classify_sentiment(polarity)

                    matched_personas[persona][sentiment].append({
                        "user": anonymize_author(user),
                        "comment": data["main_text"],
                        "polarity": polarity,
                        "parent": data["parent_text"],
                        "quotes": data["quotes"]
                    })

    return matched_personas


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


def anonymize_author(author: str) -> str:
    """Anonymize the author name
    :param: author: author name
    :returns: hashed author name"""
    return hashlib.md5(author.encode("utf-8")).hexdigest()
