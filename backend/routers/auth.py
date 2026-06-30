from fastapi import APIRouter, Depends

from core.responses import api_success
from core.security import get_current_user

router = APIRouter()


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return api_success(current_user)
