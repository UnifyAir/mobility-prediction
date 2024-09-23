from pydantic import BaseModel
from typing import List, Dict

class LoadDataRequest(BaseModel):
    csv_file: str

class PredictRequest(BaseModel):
    user_id: str
    cell_tower_loads: Dict[str, float]
    timestamp: int
    current_cell_tower: str

class PredictResponse(BaseModel):
    optimal_handover_tower: str 
    reason: str
