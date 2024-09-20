import logging
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .database import initialize_database, get_db, UserTrajectory
from .schemas import PredictRequest, PredictResponse
from .services import NetworkAgentManager
from .config import get_gemini_api_key

logger = logging.getLogger(__name__)

app = FastAPI()
network_agent_manager = NetworkAgentManager(api_key=get_gemini_api_key())

# Initialize database on startup
@app.on_event("startup")
async def startup():
    await initialize_database()

@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest, db: AsyncSession = Depends(get_db)):
    """Endpoint to predict the best cell towers for a user."""
    # Get or initialize user agent
    user_agent = await network_agent_manager.get_or_initialize_agent(
        request.user_id, 
        db
    )
    
    # Make prediction
    result = await user_agent.predict_best_cell_towers(
        user_id=request.user_id,
        cell_tower_loads=request.cell_tower_loads,
        timestamp=request.timestamp,
        current_cell_tower=request.current_cell_tower,
        db=db
    )
    tower = result.get('optimal_handover_tower', '')
    result['optimal_handover_tower'] = str(tower)
    print("received_result", result)
    return PredictResponse(**result)
