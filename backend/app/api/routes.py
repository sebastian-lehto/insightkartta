from fastapi import APIRouter
from backend.app.services.insight_service import get_region_insights
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
    return get_dataset(dataset_name)

@router.get("/regions/{region}/insights")
def region_insights(region: str):
    return get_region_insights(region)