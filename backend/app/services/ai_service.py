import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from google import genai


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

# ai_service.py
#     ↓
# services/
#     ↓
# app/
#     ↓
# backend/
#     ↓
# smart-task-tracker/
#     ↓
# .env

PROJECT_ROOT = Path(__file__).resolve().parents[3]

load_dotenv(PROJECT_ROOT / ".env")


# ============================================================
# GEMINI MODEL
# ============================================================

MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash-lite",
)


# ============================================================
# CORTEX AI SERVICE
# ============================================================

class CortexAI:

    def __init__(self):

        key = os.getenv("GEMINI_API_KEY")

        self.client = (
            genai.Client(api_key=key)
            if key
            else None
        )

    # ========================================================
    # PARSE JSON FROM AI
    # ========================================================

    def _json(self, text: str):

        if not text:
            return None

        cleaned = text.strip()

        # Remove Markdown code fences
        cleaned = re.sub(
            r"^```json\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r"^```\s*",
            "",
            cleaned,
        )

        cleaned = re.sub(
            r"\s*```$",
            "",
            cleaned,
        )

        cleaned = cleaned.strip()

        # Try normal JSON first
        try:
            return json.loads(cleaned)

        except json.JSONDecodeError:
            pass

        # Try to find JSON object inside response
        match = re.search(
            r"\{.*\}",
            cleaned,
            re.DOTALL,
        )

        if not match:
            return None

        try:
            return json.loads(match.group(0))

        except json.JSONDecodeError:
            return None

    # ========================================================
    # TASK ANALYSIS
    # ========================================================

    def analyze_task(
        self,
        title: str,
        description: str | None,
    ):

        # ----------------------------------------------------
        # No Gemini API key
        # ----------------------------------------------------

        if not self.client:

            return {
                "priority": "medium",
                "reason": (
                    "AI key is not configured; "
                    "using a safe default."
                ),
                "subtasks": [],
            }

        # ----------------------------------------------------
        # Task analysis prompt
        # ----------------------------------------------------

        prompt = f"""
You are CORTEX, an AI productivity copilot.

Analyze the following task.

Return ONLY valid JSON.

Do not use Markdown.
Do not use code fences.
Do not add explanations outside the JSON.

The JSON must contain exactly these keys:

priority
reason
subtasks

Priority MUST be exactly one of:

low
medium
high
urgent

Subtasks must be a short array of strings.

Example:

{{
    "priority": "high",
    "reason": "This task is important and requires immediate attention.",
    "subtasks": [
        "Review the requirements",
        "Complete the main work",
        "Review the final result"
    ]
}}

Title:
{title}

Description:
{description or ""}
"""

        try:

            result = self.client.models.generate_content(
                model=MODEL,
                contents=prompt,
            )

            parsed = self._json(
                result.text
            )

            if not parsed:

                return {
                    "priority": "medium",
                    "reason": (
                        "Unable to parse AI response."
                    ),
                    "subtasks": [],
                }

            return parsed

        except Exception as exc:

            return {
                "priority": "medium",
                "reason": (
                    f"AI analysis failed: {exc}"
                ),
                "subtasks": [],
            }

    # ========================================================
    # CORTEX AI ASSISTANT
    # ========================================================

    def assistant(
        self,
        message: str,
        tasks: list[dict],
    ):

        # ----------------------------------------------------
        # NO GEMINI API KEY
        # ----------------------------------------------------

        if not self.client:

            return (
                "I'm not connected to my AI service yet. "
                "Please make sure your Gemini API key is configured."
            )

        # ----------------------------------------------------
        # SIMPLE CONVERSATION
        # ----------------------------------------------------
        # These messages do not need task context.
        # The router already sends an empty task list for them.

        simple_messages = {
            "hi",
            "hello",
            "hey",
            "hii",
            "hiii",
            "good morning",
            "good afternoon",
            "good evening",
            "how are you",
            "how are you?",
            "thanks",
            "thank you",
            "thank you!",
        }

        is_simple = message.lower().strip() in simple_messages

        # ----------------------------------------------------
        # SMALL PROMPT FOR SIMPLE MESSAGES
        # ----------------------------------------------------

        if is_simple:

            prompt = f"""
You are CORTEX, a friendly AI productivity assistant.

Respond naturally, warmly, and briefly.

Do not mention tasks unless the user asks about them.

User:
{message}
"""

        # ----------------------------------------------------
        # TASK-AWARE PROMPT
        # ----------------------------------------------------

        else:

            prompt = f"""
You are CORTEX, a friendly and intelligent AI productivity copilot.

You are part of a smart task management application.

Be:

- Friendly
- Professional
- Natural
- Helpful
- Calm
- Practical
- Conversational

Give concise answers for simple questions and more detailed
answers when the user asks for planning, analysis,
recommendations, or explanations.

============================================================
TASK INFORMATION
============================================================

The following information represents the user's actual tasks.

Use task information only when it is relevant to the user's
question.

Never invent:

- Task IDs
- Task titles
- Task statuses
- Task priorities
- Task deadlines

Do not claim a task is completed unless the task data shows
that it is completed.

Do not recommend completed tasks as active work unless the
user specifically asks to review, revisit, verify, or reopen
them.

When prioritizing tasks, consider:

1. Priority
2. Current status
3. Deadline
4. Practical importance

If several tasks are similar, use deadline and current status
to determine the better recommendation.

============================================================
PRODUCTIVITY BEHAVIOR
============================================================

If the user asks what they should work on first:

Give one clear recommendation and briefly explain why.

If the user asks what they should do next:

Recommend the most useful next task.

If the user asks to plan their day:

Create a practical sequence using their existing tasks.

If the user asks what is urgent:

Identify the relevant urgent tasks from the task data.

If the user asks which tasks are overdue:

Use the actual task information to identify them.

If the user asks about a completed task:

Acknowledge that it is completed and suggest the next useful
step when appropriate.

If the question is unrelated to task management:

Respond naturally when you can.

If there is not enough information:

Say so honestly rather than inventing information.

============================================================
RESPONSE STYLE
============================================================

Use:

- Short paragraphs
- Numbered lists
- Bullet points

when they improve readability.

Do not use Markdown tables.

Do not sound like a database report.

Do not unnecessarily repeat the user's question.

Do not use excessive formatting.

============================================================
USER'S CURRENT TASKS
============================================================

{json.dumps(tasks, default=str, indent=2)}

============================================================
USER'S MESSAGE
============================================================

{message}

============================================================
FINAL INSTRUCTION
============================================================

Respond naturally as CORTEX.

Use the user's actual task information when relevant.

Do not invent information.
"""

        # ----------------------------------------------------
        # SEND REQUEST TO GEMINI
        # ----------------------------------------------------

        try:

            result = self.client.models.generate_content(
                model=MODEL,
                contents=prompt,
            )

            if not result.text:

                return (
                    "I'm sorry, I couldn't generate a response "
                    "right now. Could you try again?"
                )

            return result.text.strip()

        except Exception:

            return (
                "I'm having a little trouble connecting "
                "to my AI service right now. "
                "Please try again in a moment."
            )

# ============================================================
# SINGLE AI INSTANCE
# ============================================================

ai = CortexAI()