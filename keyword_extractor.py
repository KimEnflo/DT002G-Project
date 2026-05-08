from pathlib import Path
from typing import Dict

import contractions
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

import persona_parser

JUNK_TERMS = {
    "thank", "thanks", "cool", "nice", "great",
    "awesome", "good", "love", "lol", "yeah",
    "ok", "okay", "sure", "hi", "hey", "really", "look"
}

GENERIC_PHRASES = {
    "really cool", "good idea", "nice work",
}

def extract_persona_keywords(
        data: Dict,
        iteration: int,
        title: str,
        top_n: int = 15,
        alpha: float = 1,
) -> dict:
    """Extract and visualize persona-specific keywords using log-odds weighting
      :param data: The matched personas data
      :param title: title of the post
      :param iteration: The iteration number
      :param top_n: Number of top terms to display per persona
      :param alpha: Smoothing parameter for log-odds
      :return: Altair heatmap chart of persona keyword scores"""

    docs, persona_labels = flatten_data(data)

    vectorizer = CountVectorizer(
        stop_words="english",
        ngram_range=(1, 3),
        min_df=1,
        max_df=0.85,
        token_pattern=r"(?u)\b(?!\d+\b)[a-zA-Z0-9_]+(?:'[a-zA-Z]+)?\b"
    )

    document_term_matrix = vectorizer.fit_transform(docs)

    feature_names = vectorizer.get_feature_names_out()

    persona_scores = compute_persona(document_term_matrix, persona_labels, feature_names, alpha)

    df = pd.DataFrame({k: v.to_dict() for k, v in persona_scores.items()}).T.fillna(0.0)

    presence = (df > 0).sum(axis=0)

    df = df.loc[:, presence < len(df.index)]

    extract_top_keywords(df, iteration, title, top_n=top_n)

    return {"data_frame": df, "title": title, "iteration": iteration, "top_words": top_n}


def flatten_data(data: Dict):
    """Flatten the comment data to make it usable with CountVectorizer
    :param data The matched personas data
    :return: The flattened comments data and labels"""
    docs, persona_labels = [], []

    for persona, sentiments in data.items():
        for comments in sentiments.values():
            for entry in comments:
                text = entry.get("comment", "").strip()
                if text:
                    docs.append(contractions.fix(text))
                    persona_labels.append(persona)
    return docs, persona_labels


def extract_top_keywords(df: pd.DataFrame, iteration: int, title: str, top_n: int = 15):
    """Save the new persona_specification keywords
    :param df Dataframe of persona term scores
    :param title: The title of the post
    :param iteration: The iteration number
    :param top_n:  of top terms to display per persona
    """
    new_keywords = {}

    for persona in df.index:
        top_terms = {
            t: s for t, s in df.loc[persona]
            .sort_values(ascending=False)
            .head(top_n)
            .items()
            if s > 0 and is_informative(t, s)
        }
        if not top_terms:
            continue

        max_score = max(top_terms.values())

        new_keywords[persona] = {
            "keywords": [
                {
                    "term": term,
                    "weight": round(
                        (score / max_score) * (
                            1.2 if term.count(" ") >= 2
                            else 1.0 if term.count(" ") == 1
                            else 0.75
                        ), 4
                    )
                }
                for term, score in top_terms.items()
            ]
        }

    base_path = Path("persona_specifications.json") if iteration == 1 else Path(
        f"resources/persona_specifications/{title}/Iteration {iteration - 1}/persona_specifications.json"
    )

    new_keywords = merge_with_base(new_keywords, base_path)

    persona_parser.save_output(new_keywords, Path(
        f"resources/persona_specifications/{title}/Iteration {iteration}/persona_specifications.json"
    ))


def merge_with_base(new_keywords: dict, base_path: Path) -> dict:
    """ Merge the new rules with the last iteration rules
    :param new_keywords: The newly discovered keywords
    :param base_path: Path to the previous persona_classification
    :return: new dict of keywords for the next iteration
    """
    try:
        base = persona_parser.load_file(base_path)
    except FileNotFoundError:
        return new_keywords

    merged = {}

    for persona, base_data in base.items():
        base_terms = {
            kw["term"]: kw["weight"]
            for kw in base_data.get("keywords", [])
        }

        new_phrases = {
            kw["term"]: kw["weight"]
            for kw in new_keywords.get(persona, {}).get("keywords", [])
            if " " in kw["term"]
               and kw["term"] not in base_terms
        }

        merged[persona] = {
            "keywords": [
                {"term": t, "weight": w}
                for t, w in {**base_terms, **new_phrases}.items()
            ]
        }

    return merged


def is_informative(term: str, score: float) -> bool:
    """ Function to filter out informative terms
    :param term: The term to verify
    :param score: score of the term
    :return: boolean if It's informative or not
    """
    words = term.split()
    if score < 1.5:
        return False
    if term in GENERIC_PHRASES:
        return False
    if any(w in JUNK_TERMS for w in words):
        return False
    return True


def compute_persona(document_term_matrix, labels, feature_names, alpha) -> dict:
    """Compute log-odds scores for each term per persona
    :param document_term_matrix: Document-term matrix
    :param labels: Persona labels for each document
    :param feature_names: Vocabulary terms
    :param alpha: Smoothing parameter
    :return: Dictionary of personas mapped to sorted term scores"""
    dataframe = pd.DataFrame.sparse.from_spmatrix(document_term_matrix, columns=feature_names)
    dataframe["persona"] = labels

    persona_counts = dataframe.groupby("persona").sum()

    background = persona_counts.sum(axis=0)

    results = {}

    for persona in persona_counts.index:
        class_counts = persona_counts.loc[persona]
        other_counts = background - class_counts

        scores = log_odds(class_counts, other_counts, background, alpha)
        results[persona] = scores.sort_values(ascending=False)

    return results


def log_odds(class_counts, other_counts, background, alpha=1):
    """ Monroe-style log-odds
    :param class_counts: Term counts for the target persona
    :param other_counts: Term counts for all other personas
    :param alpha: Smoothing parameter
    :param background: Total number of terms
    :return: Log-odds score per term"""

    eps = 1e-12

    bg = background / background.sum()
    alpha_i = alpha * bg
    alpha0 = alpha_i.sum()

    y1 = class_counts
    y2 = other_counts

    n1 = y1.sum()
    n2 = y2.sum()

    num1 = y1 + alpha_i
    den1 = (n1 - y1) + (alpha0 - alpha_i)

    num2 = y2 + alpha_i
    den2 = (n2 - y2) + (alpha0 - alpha_i)

    num1 = np.maximum(num1, eps)
    num2 = np.maximum(num2, eps)
    den1 = np.maximum(den1, eps)
    den2 = np.maximum(den2, eps)

    log_odds_1 = np.log(num1) - np.log(den1)
    log_odds_2 = np.log(num2) - np.log(den2)

    delta = log_odds_1 - log_odds_2

    variance = (1 / num1) + (1 / num2)

    return pd.Series(delta / np.sqrt(variance), index=class_counts.index)
