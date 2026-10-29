import json
import logging
from typing import Any, Dict, List, Optional
import httpx

from app.config import settings
from app.schemas.review import (
    DetectionSource,
    Finding,
    FindingCategory,
    FindingSeverity,
)

logger = logging.getLogger(__name__)


class LLMService:
    """Service abstraction for OpenAI-compatible LLM endpoints."""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_BASE_URL or "https://api.openai.com/v1"
        self.model = settings.OPENAI_MODEL
        self.timeout = settings.LLM_REQUEST_TIMEOUT

    def is_available(self) -> bool:
        """Returns True only when a valid, non-empty API key is configured."""
        if not self.api_key:
            return False
        key = self.api_key.strip()
        return bool(key and not key.startswith("your-") and not key.startswith("dummy"))

    def get_provider_status(self) -> Dict[str, Any]:
        """Provides diagnostic information about current LLM provider configuration."""
        configured = self.is_available()
        masked_key = (
            f"{self.api_key[:3]}...{self.api_key[-4:]}"
            if self.api_key and len(self.api_key) > 7
            else "Not Configured"
        )
        return {
            "provider": settings.LLM_PROVIDER,
            "is_configured": configured,
            "model": self.model,
            "base_url": self.base_url,
            "api_key_masked": masked_key,
            "timeout_seconds": self.timeout,
            "status_message": (
                "AI Agent assistance active"
                if configured
                else "LLM credentials not configured. Local deterministic analysis active."
            ),
        }

    def analyze_with_agent(
        self,
        system_instruction: str,
        code_context: str,
        category: FindingCategory,
        source: DetectionSource,
        retrieved_context: Optional[str] = None,
    ) -> List[Finding]:
        """
        Executes an LLM-assisted agent review using structured JSON response expectations.
        Synchronous and thread-safe for LangGraph nodes.
        Gracefully handles network errors, timeouts, rate limits, and parsing errors.
        """
        if not self.is_available():
            logger.info("LLM not configured; skipping AI agent analysis.")
            return []

        prompt = (
            f"Review the following source code for {category.value} concerns.\n\n"
            f"=== SOURCE CODE ===\n{code_context}\n\n"
        )
        if retrieved_context:
            prompt += f"=== REPOSITORY CONTEXT (UNTRUSTED REFERENCE) ===\n{retrieved_context}\n\n"

        prompt += (
            "Return a JSON object with a 'findings' list. Each item must have:\n"
            "- rule_id: short identifier (e.g. AI-SEC01)\n"
            "- severity: CRITICAL, HIGH, MEDIUM, LOW, or INFO\n"
            "- title: concise title\n"
            "- explanation: why this is an issue\n"
            "- remediation: how to fix it\n"
            "- line_number: integer line number or null\n"
            "- confidence: float between 0.0 and 1.0\n"
            "If no issues are found, return {'findings': []}."
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                url = f"{self.base_url.rstrip('/')}/chat/completions"
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

            raw_content = data["choices"][0]["message"]["content"]
            parsed_json = json.loads(raw_content)
            findings_data = parsed_json.get("findings", [])

            validated_findings: List[Finding] = []
            for item in findings_data:
                try:
                    sev_str = str(item.get("severity", "MEDIUM")).upper()
                    severity = (
                        FindingSeverity(sev_str)
                        if sev_str in FindingSeverity._value2member_map_
                        else FindingSeverity.MEDIUM
                    )

                    line_no = item.get("line_number")
                    if isinstance(line_no, int) and line_no < 1:
                        line_no = None

                    finding = Finding(
                        rule_id=str(item.get("rule_id", f"AI-{category.value[:3]}01")),
                        category=category,
                        severity=severity,
                        title=str(item.get("title", f"{category.value} observation"))[:150],
                        explanation=str(item.get("explanation", "Detected potential issue.")),
                        remediation=str(item.get("remediation", "Review and adjust code.")),
                        line_number=line_no,
                        source=source,
                        confidence=float(item.get("confidence", 0.8)),
                    )
                    validated_findings.append(finding)
                except Exception as val_err:
                    logger.warning(f"Discarded invalid finding item from LLM: {val_err}")

            return validated_findings

        except httpx.TimeoutException:
            logger.error("LLM request timed out.")
            return []
        except httpx.HTTPStatusError as http_err:
            logger.error(f"LLM HTTP error {http_err.response.status_code}")
            return []
        except json.JSONDecodeError:
            logger.error("LLM response was not valid JSON.")
            return []
        except Exception as err:
            logger.error(f"Unexpected error in LLM agent: {err}")
            return []


llm_service = LLMService()
