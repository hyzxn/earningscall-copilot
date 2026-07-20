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
import re
from pathlib import Path
from string import Template
import httpx

PROMPTS_DIR = Path(__file__).parent / "prompts"


# --- 백엔드 설정 ---
BACKEND = os.getenv("ANALYZER_BACKEND", "ollama")

# Gemini 설정
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Ollama 설정
OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:9b")


def _load_prompt(name: str) -> str:
    """prompts/ 디렉토리에서 프롬프트 파일을 읽는다."""
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


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
        url = f"{GEMINI_BASE}/{self._model}:generateContent"
        headers = {"x-goog-api-key": self._api_key}
        body = {"contents": [{"parts": [{"text": prompt}]}]}
        resp = httpx.post(url, json=body, headers=headers, timeout=100)
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
        prompt = Template(_load_prompt("summary.md")).substitute(transcript=transcript[-4000:])
        return self._call(prompt)

    def get_metrics(self, transcript: str) -> dict:
        if not transcript.strip():
            return {}
        prompt = Template(_load_prompt("metrics.md")).substitute(transcript=transcript[-6000:])
        raw = self._call(prompt)
        raw = raw.strip()
        # JSON 블록 추출: 첫 번째 { ~ 마지막 } 사이
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            raw = raw[start : end + 1]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"parse_error": raw[:200]}
