from pydantic import BaseModel, Field
from typing import Optional

class PlayerSettings(BaseModel):
    type: str
    model: Optional[str] = None
    temperature: Optional[float] = None
    maxTokens: Optional[int] = Field(None, alias='maxTokens')
    topP: Optional[float] = Field(None, alias='topP')
    topK: Optional[float] = Field(None, alias='topK')
    thinkingMode: Optional[bool] = Field(None, alias='thinkingMode')

class GameSettings(BaseModel):
    player1: PlayerSettings
    player2: PlayerSettings

class HumanMove(BaseModel):
    pos: str
    way: str
    extended_rule: Optional[list[str]] = None