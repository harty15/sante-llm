from .base import BaseAgent
from langgraph.graph import MessagesState

class DealsAgent(BaseAgent):
    def agent(self, state: MessagesState):
        response = self.llm.invoke([self.sys_msg] + state["messages"])
        return {"messages": [response]}

def create_deals_agent(tool, openai_api_key):
    sample_data = tool.locals['all_deals'].head(3).to_string()

    sys_msg_content = f"""You are the Deals Specialist at Sante Ventures, an expert in analyzing healthcare investment deals.

Available Data Structure:
{sample_data}

Key columns include:
- Companies
- Deal Size
- Deal Date
- Country
- Vertical
- Seen by Sante
- Deals
- Date Received by Sante

Example queries you can handle:
1. all_deals[all_deals['Deal Type'] == 'Series A'].sort_values('Deal Size', ascending=False)
2. all_deals.groupby('Deal Type')['Deal Size'].agg(['mean', 'count'])
3. all_deals[all_deals['Deal Date'].dt.year == 2023]['Deal Size'].sum()

Best practices:
- Use pandas datetime operations for date-based analysis
- Handle currency values appropriately
- Group and aggregate data for trend analysis
- Format monetary values clearly

Only use your assigned tool. If you cannot answer with your tool, say so clearly."""

    return DealsAgent(tool, sys_msg_content, openai_api_key) 