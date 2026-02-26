import time

import httpx

headers = {
    "User-Agent": "redditScaper/0.1 (by u/redditScraper)",
    "Referer": "https://www.reddit.com/"
}

client = httpx.Client(headers=headers)


def parse(url):
    """Parse a reddit url and collect the comments
    :param url: the url to be parsed
    :return: list of comments"""
    data = fetch_data(url + ".json")

    link_id = data[0]["data"]["children"][0]["data"]["name"]
    total_comments = data[0]["data"]["children"][0]["data"]["num_comments"]

    return extract_comments(data[1]["data"]["children"], link_id, total_comments)


def fetch_data(url):
    """Fetch a reddit url and collect the comments"""
    return client.get(url).json()


def extract_comments(comment_nodes, link_id, total_comments, collected=None):
    """Recursively collect all comments, including collapsed 'more' ones
    :param comment_nodes: list of comments
    :param link_id: the reddit link
    :param total_comments: number of comments
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
                extract_comments(replies["data"]["children"], link_id, total_comments, collected)

        elif kind == "more":
            children_ids = node["data"].get("children", [])
            if children_ids:
                more_nodes = fetch_more_children(link_id, total_comments, children_ids)
                extract_comments(more_nodes, link_id, total_comments, collected)

    return collected


def chunked(iterable, size):
    """Creates chunks out of the iterable to loop over"""
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]


def fetch_more_children(link_id, total_comments, children_ids):
    """Recursively collect all comments, including 'more' ones
    :param link_id: the reddit link
    :param children_ids: list of children ids
    :param total_comments: number of comments"""

    scraped_data = []
    # Sleep timer to avoid rate-limiting if you get Status 429 try increasing it.
    sleep_time = 0.2 if total_comments < 1000 else 2
    batch_size = 30 if total_comments < 1000 else 50

    for batch in chunked(children_ids, batch_size):
        time.sleep(sleep_time)

        try:
            response = client.post(
                "https://www.reddit.com/api/morechildren.json",
                data={
                    "link_id": link_id,
                    "children": ",".join(batch),
                    "api_type": "json"
                },
                timeout=10.0
            )
        except httpx.RequestError as e:
            print("Request failed:", e)
            return []

        try:
            payload = response.json()
        except Exception as e:
            print("JSON error:", e)
            print(response.text[:300])
            continue
        scraped_data += payload.get("json", {}).get("data", {}).get("things", [])

    return scraped_data
