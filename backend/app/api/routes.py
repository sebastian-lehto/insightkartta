from fastapi import APIRouter, HTTPException
from backend.app.services.insight_service import (
    get_election_correlations,
    get_region_insights,
    InsightNotFoundError,
)
from backend.app.services.dataset_service import get_dataset, list_datasets

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/datasets")
def datasets():
    return list_datasets()


@router.get("/{dataset_name}")
def dataset(dataset_name: str):
    try:
        return get_dataset(dataset_name)
    except (KeyError, FileNotFoundError):
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_name}' not found")


@router.get("/regions/{region}/insights")
def region_insights(region: str):
    try:
        return get_region_insights(region)
    except InsightNotFoundError:
        raise HTTPException(status_code=404, detail=f"No insights found for region '{region}'")


@router.get("/elections/correlations")
def election_correlations():
    try:
        return get_election_correlations()
    except InsightNotFoundError:
        raise HTTPException(status_code=404, detail="Election correlations not yet generated — run make region-insights")
