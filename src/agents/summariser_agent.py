from crewai import Agent
from config.settings import summariser_llm_model

def summariser_agent():

    summarizing_agent = Agent(
        role = "Intelligent Text Summarizer Agent",
        goal = "Summarize the best & latest information fetched from the internet about the music composer, Pritam.",
        backstory = "You are a master at summarizing information to provide concise and relevant insights.",
        verbose = True,
        llm = summariser_llm_model
    )

    return summarizing_agent