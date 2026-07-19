"""
faster-whisper로 오디오 청크를 텍스트로 변환.
모델/장치는 .env에서 결정.
"""
import os

import numpy as np
from faster_whisper import WhisperModel


class Transcriber:
    def __init__(self):
        model_name = os.getenv("WHISPER_MODEL", "small")
        device = os.getenv("WHISPER_DEVICE", "cuda")
        compute_type = os.getenv("WHISPER_COMPUTE", "float16") if device == "cuda" else "int8"

        print(f"[Whisper] 모델 로딩: {model_name} / {device} / {compute_type}")
        self._model = WhisperModel(model_name, device=device, compute_type=compute_type)
        print("[Whisper] 모델 로딩 완료")

    def transcribe(self, audio: np.ndarray) -> str:
        """float32 numpy 배열 → 텍스트."""
        segments, _ = self._model.transcribe(
            audio,
            language=None,        # 자동 감지 (한/영 혼합 대응)
            vad_filter=True,      # 무음 구간 스킵
            vad_parameters={"min_silence_duration_ms": 500},
        )
        return " ".join(seg.text.strip() for seg in segments).strip()
