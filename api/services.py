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
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=api_key,
            temperature=0,
            convert_system_message_to_human=True,
        )
        
        self.system_prompt = SystemMessagePromptTemplate.from_template(
            "You are a network optimization assistant. Analyze the following user trajectory data in csv format. "
            "For each user position, the data has recorded five candidate cell towers (within 2 km) along with their respective distances. "
            "Identify patterns and key insights related to user movement, cell tower usage, and potential handover optimizations. "
            "This analysis will be used as the basis for future recommendations."
        )
        self.recommendation_prompt = HumanMessagePromptTemplate(prompt=recommendation_prompt)
 
        self.recommendation_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([self.system_prompt, self.recommendation_prompt]),
            verbose=True
        )

    async def predict_best_cell_towers(
        self,
        user_id: str,
        cell_tower_loads: Dict,
        timestamp: int,
        current_cell_tower: int,
        db: AsyncSession,
    ) -> str:
        # Fetch trajectory data directly here
        trajectory_data = await get_user_trajectory_data(user_id, timestamp, db)
        
        recommendation_result = await self.recommendation_chain.apredict(
            trajectory_data=trajectory_data,
            timestamp=timestamp, 
            cell_tower_loads=cell_tower_loads,
            current_cell_tower=current_cell_tower
        )
        return parse_prompt_output_json(recommendation_result)


    # async def predict_worst_cell_towers(
    #     self,
    #     user_id: str,
    #     cell_tower_loads: Dict,
    #     timestamp: int,
    #     current_cell_tower: int,
    #     db: AsyncSession,
    # ) -> str:
    #     # Fetch trajectory data directly here
    #     trajectory_data = await get_user_trajectory_data(user_id, timestamp, db)
        
    #     # We'll use a different chain specifically for identifying problematic towers
    #     worst_tower_result = await self.problematic_tower_chain.apredict(
    #         trajectory_data=trajectory_data,
    #         timestamp=timestamp, 
    #         cell_tower_loads=cell_tower_loads,
    #         current_cell_tower=current_cell_tower,
    #         # Additional parameters that might help identify worst towers
    #         historical_failures=await get_tower_failure_history(db),
    #         signal_quality_metrics=await get_signal_quality_data(db)
    #     )
        
    #     # Parse the output to get the worst towers in a structured format
    #     return parse_prompt_output_json(worst_tower_result)

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
    
    # Parse the cleaned JSON string
    result = json.loads(clean_json)
    
    # Convert optimal_handover_tower to string if present
    if 'optimal_handover_tower' in result:
        result['optimal_handover_tower'] = str(result['optimal_handover_tower'])
    
    return result

class NetworkAgentManager:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.user_agents: Dict[str, UserNetworkAgent] = {}

    def get_agent(self, user_id: str) -> UserNetworkAgent:
        """
        Retrieve an existing agent for the user or create a new one.
        """
        if user_id not in self.user_agents:
            self.user_agents[user_id] = UserNetworkAgent(self.api_key, user_id)
        return self.user_agents[user_id]
