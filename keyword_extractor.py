import altair as alt
import numpy as np
import pandas as pd
import contractions
from sklearn.feature_extraction.text import CountVectorizer
from typing import Dict


def extract_persona_keywords(
    data: Dict,
    ngram_range=(1, 2),
    min_df: int = 1,
    top_n: int = 15,
    alpha: float = 1,
):
    """Extract and visualize persona-specific keywords using log-odds weighting
      :param data: The matched personas data
      :param ngram_range: The n-gram range for tokenization
      :param min_df: Minimum document frequency for terms
      :param top_n: Number of top terms to display per persona
      :param alpha: Smoothing parameter for log-odds
      :return: Altair heatmap chart of persona keyword scores"""

    docs, persona_labels = flatten_data(data)

    vectorizer = CountVectorizer(
        stop_words="english",
        ngram_range=ngram_range,
        min_df=min_df,
        token_pattern=r"(?u)\b[a-zA-Z0-9_]+(?:'[a-zA-Z]+)?\b"
    )

    document_term_matrix = vectorizer.fit_transform(docs)

    feature_names = vectorizer.get_feature_names_out()

    persona_scores = compute_persona(document_term_matrix, persona_labels, feature_names, alpha)

    return visualise_output(persona_scores, top_n)


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


def compute_persona(document_term_matrix, labels, feature_names, alpha):
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


def log_odds(class_counts, other_counts,background, alpha =1 ):
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

    variance  = (1 / num1) + (1 / num2)

    return pd.Series(delta / np.sqrt(variance ), index=class_counts.index)


def visualise_output(persona_scores, top_n):
    """Create and save a heatmap of top persona keywords
    :param persona_scores: Dictionary of persona term scores
    :param top_n: Number of top terms per persona
    :return: Altair chart object"""
    df = pd.DataFrame({k: v.to_dict() for k, v in persona_scores.items()}).T.fillna(0.0)

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

    chart.save("persona_heatmap.html")

    return chart