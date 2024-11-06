from langgraph.graph import START, END, StateGraph, MessagesState
from agents.companies import create_companies_agent
from agents.deals import create_deals_agent
from agents.funding import create_funding_agent
from agents.sante_companies import create_sante_companies_agent
from agents.exits import create_exits_agent
from agents.meetings import create_meetings_agent
from agents.cap_tables import create_cap_tables_agent
from agents.search import create_search_agent
from agents.tavily import create_tavily_agent
from tools.custom_tools import create_custom_tools
from config.settings import OPENAI_API_KEY
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import tools_condition, ToolNode
from typing import Literal

def supervisor(state: MessagesState):
    supervisor_llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=OPENAI_API_KEY)
    supervisor_msg = SystemMessage(content="""You are the supervisor at Sante Ventures.
Your job is to:
1. Understand the user's request about venture capital, healthcare companies, investments, meetings, cap tables, or deals
2. Route the request to the appropriate specialist:
   - Companies Specialist: for general company information
   - Deals Specialist: for deal-related queries
   - Funding Specialist: for deal analysis of companies who have received additional funding by their lead investors
   - Santé Companies Specialist: for companies reviewed by Santé 
   - Exit Specialist: for exit-related information
   - Meetings Specialist: for meeting-related queries
   - Cap Tables Specialist: for cap table, investment, and ownership analysis of Santé portfolio companies
   - Search Specialist: for similarity search across companies
   - Web Research Specialist: for finding recent information using Tavily search
3. Explain which specialist you're routing to and why

When routing, use the exact phrase "Routing to [Specialist Name]" where Specialist Name is one of the above.""")
    response = supervisor_llm.invoke([supervisor_msg] + state["messages"])
    return {"messages": [response]}

def route_to_specialist(state: MessagesState) -> Literal["companies", "deals", "funding", "sante_companies", "exits", "meetings", "cap_tables", "search", "tavily", END]:
    last_message = state["messages"][-1].content
    if "Routing to Companies Specialist" in last_message:
        return "companies"
    elif "Routing to Deals Specialist" in last_message:
        return "deals"
    elif "Routing to Funding Specialist" in last_message:
        return "funding"
    elif "Routing to Santé Companies Specialist" in last_message:
        return "sante_companies"
    elif "Routing to Exit Specialist" in last_message:
        return "exits"
    elif "Routing to Meetings Specialist" in last_message:
        return "meetings"
    elif "Routing to Cap Tables Specialist" in last_message:
        return "cap_tables"
    elif "Routing to Search Specialist" in last_message:
        return "search"
    elif "Routing to Web Research Specialist" in last_message:
        return "tavily"
    return END

def build_graph(dataframes, vectorstore, tools):
    builder = StateGraph(MessagesState)
    builder.add_node("supervisor", supervisor)

    # Add agent nodes
    builder.add_node("companies", create_companies_agent(tools['all_companies_tool'], OPENAI_API_KEY).agent)
    builder.add_node("deals", create_deals_agent(tools['all_deals_tool'], OPENAI_API_KEY).agent)
    builder.add_node("funding", create_funding_agent(tools['funding_deals_tool'], OPENAI_API_KEY).agent)
    builder.add_node("sante_companies", create_sante_companies_agent(tools['sante_companies_tool'], OPENAI_API_KEY).agent)
    builder.add_node("exits", create_exits_agent(tools['exit_deals_tool'], OPENAI_API_KEY).agent)
    builder.add_node("meetings", create_meetings_agent(tools['meetings_tool'], OPENAI_API_KEY).agent)
    builder.add_node("cap_tables", create_cap_tables_agent(tools['cap_tables_tool'], OPENAI_API_KEY).agent)
    builder.add_node("search", create_search_agent(tools['search_companies'], OPENAI_API_KEY).agent)
    builder.add_node("tavily", create_tavily_agent(tools['tavily_search'], OPENAI_API_KEY).agent)

    # Add tool nodes (ensure all are included)
    builder.add_node("all_companies_repl_tools", ToolNode([tools['all_companies_tool']]))
    builder.add_node("all_deals_repl_tools", ToolNode([tools['all_deals_tool']]))
    builder.add_node("funding_deals_repl_tools", ToolNode([tools['funding_deals_tool']]))
    builder.add_node("sante_companies_repl_tools", ToolNode([tools['sante_companies_tool']]))
    builder.add_node("exit_deals_repl_tools", ToolNode([tools['exit_deals_tool']]))
    builder.add_node("meetings_repl_tools", ToolNode([tools['meetings_tool']]))
    builder.add_node("cap_tables_repl_tools", ToolNode([tools['cap_tables_tool']]))
    builder.add_node("search_companies_tools", ToolNode([tools['search_companies']]))
    builder.add_node("tavily_search_tools", ToolNode([tools['tavily_search']]))

    # Add edges
    builder.add_edge(START, "supervisor")
    builder.add_conditional_edges(
        "supervisor",
        route_to_specialist,
        {
            "companies": "companies",
            "deals": "deals",
            "funding": "funding",
            "sante_companies": "sante_companies",
            "exits": "exits",
            "meetings": "meetings",
            "cap_tables": "cap_tables",
            "search": "search",
            "tavily": "tavily",
            END: END
        }
    )

    # Add specialist tool edges
    for specialist, tool_name in [
        ("companies", "all_companies_repl"),
        ("deals", "all_deals_repl"),
        ("funding", "funding_deals_repl"),
        ("sante_companies", "sante_companies_repl"),
        ("exits", "exit_deals_repl"),
        ("meetings", "meetings_repl"),
        ("cap_tables", "cap_tables_repl"),
        ("search", "search_companies"),
        ("tavily", "tavily_search")
    ]:
        builder.add_conditional_edges(
            specialist,
            tools_condition,
            {
                "tools": f"{tool_name}_tools",
                END: END
            }
        )
        builder.add_edge(f"{tool_name}_tools", specialist)

    # Compile graph
    graph = builder.compile()
    return graph 