import json
import os
import re

from google import genai


MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.7-flash",
)


class CortexAI:

    def __init__(self):

        key = os.getenv(
            "GEMINI_API_KEY"
        )

        self.client = (
            genai.Client(
                api_key=key
            )
            if key
            else None
        )

    # ========================================================
    # PARSE JSON FROM AI
    # ========================================================

    def _json(
        self,
        text: str,
    ):

        cleaned = re.sub(
            r"^```json\s*|^```\s*|\s*```$",
            "",
            text.strip(),
            flags=re.I,
        )

        try:
            return json.loads(cleaned)

        except json.JSONDecodeError:

            match = re.search(
                r"\{.*\}",
                cleaned,
                re.S,
            )

            return (
                json.loads(match.group(0))
                if match
                else None
            )

    # ========================================================
    # TASK ANALYSIS
    # ========================================================

    def analyze_task(
        self,
        title: str,
        description: str | None,
    ):

        if not self.client:

            return {
                "priority": "medium",
                "reason": (
                    "AI key is not configured; "
                    "using a safe default."
                ),
                "subtasks": [],
            }

        prompt = f"""
You are CORTEX, an AI productivity copilot.

Analyze the following task.

Return ONLY valid JSON with these keys:

priority
reason
subtasks

Priority MUST be exactly one of:

low
medium
high
urgent

Subtasks must be a short array of strings.

Title:
{title}

Description:
{description or ""}
"""

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

    # ========================================================
    # CORTEX AI ASSISTANT
    # ========================================================

    def assistant(
        self,
        message: str,
        tasks: list[dict],
    ):

        if not self.client:

            return (
                "CORTEX AI is available, "
                "but GEMINI_API_KEY is not "
                "configured yet."
            )

        prompt = f"""
You are CORTEX, a concise and practical
productivity assistant.

Use the user's real task context below.

Give actionable recommendations.
Do not invent tasks that are not present
unless the user explicitly asks you to create
or suggest new ones.

USER TASKS:
{json.dumps(tasks, default=str)}

USER REQUEST:
{message}
"""

        result = self.client.models.generate_content(
            model=MODEL,
            contents=prompt,
        )

        return result.text


# ============================================================
# SINGLE AI INSTANCE
# ============================================================

ai = CortexAI()