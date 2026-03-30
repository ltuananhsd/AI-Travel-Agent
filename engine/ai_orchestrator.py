#!/usr/bin/env python3
"""
AI Orchestrator — Custom LLM-powered travel agent with tool calling.
Uses OpenAI-compatible SDK to communicate with any OpenAI-compatible API.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Generator

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from openai import OpenAI
from scripts.config import LLM_API_KEY, LLM_MODEL, LLM_BASE_URL
from engine.prompts import SYSTEM_PROMPT, TOOL_DEFINITIONS
from engine.tool_functions import execute_tool


class TravelAgent:
    """AI travel agent with conversation memory and tool-calling."""

    def __init__(self):
        if not LLM_API_KEY or LLM_API_KEY.startswith("sk-your"):
            raise ValueError(
                "LLM_API_KEY not configured. "
                "Set it in .env file or environment variable."
            )

        self.client = OpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL,
        )
        self.model = LLM_MODEL
        self.conversations = {}  # session_id → message history

    def _get_history(self, session_id: str) -> list:
        """Get or create conversation history for a session."""
        if session_id not in self.conversations:
            # Inject current date/time so AI can resolve "ngày mai", "tuần sau", etc.
            now = datetime.now()
            time_context = (
                f"Ngày giờ hiện tại: {now.strftime('%Y-%m-%d %H:%M')} "
                f"({now.strftime('%A')}, timezone: {now.astimezone().tzinfo})"
            )
            dynamic_prompt = f"{time_context}\n\n{SYSTEM_PROMPT}"
            self.conversations[session_id] = [
                {"role": "system", "content": dynamic_prompt}
            ]
        return self.conversations[session_id]

    def _trim_history(self, messages: list, max_messages: int = 30):
        """Keep conversation history under control. Always preserve system prompt."""
        if len(messages) <= max_messages:
            return messages
        # Keep system prompt + last N messages
        return [messages[0]] + messages[-(max_messages - 1):]

    def chat(self, session_id: str, user_message: str) -> str:
        """
        Process a user message and return AI response.
        Handles tool calls automatically (search flights, etc).
        """
        messages = self._get_history(session_id)
        messages.append({"role": "user", "content": user_message})

        # Trim if needed
        messages = self._trim_history(messages)
        self.conversations[session_id] = messages

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=4096,
            )
        except Exception as e:
            error_msg = f"AI service error: {str(e)}"
            messages.append({"role": "assistant", "content": error_msg})
            return error_msg

        choice = response.choices[0]
        message = choice.message

        # Handle tool calls
        if message.tool_calls:
            # Add assistant message with tool calls
            messages.append(message.model_dump())

            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                try:
                    func_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    func_args = {}

                # Execute the tool
                tool_result = execute_tool(func_name, func_args)

                # Add tool result to conversation
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result, ensure_ascii=False),
                })

            # Get final response after tool execution
            try:
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=4096,
                )
                assistant_reply = final_response.choices[0].message.content or ""
            except Exception as e:
                assistant_reply = f"Error processing results: {str(e)}"

        else:
            assistant_reply = message.content or ""

        messages.append({"role": "assistant", "content": assistant_reply})
        return assistant_reply

    def chat_stream(self, session_id: str, user_message: str) -> Generator[str, None, None]:
        """
        Stream AI response token by token.
        Note: Tool calls are executed synchronously, then the response is streamed.
        """
        messages = self._get_history(session_id)
        messages.append({"role": "user", "content": user_message})
        messages = self._trim_history(messages)
        self.conversations[session_id] = messages

        try:
            # First call — check if tools are needed (non-streaming)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=4096,
            )

            choice = response.choices[0]
            message = choice.message

            # If tool calls needed, execute them first
            if message.tool_calls:
                messages.append(message.model_dump())

                for tool_call in message.tool_calls:
                    func_name = tool_call.function.name
                    try:
                        func_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        func_args = {}

                    # Yield a status message
                    yield f"🔍 Đang tìm kiếm chuyến bay...\n\n"

                    tool_result = execute_tool(func_name, func_args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result, ensure_ascii=False),
                    })

                # Stream the final response after tool execution
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=4096,
                    stream=True,
                )

                full_reply = ""
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        token = chunk.choices[0].delta.content
                        full_reply += token
                        yield token

                messages.append({"role": "assistant", "content": full_reply})

            else:
                # No tool calls — make a streaming call for real token-by-token UX
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=4096,
                    stream=True,
                )

                full_reply = ""
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        token = chunk.choices[0].delta.content
                        full_reply += token
                        yield token

                messages.append({"role": "assistant", "content": full_reply})

        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            messages.append({"role": "assistant", "content": error_msg})
            yield error_msg

    def clear_session(self, session_id: str):
        """Clear conversation history for a session."""
        if session_id in self.conversations:
            del self.conversations[session_id]

    def get_session_info(self, session_id: str) -> dict:
        """Get info about a session."""
        messages = self.conversations.get(session_id, [])
        return {
            "session_id": session_id,
            "message_count": len(messages),
            "has_history": len(messages) > 1,
        }
