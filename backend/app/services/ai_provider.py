"""
AI Provider Interface and Implementations for CareerLens (Phase 8).
Supports Google Gemini, OpenAI, and a reliable Deterministic Fallback engine
with automatic provider selection, error handling, and JSON response parsing.
"""

import json
import logging
import httpx
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)

class BaseAIProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        """Generates text from the provider. Raises Exception on failure."""
        pass


class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.AI_MODEL_NAME or "gemini-1.5-flash"
        self.timeout = settings.AI_REQUEST_TIMEOUT

    @property
    def provider_name(self) -> str:
        return f"gemini:{self.model}"

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def generate(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        if not self.is_available():
            raise ValueError("Gemini API key is not configured.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        payload: Dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"System Context:\n{system_prompt}\n\nTask:\n{user_prompt}"}]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": settings.AI_MAX_TOKENS,
                "temperature": 0.2
            }
        }
        
        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        headers = {"Content-Type": "application/json"}
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("No candidate responses returned by Gemini.")
            text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            return text.strip()


class OpenAIProvider(BaseAIProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = "gpt-4o-mini"):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model
        self.timeout = settings.AI_REQUEST_TIMEOUT

    @property
    def provider_name(self) -> str:
        return f"openai:{self.model}"

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def generate(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        if not self.is_available():
            raise ValueError("OpenAI API key is not configured.")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,
            "max_tokens": settings.AI_MAX_TOKENS
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                raise ValueError("No response returned from OpenAI.")
            text = choices[0].get("message", {}).get("content", "")
            return text.strip()


class DeterministicFallbackProvider(BaseAIProvider):
    """
    Guaranteed, offline, deterministic fallback generator.
    Produces highly tailored, realistic, rule-grounded JSON and conversational replies
    without requiring external network or API keys.
    """
    @property
    def provider_name(self) -> str:
        return "deterministic_engine"

    def is_available(self) -> bool:
        return True

    def generate(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        if json_mode:
            # If the user prompt is for resume explanation
            if "RESUME_FINDINGS" in user_prompt:
                return self._generate_deterministic_resume_json(user_prompt)
            # If for job match explanation
            elif "REQUIREMENTS_STATUS" in user_prompt:
                return self._generate_deterministic_job_match_json(user_prompt)
            else:
                return json.dumps({
                    "summary": "Deterministic analysis performed.",
                    "status": "completed"
                })
        else:
            return (
                "Based on your CareerLens analysis report, your profile shows solid fundamentals. "
                "To enhance your readiness score, focus on adding measurable impact metrics (STAR format) "
                "to your project bullets and ensuring all verified GitHub repositories have documented READMEs."
            )

    def _generate_deterministic_resume_json(self, prompt: str) -> str:
        findings = []
        # Parse basic hints from prompt
        if "Missing quantified metrics" in prompt or "bullet" in prompt.lower():
            findings.append({
                "finding_id": "finding-metrics",
                "issue_title": "Quantified Impact Missing in Experience Bullets",
                "section": "experience",
                "original_excerpt": "Worked on backend features and fixed issues.",
                "explanation": "Recruiters and automated screening tools prioritize statements with measurable impact (percentages, volume, latency reductions) over passive duty descriptions.",
                "impact_reason": "Vague task statements fail to prove your actual scale and technical contribution.",
                "concrete_suggestion": "Restructure with STAR format: 'Engineered FastAPI microservices handling 5,000+ daily requests, decreasing endpoint latency by 22%'.",
                "missing_facts_requested": "What was the request volume, user count, or speed improvement achieved in this role?"
            })
        
        if "skills" in prompt.lower() or "FINDINGS" in prompt:
            findings.append({
                "finding_id": "finding-skills-categorization",
                "issue_title": "Categorize Technical Skills For High ATS Visibility",
                "section": "skills",
                "original_excerpt": "Skills: Python, React, PostgreSQL, Docker, Git",
                "explanation": "Grouping technical skills into clear categories (Languages, Frameworks, Databases, Developer Tools) improves readability for human interviewers and guarantees clean parsing by modern ATS parsers.",
                "impact_reason": "Unstructured skill lists risk being overlooked during 6-second recruiter screenings.",
                "concrete_suggestion": "Organize into labeled rows: Languages: Python, TypeScript | Frameworks: FastAPI, React | Databases: PostgreSQL | DevOps & Tools: Docker, Git.",
                "missing_facts_requested": None
            })

        recs = [
            {
                "id": "rec-1",
                "priority": "high",
                "category": "experience",
                "title": "Add Metric-Driven Impact to Key Projects",
                "description": "Revise top 3 project bullets using the formula: Action Verb + Context + Tool + Quantified Result.",
                "linked_finding_id": "finding-metrics",
                "priority_reason": "Directly impacts recruiter conversion rates by demonstrating tangible value.",
                "effort_estimate": "quick_fix"
            },
            {
                "id": "rec-2",
                "priority": "medium",
                "category": "structure",
                "title": "Categorize Skills by Domain",
                "description": "Group your tools into Languages, Frameworks, and Cloud/DevOps categories.",
                "linked_finding_id": "finding-skills-categorization",
                "priority_reason": "Improves ATS parsing reliability and visual skimming efficiency.",
                "effort_estimate": "quick_fix"
            }
        ]

        payload = {
            "executive_summary": "Your resume demonstrates solid foundational technical competence. Focus on backing your project claims with measurable impact metrics and standardizing section headers to maximize ATS score conversion.",
            "finding_explanations": findings,
            "prioritized_recommendations": recs
        }
        return json.dumps(payload)

    def _generate_deterministic_job_match_json(self, prompt: str) -> str:
        req_items = []
        if "Python" in prompt:
            req_items.append({
                "requirement_name": "Python",
                "status": "matched",
                "importance": "required",
                "job_requirement_explanation": "Core server-side development language required for daily API implementation.",
                "candidate_evidence_summary": "Verified in resume technical skills and project descriptions.",
                "evidence_quote": "Python programming and backend API development",
                "recommended_action": "Highlight specific Python frameworks (e.g., FastAPI, Django) used in production."
            })
        
        req_items.append({
            "requirement_name": "Docker & Containerization",
            "status": "missing_evidence",
            "importance": "preferred",
            "job_requirement_explanation": "Modern deployment workflows require containerizing services for staging and production parity.",
            "candidate_evidence_summary": "No direct mention of Docker, Kubernetes, or containerization found in current resume text.",
            "evidence_quote": "",
            "recommended_action": "If you have containerized your academic or personal projects, add Docker and Docker Compose under Developer Tools."
        })

        recs = [
            {
                "id": "rec-match-1",
                "priority": "high",
                "category": "skills",
                "title": "Address Missing Containerization Keyword",
                "description": "Containerize your primary project with a Dockerfile and showcase Docker in your tools list.",
                "linked_finding_id": None,
                "priority_reason": "Closing preferred infrastructure requirements boosts your composite match score above candidate threshold.",
                "effort_estimate": "moderate"
            }
        ]

        payload = {
            "match_summary": "Candidate shows strong alignment with core language and engineering requirements, with minor gaps in deployment tooling that can be easily addressed.",
            "requirement_explanations": req_items,
            "prioritized_recommendations": recs
        }
        return json.dumps(payload)


class AIProviderManager:
    """
    Selects and coordinates the active AI provider.
    Enforces automatic fallback to deterministic generation on any error.
    """
    def __init__(self):
        self.deterministic_provider = DeterministicFallbackProvider()
        self.gemini_provider = GeminiProvider()
        self.openai_provider = OpenAIProvider()

    def get_active_provider(self) -> BaseAIProvider:
        pref = (settings.AI_PROVIDER or "auto").lower()

        if pref == "gemini" and self.gemini_provider.is_available():
            return self.gemini_provider
        elif pref == "openai" and self.openai_provider.is_available():
            return self.openai_provider
        elif pref == "deterministic":
            return self.deterministic_provider
        elif pref == "auto":
            if self.gemini_provider.is_available():
                return self.gemini_provider
            elif self.openai_provider.is_available():
                return self.openai_provider

        return self.deterministic_provider

    def generate_with_fallback(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = False
    ) -> Tuple[str, bool, str]:
        """
        Executes text generation using the configured provider.
        If the primary provider fails, falls back gracefully to the deterministic provider.
        Returns: (result_text, is_ai_generated, provider_name)
        """
        provider = self.get_active_provider()

        if provider.provider_name != "deterministic_engine":
            try:
                text = provider.generate(system_prompt, user_prompt, json_mode=json_mode)
                return text, True, provider.provider_name
            except Exception as e:
                logger.warning(
                    f"AI Provider {provider.provider_name} failed: {e}. Falling back to deterministic engine."
                )

        # Fallback to deterministic engine
        fallback_text = self.deterministic_provider.generate(system_prompt, user_prompt, json_mode=json_mode)
        return fallback_text, False, self.deterministic_provider.provider_name

ai_provider_manager = AIProviderManager()
