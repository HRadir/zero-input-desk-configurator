from pydantic import BaseModel, Field

from app.constraints.models import DeskConfig


class GenerationResult(BaseModel):
    config: DeskConfig
    message: str = Field(
        description=(
            "Message en français à destination du client, expliquant ce qui a été fait à sa demande. "
            "Si une partie de la demande n'a aucun équivalent dans le catalogue (couleur, matière, "
            "accessoire, décoration, etc. qui n'existe pas dans les options disponibles), le signaler "
            "explicitement et clairement dans ce message plutôt que de l'ignorer silencieusement."
        )
    )
