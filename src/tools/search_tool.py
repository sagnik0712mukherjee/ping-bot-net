from langchain_community.tools import DuckDuckGoSearchRun
from crewai.tools import tool

@tool("DuckDuckGoSearch")
def web_search(query):
    """
    The function is used to perform real time web-search on the internet.

    Args:
        query (str): the user Query for search

    Return:
        Search results in array of strings.
    """

    try:
        results = DuckDuckGoSearchRun().run(query)
        return results
    except Exception as e:
        return f"[Search Error] Failed to search for '{query}'. Error: {str(e)}"
