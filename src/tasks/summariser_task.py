from crewai import Task
from src.agents.summariser_agent import summariser_agent
from datetime import datetime
from config.settings import task_data_path

current_datetime = datetime.now()
year_as_int = current_datetime.year

def get_summarising_task(search_task):

    agent = summariser_agent()

    summarising_task = Task(
        description="""
            Summarize the information that was searched from the internet
            about the music composer, Pritam.
        """,
        expected_output=f"""
            A concise point wise summary of the top search results
            (each point summarises the key information from each source of search result) and
            also mention the source Link for each point. Explicitly highlight the most recent
            information and especially negative publicity and controversy.
        """,
        agent=agent,
        markdown=True,
        output_file=f"{task_data_path}/summariser.md",
        context=[search_task]
    )

    return summarising_task