from langchain_experimental.tools import PythonAstREPLTool
from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain_community.tools.tavily_search import TavilySearchResults

# Schema for Python inputs
class PythonInputs(BaseModel):
    query: str = Field(description="code snippet to run")

# Define your specialized tools here
def create_custom_tools(dataframes, vectorstore):
    all_companies_tool = PythonAstREPLTool(
        locals={"all_companies": dataframes['all_companies']},
        name="all_companies_repl",
        description="Access to all healthcare companies across all verticals",
        args_schema=PythonInputs,
    )

    all_deals_tool = PythonAstREPLTool(
        locals={"all_deals": dataframes['all_deals']},
        name="all_deals_repl",
        description="Access to all healthcare deals across all verticals",
        args_schema=PythonInputs,
    )

    funding_deals_tool = PythonAstREPLTool(
        locals={"sante_seen_additional_funding_deals": dataframes['sante_seen_additional_funding_deals']},
        name="funding_deals_repl",
        description="Access to additional funding deals seen by Santé",
        args_schema=PythonInputs,
    )

    sante_companies_tool = PythonAstREPLTool(
        locals={"sante_seen_all_companies": dataframes['sante_seen_all_companies']},
        name="sante_companies_repl",
        description="Access to all companies reviewed by Santé",
        args_schema=PythonInputs,
    )

    exit_deals_tool = PythonAstREPLTool(
        locals={"sante_seen_exit_deals": dataframes['sante_seen_exit_deals']},
        name="exit_deals_repl",
        description="Access to exit deals seen by Santé",
        args_schema=PythonInputs,
    )

    meetings_tool = PythonAstREPLTool(
        locals={"meetings_df": dataframes['meetings_df']},
        name="meetings_repl",
        description="Access to Santé meetings data (MAM, board meetings, LP meetings)",
        args_schema=PythonInputs,
    )

    cap_tables_tool = PythonAstREPLTool(
        locals={"cap_tables": dataframes['cap_tables_df']},
        name="cap_tables_repl",
        description="Access to Santé portfolio company cap tables",
        args_schema=PythonInputs,
    )

    # Tavily Search Tool
    tavily_search = TavilySearchResults(max_results=3)

    # Search Companies Tool
    @tool
    def search_companies(query: str) -> str:
        """Search for relevant companies in the vector database"""
        return vectorstore.as_retriever(search_kwargs={"k": 15}).invoke(query)

    return {
        'all_companies_tool': all_companies_tool,
        'all_deals_tool': all_deals_tool,
        'funding_deals_tool': funding_deals_tool,
        'sante_companies_tool': sante_companies_tool,
        'exit_deals_tool': exit_deals_tool,
        'meetings_tool': meetings_tool,
        'cap_tables_tool': cap_tables_tool,
        'tavily_search': tavily_search,
        'search_companies': search_companies,
    } 