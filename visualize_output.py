from pathlib import Path

import altair as alt

def visualise_output(data:dict):
    """Create and save a heatmap of top persona keywords
    :param data: Dictionary containing
    {data_frame: Dataframe of persona term scores,
    title: The title of the thread,
    iteration: The iteration number,
    top_words:  of top terms per persona}
    :return: Altair chart object"""
    df,title,iteration,top_n = data["data_frame"],data["title"],data["iteration"],data["top_words"]

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
