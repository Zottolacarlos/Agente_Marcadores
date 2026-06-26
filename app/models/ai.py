from __future__ import annotations

from pydantic import BaseModel, Field


class AIBookmarkClassification(BaseModel):
    """Resultado estructurado de la capa IA opcional para un bookmark.

    Es aditivo: convive con la clasificación local por reglas, no la reemplaza.
    """

    category: str
    subcategory: str | None = None
    intent: str
    priority: int = Field(ge=0, le=100)
    recommended_action: str
    reason: str
    confidence: float = Field(ge=0, le=1)
