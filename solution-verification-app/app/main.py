import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .config import settings
from .flags import generate_flag
from .validators import validate_challenge, list_challenges

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Solution Verification Service",
    description="Validates player challenge solutions and returns dynamic flags",
)


class ValidateRequest(BaseModel):
    token: str
    challenge: str


class ValidateResponse(BaseModel):
    success: bool
    message: str
    flag: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/challenges")
def get_challenges():
    """List available challenges that can be validated."""
    return {"challenges": list_challenges()}


@app.post("/validate", response_model=ValidateResponse)
def validate(req: ValidateRequest):
    player_name = settings.token_map.get(req.token)
    if not player_name:
        raise HTTPException(status_code=401, detail="Invalid verification token")

    logger.info("Validation request: challenge=%s player=%s", req.challenge, player_name)

    result = validate_challenge(req.challenge, player_name)

    if result.success:
        flag = generate_flag(req.challenge, player_name)
        return ValidateResponse(success=True, message=result.message, flag=flag)

    return ValidateResponse(success=False, message=result.message)
