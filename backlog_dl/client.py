# coding: utf_8
import logging
import time
from typing import Iterable, Literal, Self
from urllib.parse import quote

from pydantic import BaseModel
from requests import Response, Session

_logger = logging.getLogger(__name__)


class SharedFile(BaseModel):
    id: int
    dir: str
    name: str
    size: int | None
    type: Literal["directory", "file"]
    updated: str

    def path(self: Self) -> str:
        return self.dir + self.name

    def size_(self: Self) -> int:
        return self.size or 0


class Client:
    def __init__(
        self: "Client",
        *,
        domain: str,
        project_id: str,
        api_key: str,
        wait: float,
    ) -> None:
        self._api_key = api_key
        self._base_url = f"https://{domain}/api/v2/projects/{project_id}"
        self._session = Session()
        self._wait = wait
        self._last_request_time = 0

    def __enter__(self: Self) -> Self:
        self._session.__enter__()
        return self

    def __exit__(self: Self, *args) -> None:
        self._session.__exit__(*args)

    def _get(self: Self, url: str) -> Response:
        wait = self._wait - (time.time() - self._last_request_time)
        if wait > 0:
            time.sleep(wait)

        url = f"{url}?apiKey={self._api_key}"
        while True:
            res = self._session.get(url)
            if res.status_code != 429:
                self._last_request_time = time.time()
                break

            _logger.warning(
                "It appears you have been rate limited. Resubmit your request in 60 seconds."  # noqa
            )
            time.sleep(60)
        return res

    def download_file(self: Self, file_id: int) -> bytes:
        res = self._get(f"{self._base_url}/files/{file_id}")
        return res.content

    def list_shared_files(self: Self, path: str) -> Iterable[SharedFile]:
        res = self._get(f"{self._base_url}/files/metadata{quote(path)}")
        for n in res.json():
            yield SharedFile.model_validate(n)
