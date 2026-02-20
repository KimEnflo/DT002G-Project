import time

import httpx

def parse(url):
    """Parse a reddit url and collect the comments
    :param url: the url to be parsed
    :return: list of comments"""
    data = fetch_data(url)
    link_id = data[0]["data"]["children"][0]["data"]["name"]

    return extract_comments(data[1]["data"]["children"], link_id)


def fetch_data(url):
    """Fetch a reddit url and collect the comments"""
    return httpx.get(url).json()


def extract_comments(comment_nodes, link_id, collected=None):
    """Recursively collect all comments, including collapsed 'more' ones
    :param comment_nodes: list of comments
    :param link_id: the reddit link
    :param collected: collected comments
    :return: list of comments"""

    if collected is None:
        collected = []

    for node in comment_nodes:
        kind = node.get("kind")

        if kind == "t1":
            comment_data = node["data"]
            collected.append(comment_data)

            replies = comment_data.get("replies")
            if replies and isinstance(replies, dict):
                extract_comments(replies["data"]["children"], link_id, collected)

        elif kind == "more":
            children_ids = node["data"].get("children", [])
            if children_ids:
                more_nodes = fetch_more_children(link_id, children_ids)
                extract_comments(more_nodes, link_id, collected)

    return collected


def fetch_more_children(link_id, children_ids):
    """Recursively collect all comments, including 'more' ones
    :param link_id: the reddit link
    :param children_ids: list of children ids"""

    # Sleep timer to avoid rate-limiting if you get Status 429 try increasing it.
    time.sleep(1)

    url = "https://www.reddit.com/api/morechildren.json"
    params = {
        "link_id": link_id,
        "children": ",".join(children_ids),
        "api_type": "json"
    }
    try:
        response = httpx.get(
            url,
            params=params,
            timeout=10.0
        )
    except httpx.RequestError as e:
        print("Request failed:", e)
        return []

    try:
        return response.json()["json"]["data"]["things"]
    except Exception as e:
        print("JSON error:", e)
        print(response.text[:500])
        return []
