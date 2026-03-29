from crewai import Agent
from config.settings import search_llm_model
from src.tools.multi_search_tool import multi_source_search
from src.tools.article_parser_tool import parse_article_metadata

def search_agent():

    searching_agent = Agent(
        role = "Intelligent Web Search Agent",
        goal = f"Search the best & latest information available on the internet about the music composer, Pritam from the last 201 hours.",
        backstory = "You are a master at performing real time internet search across multiple sources (DuckDuckGo, Bing, Reddit, Filmfare, etc.) to expand the capabilities of the LLM which may not be up to date with recent data. You excel at finding content related to Pritam himself, his famous songs (like Tu Hi Disda), his albums, his movies, and controversies around them - even when his name is not explicitly mentioned. You focus on extracting controversies, allegations, and negative publicity across all these domains.",
        verbose = True,
        llm = search_llm_model,
        tools = [multi_source_search, parse_article_metadata]
    )

    return searching_agent
