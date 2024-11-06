from .base import BaseAgent
from langgraph.graph import MessagesState

class CompaniesAgent(BaseAgent):
    def agent(self, state: MessagesState):
        response = self.llm.invoke([self.sys_msg] + state["messages"])
        return {"messages": [response]}

def create_companies_agent(tool, openai_api_key):
    sample_data = tool.locals['all_companies'].head(3).to_string()

    sys_msg_content = f"""You are the Companies Specialist at Sante Ventures, an expert in analyzing healthcare company data.

Available Data Structure:
{sample_data}

Key columns include:
- Companies
- Description
- Deals
- Vertical 
- Country
- Date Received by Sante

Example queries you can handle:
1. all_companies[all_companies['Keywords'].str.contains('biomarker discovery', na=False)]
2. all_companies.groupby('Vertical').size().sort_values(ascending=False)
3. all_companies[all_companies['Companies'] == 'Specific Company']

Best practices:
- Use pandas operations for efficient filtering and analysis
- Always check for null values before string operations
- Use .loc[] for label-based indexing
- Format your output as a clear, readable DataFrame

Only use your assigned tool. If you cannot answer with your tool, say so clearly."""

    return CompaniesAgent(tool, sys_msg_content, openai_api_key)