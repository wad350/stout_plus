"""Local HTTP API client for a Stout Plus boiler."""

from __future__ import annotations

import asyncio
from typing import Any

from aiohttp import ClientError, ClientSession


class StoutPlusApiError(Exception):
    """Base exception for communication with the boiler."""


class StoutPlusApi:
    """Small asynchronous wrapper around the boiler HTTP interface."""

    def __init__(self, session: ClientSession, host: str, timeout: int = 10) -> None:
        """Initialize the API client."""
        self._session = session
        self._host = host.strip().removeprefix("http://").rstrip("/")
        self._timeout = timeout

    @property
    def host(self) -> str:
        """Return the normalized boiler host."""
        return self._host

    async def async_get(self, endpoint: str) -> dict[str, Any]:
        """Fetch and decode a JSON endpoint."""
        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.get(self._url(endpoint)) as response:
                    response.raise_for_status()
                    data = await response.json(content_type=None)
        except (TimeoutError, ClientError, ValueError) as err:
            raise StoutPlusApiError(f"GET {endpoint} failed: {err}") from err

        if not isinstance(data, dict):
            raise StoutPlusApiError(f"GET {endpoint} returned invalid data")
        return data

    async def async_post_text(self, endpoint: str, value: str) -> None:
        """Post the text payload format used by boiler controls."""
        await self._async_post(
            endpoint,
            data=value,
            headers={"Content-Type": "text/plain;charset=UTF-8"},
        )

    async def async_post_form(self, endpoint: str, data: dict[str, str]) -> None:
        """Post a form payload used by schedule and power controls."""
        await self._async_post(endpoint, data=data)

    async def _async_post(
        self,
        endpoint: str,
        *,
        data: str | dict[str, str],
        headers: dict[str, str] | None = None,
    ) -> None:
        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.post(
                    self._url(endpoint), data=data, headers=headers
                ) as response:
                    response.raise_for_status()
        except (TimeoutError, ClientError) as err:
            raise StoutPlusApiError(f"POST {endpoint} failed: {err}") from err

    def _url(self, endpoint: str) -> str:
        return f"http://{self._host}/{endpoint.lstrip('/')}"
