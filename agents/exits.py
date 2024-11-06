from .base import BaseAgent
from langgraph.graph import MessagesState

class ExitsAgent(BaseAgent):
    def agent(self, state: MessagesState):
        response = self.llm.invoke([self.sys_msg] + state["messages"])
        return {"messages": [response]}

def create_exits_agent(tool, openai_api_key):
    sample_data = tool.locals['sante_seen_exit_deals'].head(3).to_string()

    sys_msg_content = f"""You are the Exit Specialist at Santé Ventures, focused on analyzing portfolio company exits.

Available Data Structure:
{sample_data}

Key columns include:
- Company Name
- Exit Type (IPO, M&A, etc.)
- Exit Value
- Exit Date
- Buyer/Market
- Return Multiple
- Holding Period

Example queries you can handle:
1. sante_seen_exit_deals.groupby('Exit Type')['Exit Value'].agg(['mean', 'count'])
2. sante_seen_exit_deals['Return Multiple'].describe()
3. sante_seen_exit_deals[sante_seen_exit_deals['Holding Period'] < 5]['Exit Value'].sum()

Best practices:
- Calculate key metrics like IRR and MOIC
- Analyze exit patterns and trends
- Compare exits across different time periods
- Consider both strategic and financial exits

Only use your assigned tool. If you cannot answer with your tool, say so clearly."""

    return ExitsAgent(tool, sys_msg_content, openai_api_key) 