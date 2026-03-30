#!/usr/bin/env python3
"""Chat router — AI-powered conversation endpoint."""

import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()

# Lazy-init the agent (only when first chat request arrives)
_agent = None


def _get_agent():
    """Lazy initialization of TravelAgent."""
    global _agent
    if _agent is None:
        try:
            from engine.ai_orchestrator import TravelAgent
            _agent = TravelAgent()
        except ValueError as e:
            raise HTTPException(
                status_code=503,
                detail=str(e),
            )
    return _agent


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    stream: bool = Field(False, description="Enable streaming response")


class ChatResponse(BaseModel):
    reply: str
    session_id: str


@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """Send a message to the AI travel agent."""
    agent = _get_agent()

    session_id = req.session_id or str(uuid.uuid4())

    if req.stream:
        # Streaming response
        def generate():
            for token in agent.chat_stream(session_id, req.message):
                yield token

        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={"X-Session-Id": session_id},
        )
    else:
        # Regular response
        reply = agent.chat(session_id, req.message)
        return ChatResponse(reply=reply, session_id=session_id)


@router.delete("/chat/{session_id}")
async def clear_chat(session_id: str):
    """Clear conversation history for a session."""
    agent = _get_agent()
    agent.clear_session(session_id)
    return {"status": "cleared", "session_id": session_id}
