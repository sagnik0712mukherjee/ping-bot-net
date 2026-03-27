# Imports
import os
from langchain_openai import ChatOpenAI

# API Keys
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# LLM Models
search_llm_model = ChatOpenAI(model="gpt-4o-mini", api_key=openai_api_key)
summariser_llm_model = ChatOpenAI(model="gpt-4o-mini", api_key=openai_api_key)

# Search Keywords
search_keywords = [
    # "Pritam",
    # "Pritam Chakraborty",
    # "Pritam Music",
    # "Pritam Songs",
    "Pritam Albums",
    "Pritam Movies",
    "Pritam Controversies"
]

# Search Domains
search_domains = [
    "https://www.bombaytimes.com/",
    # "https://www.imdb.com/",
    "https://www.zoomtventertainment.com/",
    "https://www.filmfare.com/"
]

# Search top k results
top_k = 5

# Path for all MD files related to the task
task_data_path = "data"

# Ensure data directory exists
os.makedirs(task_data_path, exist_ok=True)