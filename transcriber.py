"""
faster-whisper로 오디오 청크를 텍스트로 변환.
모델/장치는 .env에서 결정.
"""
import os
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
PROMPTS_DIR = Path(__file__).parent / "prompts"


class Transcriber:
    def __init__(self, whisper_lang: str | None = None):
        model_name = os.getenv("WHISPER_MODEL", "small")
        device = os.getenv("WHISPER_DEVICE", "cuda")
        compute_type = os.getenv("WHISPER_COMPUTE", "float16") if device == "cuda" else "int8"

        # 금융 도메인 초기 프롬프트 로드 (언어 선택)
        if whisper_lang is None:
            whisper_lang = os.getenv("WHISPER_LANG", "ko")
        prompt_file = f"whisper-initial-{whisper_lang}.md"
        initial_prompt_path = PROMPTS_DIR / prompt_file
        self._initial_prompt = initial_prompt_path.read_text(encoding="utf-8") if initial_prompt_path.exists() else None

        print(f"[Whisper] 모델 로딩: {model_name} / {device} / {compute_type}")
        self._model = WhisperModel(model_name, device=device, compute_type=compute_type)
        print("[Whisper] 모델 로딩 완료")

    def transcribe(self, audio: np.ndarray) -> str:
        """float32 numpy 배열 → 텍스트."""
        if audio is None or len(audio) < SAMPLE_RATE:  # 1초 미만이면 스킵
            return ""
        # 무음 청크 스킵 (최대 절대값이very small)
        if np.max(np.abs(audio)) < 0.001:
            return ""
        segments, _ = self._model.transcribe(
            audio,
            language=None,        # 자동 감지 (한/영 혼합 대응)
            vad_filter=False,     # 어닝 콜은 음성이 계속되어 VAD 비활성화
            initial_prompt=self._initial_prompt,
        )
        return " ".join(seg.text.strip() for seg in segments).strip()
