from crewai import Task
from src.agents.search_agent import search_agent
from config.settings import search_keywords, search_domains, task_data_path, top_k
from src.tools.multi_search_tool import multi_source_search
from src.tools.article_parser_tool import parse_article_metadata
from datetime import datetime

current_datetime = datetime.now()
year_as_int = current_datetime.year

def get_search_task():

    agent = search_agent()

    searching_task = Task(
        description=f"""
            Search the best & latest information available on the internet
            about the music composer, Pritam from the LAST 96 HOURS ONLY.
            
            IMPORTANT INSTRUCTIONS:
            1. You MUST use the multi_source_search tool to search across multiple sources
            2. Search for EACH of these keywords separately: {', '.join(search_keywords)}
            3. For each keyword, use: multi_source_search(query="keyword", hours_back=96, top_k={top_k})
            4. Extract and prioritize the TOP 10 most recent articles
            5. For each article URL found, use parse_article_metadata() to extract:
               - Publish date and time
               - Article title
               - Content snippet
               - Whether it contains controversy keywords
            6. Focus on recent information from {year_as_int}
            7. ESPECIALLY highlight controversies, allegations, negative publicity, disputes
            
            Return results with full metadata including publish date/time for each article.
        """,
        expected_output=f"""
            A structured list of the top {top_k} most recent articles about Pritam from the last 96 hours.
            For each article include:
            - Title
            - URL
            - Publish Date and Time (formatted as YYYY-MM-DD HH:MM:SS)
            - Source (DuckDuckGo, Bing, Reddit, etc.)
            - Brief snippet
            - Controversy flag (Yes/No)
            - Content preview
        """,
        agent=agent,
        markdown=True,
        output_file=f"{task_data_path}/search.md",
        tools=[multi_source_search, parse_article_metadata]
    )

    return searching_task
