from pathlib import Path
from typing import Dict

import altair as alt
import contractions
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

import persona_parser

def extract_persona_keywords(
        data: Dict,
        iteration: int,
        title: str,
        top_n: int = 15,
        alpha: float = 1,
):
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
        ngram_range= (1, 3),
        min_df= 2,
        max_df=0.8,
        token_pattern=r"(?u)\b(?!\d+\b)[a-zA-Z0-9_]+(?:'[a-zA-Z]+)?\b"
    )

    document_term_matrix = vectorizer.fit_transform(docs)

    feature_names = vectorizer.get_feature_names_out()

    persona_scores = compute_persona(document_term_matrix, persona_labels, feature_names, alpha)

    df = pd.DataFrame({k: v.to_dict() for k, v in persona_scores.items()}).T.fillna(0.0)

    presence = (df > 0).sum(axis=0)

    df = df.loc[:, presence < len(df.index)]

    extract_top_keywords(df, iteration, title, top_n=top_n)

    return visualise_output(df, title, iteration, top_n)


def flatten_data(data: Dict):
    """Flatten the comment data to make it usable with CountVectorizer
    :param data The matched personas data
    :return: The flattened comments data and labels"""
    docs, persona_labels = [], []

    for persona, sentiments in data.items():
        for _, comments in sentiments.items():
            for entry in comments:
                docs.append(contractions.fix(entry["comment"]))
                persona_labels.append(persona)

    return docs, persona_labels


def extract_top_keywords(df: pd.DataFrame, iteration, title, top_n=15):
    """Save the new persona_specification keywords
    :param df Dataframe of persona term scores
    :param title: The title of the post
    :param iteration: The iteration number
    :param top_n:  of top terms to display per persona
    """

    junk_terms = {
        "thank", "thanks", "cool", "nice", "great",
        "awesome", "good", "love", "lol", "yeah",
        "ok", "okay", "sure", "hi", "hey"
    }

    new_keywords = {}

    for persona in df.index:
        filtered = df.loc[persona]
        top_terms = filtered.sort_values(ascending=False).head(top_n)
        top_terms = dict(top_terms)

        total = sum(max(s, 0) for s in top_terms.values())

        new_keywords[persona] = {
            "keywords": [
                {
                    "term": term,
                    "weight": (
                            max(score, 0) / total
                            * (1.3 if term.count(" ") >= 3 else 0.6)
                    )
                }
                for term, score in top_terms.items()
                if score > 0 and term not in junk_terms
            ]
        }
    persona_parser.save_output(new_keywords, Path(
        f"resources/persona_specifications/"
        f"{title}/"
        f"Iteration {iteration}/persona_specifications.json"))


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


def visualise_output(df, title, iteration, top_n):
    """Create and save a heatmap of top persona keywords
    :param df: Dataframe of persona term scores
    :param title: The title of the thread
    :param iteration: The iteration number
    :param top_n:  of top terms per persona
    :return: Altair chart object"""

    persona_top_words = {}

    for persona in df.index:
        top_terms = df.loc[persona].sort_values(ascending=False).head(top_n)
        persona_top_words[persona] = set(top_terms.index)

    all_top_words = sorted(set.union(*persona_top_words.values()))
    df = df[all_top_words]

    global_order = df.mean(axis=0).sort_values(ascending=False).index
    df = df[global_order]

    long_df = df.reset_index().melt(
        id_vars="index",
        var_name="term",
        value_name="score"
    ).rename(columns={"index": "persona"})

    chart = alt.Chart(long_df).mark_rect().encode(
        x="persona:N",
        y=alt.Y("term:N", sort=None),
        color="score:Q"
    ).properties(width=400, height=900)
    chart.save(Path(
        f"resources/heatmaps/"
        f"{title}/"
        f"Iteration {iteration}/persona_heatmap.html"))

    return chart
