import spacy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

nlp = spacy.load("en_core_web_lg")

def analyze_comment(comments: dict, persona_rules: dict,platform : str, context_weight: float = 0.4) -> dict:
    """Analyze Reddit comments for persona matches and sentiment, including parent and quotes
    :param platform: The platform used to fetch the comments
    :param comments: Dictionary of cleaned comments, keyed by comment ID.
                     Each comment should have 'text', 'quotes', 'parent_text'.
    :param persona_rules: Dictionary of persona rules with keywords.
    :param context_weight: Weight of parent + quotes in sentiment analysis (0.0 - 1.0)
    :return: Dictionary of persona matches, split into positive, neutral, negative.
    """
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

    for comment_id, comment_data in comments.items():
        if platform == "reddit":
            data = extract_reddit_comments(comment_data)

        for persona, info in persona_rules.items():

            keywords = [k.lower() for k in info["keywords"]]
            if any(k in data["tokens"] for k in keywords):
                main_compound = analyzer.polarity_scores(data["main_text"])["compound"]

                context_scores = analyzer.polarity_scores(data["full_text"])
                context_compound = context_scores["compound"]
                polarity = combine_with_context(
                    main_compound,
                    context_compound,
                    context_weight
                )

                sentiment = classify_sentiment(polarity)

                matched_personas[persona][sentiment].append({
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

def extract_reddit_comments(comment_data: dict)-> dict:
    """extract Reddit comments for persona matches, including parent and quotes
    :param comment_data: Dictionary of cleaned comments, keyed by comment ID.
    :return: Dictionary of persona matches, split into positive, neutral, negative."""
    main_text = comment_data.get('text', '')
    parent_text = comment_data.get('parent_text', '')
    quotes = [q.get('text', '') for q in comment_data.get('quotes', [])]

    context_text = " ".join([parent_text] + quotes) if parent_text or quotes else ""

    full_text_for_sentiment = " ".join([main_text, context_text]).strip()

    full_tokens = [t.lemma_.lower() for t in nlp(full_text_for_sentiment)]

    return {
        "main_text": main_text,
        "full_text": full_text_for_sentiment,
        "tokens": full_tokens,
        "parent_text": parent_text,
        "quotes": quotes
    }

def combine_with_context(main_compound, context_compound, context_weight)-> int:
    """
    Context adjusts intensity only if context sentiment is strong.
    :param: main_compound: Compound score of main text
    :param: context_compound: Compound score of context text
    :param: context_weight: context weight to apply
    :return: Intensity adjusted compound score
    """

    polarity = main_compound

    if abs(context_compound) > 0.2:
        if main_compound * context_compound > 0:
            polarity += context_weight * context_compound
        else:
            polarity -= context_weight * context_compound

    return polarity