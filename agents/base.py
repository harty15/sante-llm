from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    def __init__(self, tool, sys_msg_content, openai_api_key):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=openai_api_key).bind_tools([tool])
        self.sys_msg = SystemMessage(content=sys_msg_content)

    @abstractmethod
    def agent(self, state):
        pass 