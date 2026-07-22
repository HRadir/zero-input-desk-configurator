from pydantic import BaseModel, Field


class DeskConfig(BaseModel):
    finition_id: str
    plateau_id: str
    largeur_choisie_cm: int = Field(gt=0)
    structure_id: str
    nombre_ecrans: int = Field(ge=1, le=6)
    accessoires: list[str] = Field(default_factory=list)
    style_demande: str | None = None
