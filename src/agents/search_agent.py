from crewai import Agent
from config.settings import search_llm_model
from src.tools.search_tool import web_search

def search_agent():

    searching_agent = Agent(
        role = "Intelligent Web Search Agent",
        goal = f"Search the best & latest information available on the internet about the music composer, Pritam.",
        backstory = "You are a master at performing real time internet search to expand the capabilities of the LLM which may not be up to date with recent data.",
        verbose = True,
        llm = search_llm_model,
        tools = [web_search]
    )

    return searching_agent
