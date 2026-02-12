from pydantic import BaseModel
from typing import List, Dict, Optional, Literal, Any
from datetime import datetime

class NPCState(BaseModel):
    stage: int = 0
    flags: Dict[str, bool] = {}

class MessageTurn(BaseModel):
    role: Literal['user', 'npc']
    name: Optional[str] = None
    text: str
    timestamp: datetime = None

class CaseState(BaseModel):
    mode: Literal['MENU', 'NAVIGATION', 'DIALOGUE', 'FILES', 'DETENTION'] = 'MENU'
    open_characters: List[str] = []
    open_locations: List[str] = []
    open_evidence: List[str] = []
    last_active_character: Optional[str] = None
    npc_states: Dict[str, NPCState] = {}
    recent_messages: List[MessageTurn] = []
    flags: Dict[str, Any] = {}

class RouteResult(BaseModel):
    route_to: str
    confidence: float
    reason_tags: List[str]

class Evidence(BaseModel):
    id: str
    title: str
    description: str
    condition: str  # упрощённо, можно потом заменить на функцию

class Location(BaseModel):
    id: str
    name: str
    address: str
    description: str
    available_npcs: List[str]
    open_by_default: bool = False
    unlock_condition: Optional[str] = None

class Character(BaseModel):
    id: str
    name: str
    role: str
    description: str
