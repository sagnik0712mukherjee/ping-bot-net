from crewai import Task
from src.agents.search_agent import search_agent
from config.settings import search_keywords, search_domains, task_data_path, top_k
from src.tools.search_tool import web_search
from datetime import datetime

current_datetime = datetime.now()
year_as_int = current_datetime.year

def get_search_task():

    agent = search_agent()

    searching_task = Task(
        description=f"""
            Search the best & latest information available on the internet
            about the music composer, Pritam.
            
            IMPORTANT: You MUST use the web_search tool to search for EACH of these keywords separately:
            {', '.join(search_keywords)}
            
            For each keyword in the list, you MUST call the web_search tool with that keyword as the query parameter.
            Example: Call web_search with query="Pritam", then web_search with query="Pritam Chakraborty", etc.
            
            Explore information from these domains: {', '.join(search_domains)}.
            Only search for and highlight the most recent information and negative publicity/controversy
            from year {year_as_int} and {year_as_int - 1}.
        """,
        expected_output=f"""
            An array of strings with the top {top_k} results from searching each keyword.
        """,
        agent=agent,
        markdown=True,
        output_file=f"{task_data_path}/search.md",
        tools=[web_search]
    )

    return searching_task
