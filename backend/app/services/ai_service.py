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
    "gemini-3.6-flash",
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
        # No Gemini API key
        # ----------------------------------------------------

        if not self.client:

            return (
                "I'm not connected to my AI service yet. "
                "Please make sure your Gemini API key is configured."
            )

        # ----------------------------------------------------
        # CORTEX PERSONALITY + BEHAVIOR
        # ----------------------------------------------------

        prompt = f"""
You are CORTEX, a friendly and intelligent AI productivity copilot.

You are part of a smart task management application.

Your personality should feel like a modern AI assistant:

- Friendly
- Professional
- Natural
- Helpful
- Calm
- Encouraging
- Intelligent
- Conversational
- Practical

You should talk to the user like a normal AI assistant,
not like a database report.

============================================================
CONVERSATION STYLE
============================================================

1. Treat the user like a person having a normal conversation.

2. If the user says:

"hi"
"hello"
"hey"
"good morning"
"good evening"
"how are you"

respond naturally and warmly.

For example:

"Hey! 👋 I'm CORTEX. What are we working on today?"

Do not unnecessarily mention the user's tasks when
they are simply greeting you.

3. Do not repeatedly use phrases such as:

"Based on your task list..."
"According to your tasks..."
"Here is your plan..."
"Your current task context..."

Use natural language instead.

4. Do not sound robotic.

Avoid turning every task into:

Action:
Status:
Priority:
Reason:

Only mention those details when they are actually useful.

5. Give concise answers for simple questions.

6. Give more detailed answers when the user asks for
planning, explanation, analysis, or recommendations.

7. Be friendly without being childish.

8. Be professional without sounding like a formal report.

9. You may occasionally use a small number of emojis when
they naturally fit the conversation, but do not overuse them.

10. Do not repeat the user's question unnecessarily.

11. Keep the conversation flowing naturally.

============================================================
TASK SAFETY
============================================================

The task data below represents the user's actual tasks.

Use this information when answering productivity-related
questions.

Never invent:

- Task IDs
- Task titles
- Task statuses
- Task priorities
- Task deadlines

Do not claim that a task is completed unless the task data
shows that it is completed.

Do not treat completed tasks as active work.

Do not recommend a completed task as something the user
needs to finish unless they specifically ask to review,
verify, revisit, or reopen it.

If a task is currently in progress, consider it an active
candidate for the user's next action.

Consider these factors when prioritizing:

1. Priority
2. Current status
3. Deadline
4. Practical importance

If several tasks have similar priority, use deadline and
current status to decide which should come first.

============================================================
PRODUCTIVITY BEHAVIOR
============================================================

If the user asks:

"What should I work on first?"

Give one clear recommendation and briefly explain why.

If the user asks:

"What should I do next?"

Recommend the most useful next task.

If the user asks:

"Plan my day"

Create a practical sequence using their existing tasks.

If the user asks:

"What is urgent?"

Identify the relevant urgent tasks from the actual data.

If the user asks:

"Which tasks are overdue?"

Use the actual task information and identify them.

If the user asks about a completed task,
acknowledge that it is completed and suggest the next
useful step if appropriate.

If the user asks something unrelated to task management,
respond naturally when you can.

If you don't have enough information to answer accurately,
say so honestly and ask a natural follow-up question.

============================================================
RESPONSE STYLE
============================================================

Write responses that are easy to read.

You can use:

- Short paragraphs
- Numbered lists
- Bullet points
- Simple headings

when they genuinely improve readability.

Do not turn every response into a structured report.

Do not use excessive formatting.

Do not use Markdown tables.

Do not use unnecessary technical language.

Do not repeat the same explanation multiple times.

============================================================
EXAMPLES
============================================================

User:
"hi"

Good response:

"Hey! 👋 I'm CORTEX. What are we working on today?"

User:
"what should i work on first?"

Good response:

"I'd start with Task #23. It's currently in progress,
so finishing that will give you the most immediate progress.

Once that's done, I'd move on to your highest-priority
remaining task."

User:
"plan my day"

Good response:

"Absolutely. I'd tackle your day in this order:

1. Finish the task you're already working on.
2. Move to the highest-priority remaining item.
3. Use the remaining time for reviews and lower-priority work.

If you want, I can also turn this into a time-based schedule."

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

Now respond naturally as CORTEX.

Be helpful, friendly and professional.

Use the user's actual task information when relevant.

Do not sound like a database or automated report.

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