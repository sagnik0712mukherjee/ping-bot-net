from crewai import Crew
from src.agents.summariser_agent import summariser_agent
from src.agents.search_agent import search_agent
from src.tasks.search_task import get_search_task
from src.tasks.summariser_task import get_summarising_task

def build_crew():

    searching_agent = search_agent()
    summarizing_agent = summariser_agent()

    search_task = get_search_task()
    summarising_task = get_summarising_task(search_task)

    crew = Crew(
        agents=[searching_agent, summarizing_agent],
        tasks=[search_task, summarising_task],
        verbose=True
    )

    return crew