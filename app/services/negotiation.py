import httpx

from app.errors import ExternalAPIFailure
from app.models import NegotiationResponse


class NegotiationClient:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds

    async def submit(self, english_input: str) -> NegotiationResponse:
        payload = {"input": english_input}
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(self.base_url, json=payload)
                response.raise_for_status()
                body = response.json()
        except Exception as exc:
            raise ExternalAPIFailure(str(exc)) from exc

        suggestion = body.get("suggestion")
        if not suggestion:
            raise ExternalAPIFailure("Negotiation API response missing 'suggestion'")

        return NegotiationResponse(suggestion=suggestion, raw_payload=body)
