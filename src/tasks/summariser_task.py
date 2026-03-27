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
            about the music composer, Pritam. Even if it does NOT mention him, but one of his songs, then also include that information.
            Basically we need to be alerted about any news related to him, his songs, his albums, his movies, and especially controversies around him
            even if his name is NOT mentioned.
            
            CRITICAL REQUIREMENTS:
            1. **IF NO ARTICLES FOUND**: Return only "NO_ARTICLES_FOUND" (exactly as written)
            2. For each article, include the PUBLISH DATE AND TIME (formatted as YYYY-MM-DD HH:MM:SS)
            3. Organize by recency - latest articles first
            4. Clearly highlight ANY controversies, allegations, or negative publicity found
            5. Include source URL for each point
            6. Mark articles flagged as controversial OR about Pritam's works with a ⚠️ ALERT flag
            7. Keep summaries concise but informative (2-3 lines per article)
            8. The article metadata includes 'is_pritam_work' flag - if True, it means the article is about one of his songs/albums/movies even if his name is not mentioned
        """,
        expected_output=f"""
            Option 1 - If NO articles found:
                NO_ARTICLES_FOUND
            
            Option 2 - If articles exist:
                A well-organized summary with:
                - Each article listed with its publish date/time (YYYY-MM-DD HH:MM:SS)
                - Point-wise summary of key information
                - Source link for each article
                - Clear marking of controversial content with ⚠️ flag
                - Organized from newest to oldest
                - All controversies, allegations highlighted in bold
        """,
        agent=agent,
        markdown=True,
        output_file=f"{task_data_path}/summariser.md",
        context=[search_task]
    )

    return summarising_task