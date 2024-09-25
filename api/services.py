from langchain.chains import LLMChain
from collections import defaultdict
import json
from typing import Dict
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Import your database models and retrieval function.
from .database import UserContext, get_user_trajectory_data

# LangChain imports
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_google_genai import ChatGoogleGenerativeAI  # LLM interface
from langchain_community.callbacks.manager import get_openai_callback  # Optional logging
from langchain_core.messages.ai import AIMessage
from langchain_core.messages.human import HumanMessage




from langchain.prompts import PromptTemplate  # Import the base PromptTemplate.
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    AIMessagePromptTemplate
)


recommendation_prompt = PromptTemplate(
    input_variables=["trajectory_data", "cell_tower_loads", "timestamp", "current_cell_tower"],
    template="""

    The input CSV has the following fields:

    time: An integer representing the elapsed time in seconds since the start of the route.
    cell1, distance1, cell2, distance2, …, cell5, distance5: The candidate cell tower IDs and their respective distances (in meters) from the user's current position.
    {trajectory_data}

    What are the best 2-3 cell towers for handover?  Consider the historical patterns and insights from the pattern in above data.
    Predict which is the best cell tower currently at the {timestamp}th second. Also consider the cell tower load on multiple towers as: {cell_tower_loads}, where load value is out of 1.
    Predict the cell tower at the {timestamp}th second, to have least amount of handovers in next 100 seconds based on mobility pattern. When the current cell_tower_id is {current_cell_tower}
    Clearly give your answer in following json format: {{"optimal_handover_tower": int, "reason": "string"}}
    """
)


class UserNetworkAgent:
    def __init__(self, api_key: str, user_id: str):
        self.user_id = user_id
        # Initialize the ChatGoogleGenerativeAI model.
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=api_key,
            temperature=0,
            convert_system_message_to_human=True,
        )
        # Create a ConversationBufferMemory to hold all messages.
        self.memory = ConversationBufferMemory(memory_key="chat_history")
       
        
        self.system_prompt = SystemMessagePromptTemplate.from_template(
                "You are a network optimization assistant. Analyze the following user trajectory data in csv format. "
                "For each user position, the data has recorded five candidate cell towers (within 2 km) along with their respective distances. "
                "Identify patterns and key insights related to user movement, cell tower usage, and potential handover optimizations. "
                "This analysis will be used as the basis for future recommendations."
            )
        self.recommendation_prompt  = HumanMessagePromptTemplate(prompt = recommendation_prompt)
 
        # Create a single ConversationChain that uses the above prompt and memory.
        self.recommendation_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([self.system_prompt, self.recommendation_prompt]),
            verbose=True
        )
        self.is_initialized = False

    async def initialize_context(self, trajectory_data: str):
        """
        Always load context during initialization by running the analysis prompt on the trajectory data.
        The conversation (analysis input and the AI's response) is stored in memory.
        """
        # Run the analysis prompt (the first human message is the trajectory data).
        # At this point, the chat_history is empty.
        
        self.trajectory_data = trajectory_data
        self.is_initialized = True
        return "" 

    async def predict_best_cell_towers(
        self,
        user_id: str,
        cell_tower_loads: Dict,
        timestamp: int,
        current_cell_tower: int,
        db: AsyncSession,
    ) -> str:
        """
        Use the existing conversation (analysis prompt and its result) and add a follow-up human message asking for recommendations.
        The conversation now has: [SystemMessage, HumanMessage (analysis), AIMessage (analysis result), HumanMessage (recommendation query)].
        """
        if not self.is_initialized:
            raise ValueError("Context is not initialized. Please call initialize_context() first.")
        # Build the recommendation query (the new human message).

        recommendation_result = await self.recommendation_chain.apredict(
            trajectory_data=self.trajectory_data,
            timestamp=timestamp, 
            cell_tower_loads=cell_tower_loads,
            current_cell_tower=current_cell_tower
        )
        print(recommendation_result)
        return parse_prompt_output_json(recommendation_result)

def parse_prompt_output_json(input_str):
    """
    Parses a JSON string that may be wrapped in Markdown code block delimiters.

    Args:
        input_str (str): The input string containing the JSON data, possibly with Markdown delimiters.

    Returns:
        dict: The parsed JSON data as a Python dictionary.
    """
    # Remove the opening delimiter (e.g., ```json or ```) and any whitespace that follows.
    clean_json = re.sub(r'^```(?:json)?\s*', '', input_str)
    # Remove the closing delimiter (```) and any preceding whitespace.
    clean_json = re.sub(r'\s*```$', '', clean_json)
    
    # Parse the cleaned JSON string.
    return json.loads(clean_json)

class NetworkAgentManager:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.user_agents: Dict[str, UserNetworkAgent] = {}

    async def get_or_initialize_agent(
        self,
        user_id: str,
        db,
    ) -> UserNetworkAgent:
        """
        Retrieve an existing agent for the user or create and initialize a new one.
        Always loads context during initialization.
        """
        if user_id not in self.user_agents:
            self.user_agents[user_id] = UserNetworkAgent(self.api_key, user_id)
        agent = self.user_agents[user_id]
        if not agent.is_initialized:
            trajectory_data = await get_user_trajectory_data(user_id, 0, db)
            await agent.initialize_context(trajectory_data)
        return agent