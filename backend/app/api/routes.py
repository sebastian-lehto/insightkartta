from fastapi import APIRouter
from backend.app.services.analysis_service import get_unemployment_analysis

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/unemployment")
def unemployment():
    return get_unemployment_analysis()