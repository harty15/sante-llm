import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Configure environment
pd.set_option("display.max_rows", 20)
pd.set_option("display.max_columns", 20)

# Environment variables
# Environment setup for LangChain
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2")
LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT")

# Core API keys and configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
TEMPERATURE = float(os.getenv("TEMPERATURE"))

# Vector store configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
EMBED_MODEL = os.getenv("EMBED_MODEL")

# S3 configuration
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET")

# Additional API keys
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Retriever configuration
RETRIEVER_K = int(os.getenv("RETRIEVER_K", "15"))

# Deal Cloud configuration
DEALCLOUD_CLIENT_ID = os.getenv("DEALCLOUD_CLIENT_ID")
DEALCLOUD_CLIENT_SECRET = os.getenv("DEALCLOUD_CLIENT_SECRET")
DEALCLOUD_BASE_URL = os.getenv("DEALCLOUD_BASE_URL")