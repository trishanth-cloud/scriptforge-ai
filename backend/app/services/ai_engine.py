"""
ScriptForge AI — AI Engine Service
Gemini API integration with mock-mode fallback.
"""

import json
import logging
import re

from app.config import settings

logger = logging.getLogger(__name__)


class AIEngine:
    """Wrapper around Google Gemini API for all AI operations."""

    def __init__(self) -> None:
        self.mock_mode = False
        self.client = None
        self.model = settings.AI_MODEL

        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set — running in mock mode")
            self.mock_mode = True
        else:
            try:
                from google import genai
                self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
                logger.info("AIEngine initialised with model %s", self.model)
            except Exception as exc:
                logger.error("Failed to initialise Gemini client: %s", exc)
                self.mock_mode = True

    # ── Public API ──────────────────────────────────────────────

    async def analyze(self, content: str, file_type: str) -> dict:
        """Analyze content and return structured analysis."""
        if self.mock_mode:
            return self._mock_analyze(content, file_type)

        prompt = (
            "You are a code-generation assistant. Analyze the following content and return "
            "a JSON object (no markdown fences) with these keys:\n"
            '  "summary": short summary of what the content asks for,\n'
            '  "extracted_instructions": list of step-by-step instructions found,\n'
            '  "detected_variables": list of variable names or parameters detected,\n'
            '  "dependencies": list of libraries or external dependencies needed,\n'
            '  "ambiguities": list of anything unclear in the instructions,\n'
            '  "task_type": one of [data_transformation, automation, web_scraping, file_processing, '
            "api_integration, database_operation, system_administration, data_analysis, "
            "web_application, utility_script, other],\n"
            '  "recommended_language": best programming language for this task,\n'
            '  "confidence": float 0-1 for how confident you are,\n'
            '  "explanation": brief explanation of your choices.\n\n'
            f"File type: {file_type}\n\n"
            f"Content:\n{content[:6000]}"
        )
        try:
            return await self._call_json(prompt)
        except Exception as exc:
            logger.warning("AI analyze call failed (%s); using fallback analysis.", exc)
            return self._mock_analyze(content, file_type)

    async def plan(self, analysis: dict, task_type: str, language: str) -> dict:
        """Generate an execution plan."""
        if self.mock_mode:
            return self._mock_plan(analysis, task_type, language)

        prompt = (
            "You are a code-generation planner. Given the analysis below, produce a JSON object "
            "(no markdown fences) with:\n"
            '  "steps": list of step-by-step actions to implement the script,\n'
            f'  "language": "{language}",\n'
            '  "estimated_complexity": "low" | "medium" | "high",\n'
            '  "requires_approval": true,\n'
            '  "warnings": list of potential issues,\n'
            '  "description": one-paragraph description of the plan.\n\n'
            f"Task type: {task_type}\nLanguage: {language}\n\n"
            f"Analysis:\n{json.dumps(analysis, indent=2)[:4000]}"
        )
        try:
            return await self._call_json(prompt)
        except Exception as exc:
            logger.warning("AI plan call failed (%s); using fallback plan.", exc)
            return self._mock_plan(analysis, task_type, language)

    async def generate(
        self, content: str, analysis: dict, plan: dict, language: str
    ) -> str:
        """Generate script code. Returns the raw code string."""
        if self.mock_mode:
            return self._mock_generate(analysis, language)

        prompt = (
            f"You are an expert {language} developer. Generate a complete, production-quality "
            f"{language} script based on the following.\n\n"
            "Requirements:\n"
            "- Clean, readable code with meaningful comments\n"
            "- Proper error handling (try/except or try/catch)\n"
            "- Modular structure with functions\n"
            "- Include a main entry point\n"
            "- Do NOT include markdown fences — return only the code\n\n"
            f"Plan:\n{json.dumps(plan, indent=2)[:3000]}\n\n"
            f"Analysis:\n{json.dumps(analysis, indent=2)[:3000]}\n\n"
            f"Original content:\n{content[:3000]}"
        )
        try:
            return await self._call_text(prompt)
        except Exception as exc:
            logger.warning("AI generate call failed (%s); using fallback generation.", exc)
            return self._mock_generate(analysis, language)

    async def debug(self, script: str, error: str, language: str) -> dict:
        """Analyze an error and return a fix."""
        if self.mock_mode:
            return self._mock_debug(script, error, language)

        prompt = (
            f"You are a {language} debugging expert. A script failed with the error below.\n"
            "Return a JSON object (no markdown fences) with:\n"
            '  "diagnosis": what went wrong,\n'
            '  "fix_applied": what you changed,\n'
            '  "revised_script": the complete fixed script (no fences),\n'
            '  "resolved": true if you are confident the fix works.\n\n'
            f"Error:\n{error[:2000]}\n\n"
            f"Script:\n{script[:5000]}"
        )
        try:
            return await self._call_json(prompt)
        except Exception as exc:
            logger.warning("AI debug call failed (%s); using fallback debug.", exc)
            return self._mock_debug(script, error, language)

    async def explain(self, script: str) -> str:
        """Generate a human-readable explanation of a script."""
        if self.mock_mode:
            return "This script performs the operations described in the original task."

        prompt = (
            "Explain the following script in clear, non-technical language. "
            "Describe what it does step by step.\n\n"
            f"{script[:6000]}"
        )
        return await self._call_text(prompt)

    # ── Internal helpers ────────────────────────────────────────

    async def _call_text(self, prompt: str) -> str:
        """Call Gemini and return plain text with automatic model fallback."""
        candidate_models = [self.model, "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
        # Deduplicate while preserving order
        seen = set()
        models_to_try = [m for m in candidate_models if not (m in seen or seen.add(m))]

        last_error = None
        for candidate in models_to_try:
            try:
                response = self.client.models.generate_content(
                    model=candidate,
                    contents=prompt,
                )
                if response and response.text:
                    return response.text
            except Exception as exc:
                last_error = exc
                logger.warning("Gemini model '%s' failed (%s), trying fallback...", candidate, exc)

        logger.error("All Gemini candidate models failed: %s", last_error)
        raise last_error or RuntimeError("Gemini content generation failed.")

    async def _call_json(self, prompt: str) -> dict:
        """Call Gemini and parse JSON from the response."""
        text = await self._call_text(prompt)
        # Try to extract JSON from the response
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON block in text
            match = re.search(r"\{[\s\S]*\}", text)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            logger.warning("Failed to parse JSON from Gemini response, returning raw text")
            return {"raw_response": text}

    # ── Mock responses ──────────────────────────────────────────

    def _mock_analyze(self, content: str, file_type: str) -> dict:
        lines = content.strip().splitlines()
        return {
            "summary": f"Content with {len(lines)} lines of type '{file_type}'.",
            "extracted_instructions": lines[:5] if lines else ["No instructions found"],
            "detected_variables": [],
            "dependencies": [],
            "ambiguities": ["Running in mock mode — analysis is approximate."],
            "task_type": "utility_script",
            "recommended_language": "python",
            "confidence": 0.5,
            "explanation": "Mock analysis based on content length and type.",
        }

    def _mock_plan(self, analysis: dict, task_type: str, language: str) -> dict:
        return {
            "steps": [
                "Read and parse input data",
                "Process according to instructions",
                "Validate output",
                "Write results",
            ],
            "language": language,
            "estimated_complexity": "medium",
            "requires_approval": True,
            "warnings": ["This plan was generated in mock mode."],
            "description": f"A {task_type} task implemented in {language}.",
        }

    def _mock_generate(self, analysis: dict, language: str) -> str:
        summary = analysis.get("summary", "Perform the requested task")
        instructions = analysis.get("extracted_instructions", [])
        steps = "\n".join(f"    # Step: {s}" for s in instructions) if instructions else "    # TODO: implement task"

        if language == "python":
            return (
                '#!/usr/bin/env python3\n'
                f'"""ScriptForge AI — Generated Script\n{summary}\n"""\n\n'
                'import sys\n\n\n'
                'def main():\n'
                f'    """Main entry point."""\n'
                f'{steps}\n'
                '    print("Task completed successfully.")\n\n\n'
                'if __name__ == "__main__":\n'
                '    try:\n'
                '        main()\n'
                '    except Exception as e:\n'
                '        print(f"Error: {e}", file=sys.stderr)\n'
                '        sys.exit(1)\n'
            )
        elif language == "javascript":
            return (
                f"// ScriptForge AI — Generated Script\n// {summary}\n\n"
                "function main() {\n"
                f"  // TODO: implement\n"
                '  console.log("Task completed successfully.");\n'
                "}\n\nmain();\n"
            )
        elif language == "bash":
            return (
                "#!/usr/bin/env bash\n"
                f"# ScriptForge AI — Generated Script\n# {summary}\n\n"
                "set -euo pipefail\n\n"
                "main() {\n"
                "  # TODO: implement\n"
                '  echo "Task completed successfully."\n'
                "}\n\nmain\n"
            )
        else:
            return f"# ScriptForge AI — Generated {language} Script\n# {summary}\n# TODO: implement\n"

    def _mock_debug(self, script: str, error: str, language: str) -> dict:
        return {
            "diagnosis": f"Mock diagnosis: {error[:200]}",
            "fix_applied": "Added basic error handling (mock fix).",
            "revised_script": script,
            "resolved": False,
        }
