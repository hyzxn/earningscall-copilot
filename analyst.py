"""
Gemini API 또는 Ollama 로컬 모델로 누적 스크립트를 분석한다.
- summary: 핵심 요약
- metrics: 주요 지표 구조화 추출

환경변수 ANALYZER_BACKEND로 백엔드 선택:
  - gemini: Google Gemini API 사용
  - ollama: Ollama 로컬 모델 사용 (기본값)
"""
import os
import json
import httpx


# --- 백엔드 설정 ---
BACKEND = os.getenv("ANALYZER_BACKEND", "ollama")

# Gemini 설정
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Ollama 설정
OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:9b")


SUMMARY_PROMPT = """You are a professional equity research analyst.
Analyze the following earnings call transcript excerpt and provide:
1. Key summary (3-5 bullet points, Korean)
2. Management tone assessment (긍정/중립/부정 + brief reason)

Transcript:
{transcript}

Respond in Korean. Be concise and factual."""

METRICS_PROMPT = """You are a financial data extraction specialist.
Extract structured financial metrics from this earnings call transcript.

Transcript:
{transcript}

Return ONLY valid JSON (no markdown, no explanation):
{{
  "eps": {{"actual": null, "consensus": null, "beat_miss": null}},
  "revenue": {{"actual": null, "unit": null, "yoy_growth": null}},
  "operating_margin": null,
  "guidance": {{
    "next_quarter": null,
    "full_year": null
  }},
  "key_topics": [],
  "management_tone": null,
  "notable_quotes": []
}}

Use null for any field not mentioned in the transcript.
For numbers, include units in the string (e.g. "$3.2B", "15.3%").
notable_quotes: max 2 items, each under 20 words."""


class Analyst:
    def __init__(self):
        self._backend = BACKEND

        if self._backend == "gemini":
            self._api_key = os.getenv("GEMINI_API_KEY", "")
            self._model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
            if not self._api_key:
                raise ValueError("GEMINI_API_KEY가 .env에 없습니다.")
        else:
            self._model = OLLAMA_MODEL

    # --- 백엔드별 _call 구현 ---

    def _call_gemini(self, prompt: str) -> str:
        url = f"{GEMINI_BASE}/{self._model}:generateContent?key={self._api_key}"
        body = {"contents": [{"parts": [{"text": prompt}]}]}
        resp = httpx.post(url, json=body, timeout=100)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    def _call_ollama(self, prompt: str) -> str:
        url = f"{OLLAMA_BASE}/api/chat"
        body = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        resp = httpx.post(url, json=body, timeout=100)
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"]

    def _call(self, prompt: str) -> str:
        if self._backend == "gemini":
            return self._call_gemini(prompt)
        return self._call_ollama(prompt)

    # --- 외부 인터페이스 (변경 없음) ---

    def get_summary(self, transcript: str) -> str:
        if not transcript.strip():
            return ""
        prompt = SUMMARY_PROMPT.format(transcript=transcript[-4000:])
        return self._call(prompt)

    def get_metrics(self, transcript: str) -> dict:
        if not transcript.strip():
            return {}
        prompt = METRICS_PROMPT.format(transcript=transcript[-6000:])
        raw = self._call(prompt)
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"parse_error": raw[:200]}
