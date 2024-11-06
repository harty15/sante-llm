from data.loaders import load_all_dataframes
from config.settings import (
    S3_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
    OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_INDEX, EMBED_MODEL
)
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone as PineconeClient
from langchain_community.embeddings import OpenAIEmbeddings
from tools.custom_tools import create_custom_tools
from graph.builder import build_graph
from langgraph.graph import MessagesState


# Load data
dataframes = load_all_dataframes(S3_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

# Initialize Pinecone and vector store
pc = PineconeClient(api_key=PINECONE_API_KEY)
pinecone_index = pc.Index(PINECONE_INDEX)
embeddings = OpenAIEmbeddings(model=EMBED_MODEL, api_key=OPENAI_API_KEY)
vectorstore = PineconeVectorStore(index=pinecone_index, embedding=embeddings, text_key="Description")

# Create tools
tools = create_custom_tools(dataframes, vectorstore)

# Build the graph
graph = build_graph(dataframes, vectorstore, tools)
    