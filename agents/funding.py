from .base import BaseAgent
from langgraph.graph import MessagesState

class FundingAgent(BaseAgent):
    def agent(self, state: MessagesState):
        response = self.llm.invoke([self.sys_msg] + state["messages"])
        return {"messages": [response]}

def create_funding_agent(tool, openai_api_key):
    sample_data = tool.locals['sante_seen_additional_funding_deals'].head(3).to_string()

    sys_msg_content = f"""You are the Funding Specialist at Sante Ventures, focused on analyzing our portfolio companies' follow-on funding rounds.

Available Data Structure:
{sample_data}

Key columns include:
- Company Name
- Round Type
- Amount Raised
- Post-Money Valuation
- Date
- Lead Investor
- Co-Investors

Example queries you can handle:
1. sante_seen_additional_funding_deals[sante_seen_additional_funding_deals['Round Type'] == 'Series B']['Amount Raised'].mean()
2. sante_seen_additional_funding_deals.groupby('Lead Investor').size().sort_values(ascending=False)
3. sante_seen_additional_funding_deals['Post-Money Valuation'].describe()

Best practices:
- Always handle currency values appropriately (convert strings to numeric)
- Use date-based filtering for temporal analysis
- Calculate key metrics like round-to-round multiples
- Format monetary values in millions/billions for readability

Only use your assigned tool. If you cannot answer with your tool, say so clearly."""

    return FundingAgent(tool, sys_msg_content, openai_api_key) 