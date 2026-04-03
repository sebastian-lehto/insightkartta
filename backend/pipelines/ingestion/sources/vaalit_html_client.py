from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

import requests
from bs4 import BeautifulSoup
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

LOGGER = logging.getLogger(__name__)


class FetchError(RuntimeError):
    """Raised when an election result page cannot be fetched successfully."""


@dataclass(frozen=True)
class FetchTarget:
    year: int
    region: str  # InsightKartta region code, e.g. KU020

    @property
    def numeric_code(self) -> str:
        if not self.region.startswith("KU") or len(self.region) != 5:
            raise ValueError(f"Expected municipality region code like 'KU020', got: {self.region}")
        return self.region[2:]

    @property
    def url(self) -> str:
        return f"https://tulospalvelu.vaalit.fi/KV-{self.year}/en/kutulos_{self.numeric_code}.html"


@dataclass
class FetchResult:
    dataset: str
    year: int
    region: str
    source_url: str
    http_status: int
    fetched_at: str
    content_hash: str | None
    html_path: str | None
    manifest_path: str | None
    from_cache: bool
    status: str  # "ok" | "not_found"
    error: str | None = None


class VaalitHtmlClient:
    """Polite fetcher for official municipal election municipality pages."""

    def __init__(
        self,
        *,
        dataset_name: str,
        raw_root: Path,
        timeout_seconds: int = 20,
        backoff_factor: float = 0.75,
        user_agent: str = "InsightKartta/0.1 (+portfolio data pipeline)",
        sleep_seconds: float = 0.2,
        overwrite: bool = False,
    ) -> None:
        self.dataset_name = dataset_name
        self.raw_root = raw_root
        self.timeout_seconds = timeout_seconds
        self.sleep_seconds = sleep_seconds
        self.overwrite = overwrite
        self.session = self._build_session(user_agent=user_agent, backoff_factor=backoff_factor)

    @staticmethod
    def _build_session(*, user_agent: str, backoff_factor: float) -> Session:
        session = requests.Session()
        retry = Retry(
            total=4,
            read=4,
            connect=4,
            backoff_factor=backoff_factor,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update({"User-Agent": user_agent})
        return session

    def fetch_many(self, targets: Iterable[FetchTarget]) -> list[FetchResult]:
        results: list[FetchResult] = []

        for index, target in enumerate(targets, start=1):
            result = self.fetch_one(target)
            results.append(result)

            if result.status == "ok":
                LOGGER.info(
                    "[%s] fetched %s %s (cache=%s)",
                    index,
                    target.year,
                    target.region,
                    result.from_cache,
                )
            elif result.status == "not_found":
                LOGGER.warning(
                    "[%s] missing page for %s %s: %s",
                    index,
                    target.year,
                    target.region,
                    target.url,
                )
            else:
                LOGGER.error(
                    "[%s] unexpected fetch status for %s %s: %s",
                    index,
                    target.year,
                    target.region,
                    result.status,
                )

            time.sleep(self.sleep_seconds)

        return results

    def fetch_one(self, target: FetchTarget) -> FetchResult:
        html_path = self._html_path(target)
        manifest_path = self._manifest_path(target)

        if html_path.exists() and manifest_path.exists() and not self.overwrite:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            return FetchResult(
                dataset=manifest["dataset"],
                year=manifest["year"],
                region=manifest["region"],
                source_url=manifest["source_url"],
                http_status=manifest["http_status"],
                fetched_at=manifest["fetched_at"],
                content_hash=manifest.get("content_hash"),
                html_path=str(html_path),
                manifest_path=str(manifest_path),
                from_cache=True,
                status=manifest.get("status", "ok"),
                error=manifest.get("error"),
            )

        response = self.session.get(target.url, timeout=self.timeout_seconds)

        if response.status_code == 404:
            fetched_at = datetime.now(UTC).isoformat()

            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest = {
                "dataset": self.dataset_name,
                "year": target.year,
                "region": target.region,
                "source_url": target.url,
                "http_status": response.status_code,
                "fetched_at": fetched_at,
                "content_hash": None,
                "html_path": None,
                "status": "not_found",
                "error": "Page not available for municipality/year",
            }
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            return FetchResult(
                dataset=self.dataset_name,
                year=target.year,
                region=target.region,
                source_url=target.url,
                http_status=response.status_code,
                fetched_at=fetched_at,
                content_hash=None,
                html_path=None,
                manifest_path=str(manifest_path),
                from_cache=False,
                status="not_found",
                error="Page not available for municipality/year",
            )

        if response.status_code != 200:
            raise FetchError(f"Failed to fetch {target.url}: HTTP {response.status_code}")

        html = response.text
        self._validate_basic_structure(html=html, url=target.url)

        content_hash = hashlib.sha256(html.encode("utf-8")).hexdigest()
        fetched_at = datetime.now(UTC).isoformat()

        html_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)

        html_path.write_text(html, encoding="utf-8")
        manifest = {
            "dataset": self.dataset_name,
            "year": target.year,
            "region": target.region,
            "source_url": target.url,
            "http_status": response.status_code,
            "fetched_at": fetched_at,
            "content_hash": content_hash,
            "html_path": str(html_path),
            "status": "ok",
            "error": None,
        }
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return FetchResult(
            dataset=self.dataset_name,
            year=target.year,
            region=target.region,
            source_url=target.url,
            http_status=response.status_code,
            fetched_at=fetched_at,
            content_hash=content_hash,
            html_path=str(html_path),
            manifest_path=str(manifest_path),
            from_cache=False,
            status="ok",
            error=None,
        )

    def _html_path(self, target: FetchTarget) -> Path:
        return self.raw_root / self.dataset_name / str(target.year) / f"{target.region}.html"

    def _manifest_path(self, target: FetchTarget) -> Path:
        return self.raw_root / self.dataset_name / str(target.year) / f"{target.region}.manifest.json"

    @staticmethod
    def _validate_basic_structure(*, html: str, url: str) -> None:
        soup = BeautifulSoup(html, "html.parser")
        if soup.find("table", class_="tulosPuolueTaulu") is None:
            raise FetchError(f"Expected party result table not found in {url}")