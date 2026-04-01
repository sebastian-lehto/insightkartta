from fastapi import APIRouter
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