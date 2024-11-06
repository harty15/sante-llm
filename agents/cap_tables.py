from .base import BaseAgent
from langgraph.graph import MessagesState

class CapTablesAgent(BaseAgent):
    def agent(self, state: MessagesState):
        response = self.llm.invoke([self.sys_msg] + state["messages"])
        return {"messages": [response]}

def create_cap_tables_agent(tool, openai_api_key):
    # sample_data = tool.locals['cap_tables'].head(3).to_string()
    companies = tool.locals['cap_tables']['Company'].value_counts()

    sys_msg_content = f"""You are the Cap Tables Specialist at Santé Ventures, focused on analyzing ownership, investments, and capitalization data.

Available Companies:
{companies}

When asked about a company, make sure to reference the available companies.
Key columns include:
- Company
- URL
- Markdown Content (contains detailed cap table information)

Example queries you can handle:
1. cap_tables[cap_tables['Company'] == 'Specific Company']['Markdown Content'].iloc[0]
1a. cap_tables[cap_tables['Company'].str.contains('Specific Company', na=False)]['Markdown Content'].iloc[0]
2. cap_tables[cap_tables['Markdown Content'].str.contains('Series A', na=False)].iloc[0]
3. len(cap_tables['Company'].unique())

Best practices:
- Parse markdown content carefully for specific information
- Look for ownership percentages and share counts
- Track changes across funding rounds
- Consider both fully diluted and current ownership

Only use your assigned tool. If you cannot answer with your tool, say so clearly."""

    return CapTablesAgent(tool, sys_msg_content, openai_api_key)