import logging
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .database import initialize_database, get_db, UserTrajectory
from .schemas import PredictRequest, PredictResponse
from .services import NetworkAgentManager
from .config import get_gemini_api_key

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI()
network_agent_manager = NetworkAgentManager(api_key=get_gemini_api_key())

# Initialize database on startup
@app.on_event("startup")
async def startup():
    logger.info("Initializing database...")
    await initialize_database()
    logger.info("Database initialization complete")

@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest, db: AsyncSession = Depends(get_db)):
    """Endpoint to predict the best cell towers for a user."""
    logger.info(f"Received prediction request for user_id: {request.user_id}")
    
    try:
        # Get user agent
        user_agent = network_agent_manager.get_agent(request.user_id)
        logger.debug(f"Retrieved agent for user_id: {request.user_id}")
        
        # Make prediction
        logger.info(f"Making prediction for user_id: {request.user_id}, current_cell_tower: {request.current_cell_tower}")
        result = await user_agent.predict_best_cell_towers(
            user_id=request.user_id,
            cell_tower_loads=request.cell_tower_loads,
            timestamp=request.timestamp,
            current_cell_tower=request.current_cell_tower,
            db=db
        )
        
        logger.info(f"Prediction complete for user_id: {request.user_id}. Optimal tower: {result['optimal_handover_tower']}")
        return PredictResponse(**result)
        
    except Exception as e:
        logger.error(f"Error processing prediction request for user_id: {request.user_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
