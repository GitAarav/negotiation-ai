from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field


class NegotiationRequest(BaseModel):
    input: str = Field(min_length=1, description="English-only case summary from the multilingual layer")


class NegotiationResponse(BaseModel):
    suggestion: str
    settlement_range: str
    risk_level: Literal["low", "medium", "high"]
    next_step: str


app = FastAPI(title="Mock Negotiation Engine")


def build_mock_suggestion(english_input: str) -> NegotiationResponse:
    normalized = english_input.lower()

    if any(keyword in normalized for keyword in ["payment", "invoice", "freelance", "salary", "wage"]):
        return NegotiationResponse(
            suggestion=(
                "A partial settlement between 60% and 80% of the claimed amount is a reasonable opening position."
            ),
            settlement_range="60%-80%",
            risk_level="medium",
            next_step="Request proof of completed work and propose a time-bound payment plan.",
        )

    if any(keyword in normalized for keyword in ["delivery", "product", "goods", "shipment", "order"]):
        return NegotiationResponse(
            suggestion="A replacement or refund-backed settlement offer is reasonable at this stage.",
            settlement_range="40%-70%",
            risk_level="low",
            next_step="Ask for delivery records and offer either replacement or proportional refund.",
        )

    if any(keyword in normalized for keyword in ["rent", "deposit", "tenant", "landlord", "lease"]):
        return NegotiationResponse(
            suggestion="A structured settlement tied to documented damages or dues is reasonable.",
            settlement_range="50%-75%",
            risk_level="medium",
            next_step="Exchange lease records, receipts, and inspection evidence before the next round.",
        )

    return NegotiationResponse(
        suggestion="A balanced opening settlement with documented evidence from both sides is reasonable.",
        settlement_range="50%-70%",
        risk_level="medium",
        next_step="Collect supporting evidence and make a specific written proposal for the next discussion.",
    )


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/negotiation-engine", response_model=NegotiationResponse)
async def negotiate(payload: NegotiationRequest) -> NegotiationResponse:
    return build_mock_suggestion(payload.input)
