import altair as alt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from typing import Dict


def extract_persona_keywords(
    data: Dict,
    ngram_range=(1, 2),
    min_df: int = 2,
    top_n: int = 15,
    alpha: float = 1,
):
    docs, persona_labels = flatten_data(data)

    vectorizer = CountVectorizer(
        stop_words="english",
        ngram_range=ngram_range,
        min_df=min_df
    )

    x = vectorizer.fit_transform(docs)
    feature_names = vectorizer.get_feature_names_out()

    df_counts = np.asarray((x > 0).sum(axis=0)).ravel()

    num_docs = x.shape[0]

    idf = np.log((num_docs + 1) / (df_counts + 1)) + 1

    x = x.multiply(idf)

    persona_scores = compute_persona(x, persona_labels, feature_names, alpha)

    return visualise_output(persona_scores, top_n)


def flatten_data(data: Dict):
    """Flatten the comment data to make it usable with CountVectorizer
    :param data The matched personas data
    :return: The flattened comments data and labels"""
    docs, persona_labels = [], []

    for persona, sentiments in data.items():
        for _, comments in sentiments.items():
            for entry in comments:
                docs.append(entry["comment"])
                persona_labels.append(persona)

    return docs, persona_labels


def compute_persona(x, labels, feature_names, alpha):
    df = pd.DataFrame.sparse.from_spmatrix(x, columns=feature_names)
    df["persona"] = labels

    persona_counts = df.groupby("persona").sum()
    results = {}

    for persona in persona_counts.index:
        class_counts = persona_counts.loc[persona]
        other_counts = persona_counts.drop(persona).sum()

        scores = log_odds(class_counts, other_counts, alpha, len(feature_names))
        results[persona] = scores.sort_values(ascending=False)

    return results


def log_odds(class_counts, other_counts, alpha, vocab_size):
    class_total = class_counts.sum()
    other_total = other_counts.sum()

    p_class = (class_counts + alpha) / (class_total + alpha * vocab_size)
    p_other = (other_counts + alpha) / (other_total + alpha * vocab_size)

    return np.log(p_class / p_other)


def visualise_output(persona_scores, top_n):
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
        x=alt.X("term:N", sort=None),
        y="persona:N",
        color="score:Q"
    ).properties(width=900, height=400)

    chart.save("persona_heatmap.html")

    return chart