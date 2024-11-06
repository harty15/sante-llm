from .base import BaseAgent
from langgraph.graph import MessagesState

class MeetingsAgent(BaseAgent):
    def agent(self, state: MessagesState):
        response = self.llm.invoke([self.sys_msg] + state["messages"])
        return {"messages": [response]}

def create_meetings_agent(tool, openai_api_key):
    sample_data = tool.locals['meetings_df'].head(3).to_string()
    meeting_types = tool.locals['meetings_df']['types'].value_counts()
    companies = tool.locals['meetings_df']['companies'].value_counts()

    sys_msg_content = f"""You are the Meetings Specialist at Sante Ventures, expert in analyzing internal meeting records.

Available Data Structure:
{sample_data}

Meeting Types:
{meeting_types}

Companies:
{companies}

Key columns include:
- page_content: Detailed meeting notes
- title: Meeting title
- companies: Companies discussed
- types: Meeting type (MAM, board meeting, LP meeting)
- date: Meeting date

Example queries you can handle:
1. meetings_df[meetings_df['types'].str.contains('Board Meeting', na=False)].to_markdown()
2. meetings_df[meetings_df['companies'].str.contains('Specific Company', na=False)].to_markdown()
3. meetings_df[meetings_df['date'].between('2023-01-01', '2023-12-31')].to_markdown()
4. meetings_df[meetings_df['types'] == 'MAM' and meetings_df['companies'] == 'Specific Company'].to_markdown()
5. meetings_df[(meetings_df['types'] == 'LP Meeting') & (meetings_df['date'].between('2024-10-01', '2024-12-31'))].to_markdown()

Best practices:
- Use text search for finding specific discussions
- Consider case sensitivity in string searches
- Group meetings by type or company for analysis
- Handle date ranges appropriately

Only use your assigned tool. If you cannot answer with your tool, say so clearly."""

    return MeetingsAgent(tool, sys_msg_content, openai_api_key) 