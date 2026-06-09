import re
from difflib import SequenceMatcher

import spacy
from spacy.tokens import Doc
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()
nlp = spacy.load("en_core_web_lg")

ACK_WORDS = {"ok", "okay", "thanks", "thank", "cool", "nice", "got", "got it", "sure", "yep", "yup"}

ITERATION_RULES = {
    1: {"threshold": 0.25, "kw_w": 0.60, "beh_w": 0.40},
    2: {"threshold": 0.28, "kw_w": 0.60, "beh_w": 0.40},
    3: {"threshold": 0.32, "kw_w": 0.55, "beh_w": 0.45},
}

PARENT_REPLY_WEIGHTS = {
    "Question asker": {
        "Solution Provider": 0.08,
        "Technical explainer": 0.05,
        "Critic": 0.04,
        "Question asker": 0.01,
    },
    "Solution Provider": {
        "Question asker": 0.05,
        "Technical explainer": 0.04,
        "Critic": 0.03,
        "Solution Provider": 0.01,
    },
    "Critic": {
        "Solution Provider": 0.06,
        "Critic": 0.05,
        "Technical explainer": 0.04,
        "Question asker": 0.01,
    },
    "Technical explainer": {
        "Question asker": 0.04,
        "Technical explainer": 0.04,
        "Solution Provider": 0.01,
        "Critic": 0.03,
    },
}


def analyze_comment(comments: dict, persona_rules: dict, iteration: int, platform: str, use_context: bool) -> dict:
    """Analyze Reddit comments for persona matches and sentiment, including parent and quotes.
    :param comments: Dictionary of cleaned comments, keyed by comment ID.
                     Each comment should have 'text', 'quotes', 'parent_text'.
    :param persona_rules: Dictionary of persona rules with keywords.
    :param iteration: The iteration number
    :param platform: The platform used to fetch the comments
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

            if not data["main_text"].strip():
                continue

            main_doc = nlp(data["main_text"])
            ctx_doc = nlp(data["full_context"]) if use_context and data["full_context"] else None
            parent_doc = nlp(data["parent_text"]) if use_context and data["parent_text"] else None

            main_proc = process_text(main_doc)
            if filter_messages(main_proc[1], main_proc[0], data["parent_text"]):
                continue

            scores = []

            for persona in persona_rules:
                score, kw_hits = find_match_score(
                    iteration,
                    persona_keywords[persona],
                    main_proc,
                    persona,
                )
                if score > 0:
                    scores.append((persona, score, kw_hits))
            parent_persona, parent_score = None, 0.0
            if use_context:
                parent_persona, parent_score = classify_parent_persona(
                    parent_doc, persona_docs, persona_keywords, iteration
                )
                scores = apply_parent_nudge(scores, parent_persona, list(persona_rules.keys()))

            if ctx_doc:
                scores = apply_context_score(
                    scores,
                    ctx_doc,
                    persona_keywords
                )

            if not scores:
                continue

            best_persona = pick_best_persona(scores)

            if best_persona:
                sentiment = calculate_sentiment_score(
                    main_doc.text,
                    ctx_doc.text if ctx_doc else "",
                    use_context,
                )

                matched_personas[best_persona][sentiment[0]].append({
                    "user": user,
                    "message_id": comment_id,
                    "comment": data["main_text"],
                    "polarity": sentiment[1],
                    "parent": data["parent_text"],
                    "parent_persona": parent_persona if use_context else None,
                    "parent_persona_score": parent_score if use_context else 0.0,
                    "quotes": data["quotes"],
                    "score": [(p, s) for p, s, _ in scores]
                })

    return matched_personas


def pick_best_persona(scores: list) -> str | None:
    """Pick the best persona from scored candidates skipping close ties to prevent misclassification
    :param scores: List of scores
    :return The best fitting persona or None"""
    if not scores:
        return None
    scores.sort(key=lambda x: x[1], reverse=True)

    if len(scores) == 1:
        return scores[0][0]

    top_persona, top_score, top_kw = scores[0]
    second_persona, second_score, second_kw = scores[1]
    gap = top_score - second_score

    if gap >= 0.05:
        return top_persona

    kw_gap = top_kw - second_kw
    if abs(kw_gap) < 0.01:
        return None

    return top_persona if kw_gap >= 0 else second_persona


def find_match_score(iteration: int,
                     keywords: list,
                     processed_main: tuple[str, set],
                     persona: str) -> float | tuple[float, float]:
    """Find matching persona for a comment
    :param iteration: Iteration number
    :param keywords: List of keywords
    :param processed_main: Tuple containing (text,tokens) from the main document
    :param persona: Current persona being tried
    :return: Float of 0.0 if no matching or Tuple containing (score, kw_hits)"""
    rules = ITERATION_RULES[iteration]
    return compute_persona_score(
        keywords,
        processed_main,
        kw_w=rules["kw_w"],
        beh_w=rules["beh_w"],
        persona=persona,
    )


def compute_persona_score(
        keywords: list,
        processed_main: tuple[str, set],
        kw_w: float,
        beh_w: float,
        persona: str,
) -> float | tuple[float, float]:
    """Core persona scoring.
    :param keywords: Persona keyword list with weights
    :param processed_main: (text, tokens) for the main comment
    :param kw_w: Weight for keyword score for this iteration
    :param beh_w: Weight for behavioral intent for this iteration
    :param persona: Persona name
    :return: Float of 0.0 if no matching or Tuple containing (score, kw_hits)
    """
    total_weight = sum(kw["weight"] for kw in keywords)
    if total_weight == 0:
        return 0.0

    main_hits = find_keyword_hits(keywords, *processed_main)

    kw_main_ratio = min(main_hits / total_weight, 1.0)
    keyword_score = 0.85 * kw_main_ratio

    beh = behavior_score(intent(processed_main[0]), persona)

    return kw_w * keyword_score + beh_w * beh, main_hits

def apply_context_score(
        scores: list,
        ctx_doc: Doc,
        persona_keywords: dict
) -> list:
    """Apply additional context-based reinforcement to persona scores.
    :param scores: List of scores
    :param ctx_doc: Document context
    :param persona_keywords: Keywords of the persona
    :return: Updated list of (persona, score, kw_hits)"""

    updated = []

    for persona, score, kw_hits in scores:
        ctx_score = compute_context_score(
            persona_keywords[persona],
            ctx_doc
        )

        updated.append(
            (persona, score + ctx_score, kw_hits)
        )

    return updated

def compute_context_score(keywords: list,ctx:Doc)-> float:
    """ Calculate the score for the context
    :param keywords: Keywords of the persona
    :param ctx: Document context
    :return score: Score of the context"""
    total_weight = sum(kw["weight"] for kw in keywords)
    if total_weight == 0:
        return 0.0
    processed_ctx = process_text(ctx)
    main_hits = find_keyword_hits(keywords, *processed_ctx)

    kw_main_ratio = min(main_hits / total_weight, 1.0)
    keyword_score = 0.45 * kw_main_ratio

    return min(keyword_score, 0.12)

def find_keyword_hits(keywords: list, text: str, token_set: set) -> float:
    """Search for keyword hits against the comment text and token set and scores it accordingly
    :param keywords: Keywords of the persona
    :param text: The comment text
    :param token_set: set of tokens from the comment
    :return: float score of the number of hits for the comment against the persona keywords
    """
    score = 0.0
    for kw in keywords:
        term, weight = kw["term"], kw["weight"]
        if " " in term:
            if phrase_in_text(term, text):
                score += weight
        elif term in token_set:
            score += weight * 0.9
        elif any(similar(token, term) > 0.82 for token in token_set if len(token) > 2):
            score += weight * 0.1
    return score


def behavior_score(intent_feature: dict, persona: str) -> float:
    """ Behavioral score to boost persona detection if intent signal and persona match
    :param intent_feature: The intent signal
    :param persona: The current persona being matched
    :return: float of added score to the persona classification
    """
    p = persona.lower()
    score = 0.0
    if p == "question asker" and intent_feature["is_question"]:
        score += 0.8
    if p == "solution provider" and intent_feature["is_advice"]:
        score += 0.8
    if p == "critic" and intent_feature["is_criticisms"]:
        score += 0.8
    if p == "technical explainer" and intent_feature["is_explanation"]:
        score += 0.8
    return min(score, 1.0)


def intent(text: str) -> dict:
    """Extract intent signal from text
    :param text: the comment text
    :return: boolean if any terms exist in the comment
    """
    t = text.lower()
    return {
        "is_question": bool(re.search(
            r"\?|"
            r"\bhow (do|can|does|did|would|should)\b|"
            r"\bwhat (is|are|was|were|do|does|did|would|should|can)\b|"
            r"\bwhy (is|are|was|did|do|does|would|can)\b|"
            r"\bis (there|this|that|it)\b|"
            r"\bdoes (this|it|anyone|that)\b|"
            r"\bcan (you|i|someone|anyone|it)\b|"
            r"\banyone (know|have|tried|used)\b|"
            r"\bany idea\b|"
            r"\bnot getting\b|"
            r"\bexpected\b", t
        )),
        "is_advice": bool(re.search(
            r"\bshould\b|try\b|recommend\b|suggest\b|consider\b|"
            r"you can\b|you could\b|you might\b|use\b.{0,15}\binstead\b|"
            r"here'?s (how|what|a)\b|the (fix|solution|answer) is\b|"
            r"worked for me\b|fixed (it|this)\b", t
        )),
        "is_criticisms": bool(re.search(
            r"\bbad\b|wrong\b|issue\b|broken\b|doesn.?t work\b|not working\b|"
            r"scam\b|fraud\b|terrible\b|awful\b|hate\b|useless\b|"
            r"fails?\b|bug\b|worst\b|misleading\b|incorrect\b|"
            r"\bnot correct\b|\bnot right\b|\bnot working\b|\bnot happy\b"
            r"(never|still) (works?|arrived?|received?)\b|"
            r"disappoint|frustrating|ridiculous\b|waste\b", t
        )),
        "is_explanation": bool(re.search(
            r"\bthe reason\b|this is because\b|which means\b|"
            r"\bessentially\b|\bspecifically\b|\btechnically\b|"
            r"\bmeaning\b|\bworks by\b|limited to\b|regardless of\b|"
            r"\bdepending on\b|\bunlike\b|the difference\b|"
            r"\bin other words\b|\bto clarify\b|\bbasically\b|"
            r"this means\b|what this does\b|"
            r"done by\b|processed by\b|handled by\b|"
            r"not much different\b|similar to\b|works like\b|"
            r"all of the\b|in terms of\b", t
        )),
    }


def classify_parent_persona(parent_doc: Doc | None,
                            persona_docs: dict,
                            persona_keywords: dict,
                            iteration: int) -> tuple[None, float] | tuple[float, float]:
    """Classify the parent comment's persona using the same scoring logic as main comments.
    :param parent_doc: Parent comment or None
    :param persona_docs: dictionary of all personas
    :param persona_keywords: persona keywords
    :param iteration: Iteration of the classification
    :return: tuple of persona and score or tuple of None and score"""
    if parent_doc is None:
        return None, 0.0
    rules = ITERATION_RULES[iteration]
    parent_proc = process_text(parent_doc)
    best_persona, best_score = None, 0.0

    for persona, p_doc in persona_docs.items():
        score, kw_hits = compute_persona_score(
            persona_keywords[persona],
            parent_proc,
            kw_w=rules["kw_w"],
            beh_w=rules["beh_w"],
            persona=persona,
        )
        if score > best_score:
            best_score = score
            best_persona = persona

    return (best_persona if best_score >= 0.15 else None), best_score


def apply_parent_nudge(scores: list, parent_persona: str | None, all_personas: list) -> list:
    """Nudge persona scores based on the parent comment's persona.
    :param scores: list of scores to apply the nudge
    :param parent_persona: parent comment's persona or None
    :param all_personas: list of all personas
    :return: list of the updated score"""
    if parent_persona is None or parent_persona not in PARENT_REPLY_WEIGHTS:
        return scores

    nudges = PARENT_REPLY_WEIGHTS[parent_persona]
    score_dict = {persona: (score, kw) for persona, score, kw in scores}

    return [
        (persona, score_dict.get(persona, (0.0, 0.0))[0] + nudges.get(persona, 0.0),
         score_dict.get(persona, (0.0, 0.0))[1])
        for persona in all_personas
    ]

def calculate_sentiment_score(main_text: str, context_text: str, use_context: bool) -> tuple[str, float]:
    """Calculates sentiment score for the persona
    :param main_text : main comment text
    :param context_text : quotation,title and parent context
    :param use_context: use context or not
    :return tuple of label and score"""
    main_compound = analyzer.polarity_scores(main_text)["compound"]
    context_compound = analyzer.polarity_scores(context_text)["compound"]
    sentiment = main_compound if not use_context else combine_with_context(
        main_compound,
        context_compound)
    return classify_sentiment_label(sentiment), sentiment


def classify_sentiment_label(polarity: float, threshold: float = 0.10) -> str:
    """Classify sentiment based on polarity and threshold
    :param polarity: Polarity score
    :param threshold: Threshold for polarity score
    :return: Sentiment label"""
    if abs(polarity) < threshold:
        return "neutral"
    return "positive" if polarity > 0 else "negative"


def combine_with_context(main_compound: float, context_compound: float, context_weight: float = 0.4) -> float:
    """ Adjust main sentiment intensity using context, only when both signals are strong.
    Reinforce if same directs or dampen if opposite and no adjustment if either are weak.
    :param main_compound: Compound score of main text
    :param context_compound: Compound score of context text
    :param context_weight: Weight for context adjustment
    :return: Intensity adjusted compound score """

    weak_main = abs(main_compound) < 0.1
    weak_context = abs(context_compound) <= 0.2

    if weak_main or weak_context:
        return main_compound

    same_direction = main_compound * context_compound > 0
    adjustment = context_weight * (context_compound if same_direction else -abs(context_compound))
    return main_compound + adjustment


def extract_reddit_comments(comment_data: dict, title: str) -> dict:
    """extract Reddit comments for persona matches, including parent and quotes
    :param comment_data: Dictionary of cleaned comments, keyed by comment ID.
    :param title: Title of the thread
    :return: Dictionary containing main comment text and context text."""
    main_text = comment_data.get('text', '')
    parent_text = comment_data.get('parent_text', '')
    quotes = [q.get('text', '') for q in comment_data.get('quotes', [])]

    context_text = " ".join([title] + quotes) if parent_text or quotes else ""

    return {
        "main_text": main_text,
        "full_context": context_text,
        "parent_text": parent_text,
        "quotes": quotes
    }


def filter_messages(tokens: set, main_text: str, parent_text: str) -> bool:
    """Filter out low signal comments that are too short or purely acknowledgement noise
    :param tokens: tokens existing in the comment
    :param main_text: the main comment text
    :param parent_text: parent text
    :return: boolean if it should be skipped or not
    """
    meaningful = tokens - ACK_WORDS
    words = main_text.split()
    if parent_text is not None:
        words += parent_text.split()

    return len(meaningful) < 3 or len(words) < 6


def process_text(doc: Doc) -> tuple[str, set]:
    """process the text  by lemmatization and setting it to lowercase
    :param doc: Spacy Doc
    :return: tuple of text and tokens created from the comment
    """
    tokens = {t.lemma_.lower() for t in doc}
    text = doc.text.lower()
    return text, tokens


def similar(a: str, b: str) -> float:
    """Check similarity ratio between two strings
    :param a: First string
    :param b: Second string
    :return: Similarity ratio"""
    return SequenceMatcher(None, a, b).ratio()


def phrase_in_text(term: str, text: str) -> bool:
    """ Check for if term exist as a whole word in the text
    :param term: The keyword term to search for
    :param text: The full comment text being searched
    :return: boolean if term exists as a whole word
    """
    pattern = rf"\b{re.escape(term)}\b"
    return re.search(pattern, text) is not None
