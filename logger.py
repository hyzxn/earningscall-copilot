"""
세션별 로그 파일 3개를 생성한다.
  session_YYYYMMDD_HHMMSS_cc.txt          - 실시간 자막
  session_YYYYMMDD_HHMMSS_ai_overview.txt - AI 요약
  session_YYYYMMDD_HHMMSS_indicator.txt   - 주요 지표
"""
import json
import os
from datetime import datetime
from pathlib import Path


class SessionLogger:
    def __init__(self):
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._cc        = log_dir / f"session_{ts}_cc.txt"
        self._overview  = log_dir / f"session_{ts}_ai_overview.txt"
        self._indicator = log_dir / f"session_{ts}_indicator.txt"

        # 헤더 초기화
        self._write(self._cc,        f"[EarningsCall Copilot] 세션 시작: {datetime.now()}\n{'='*60}\n")
        self._write(self._overview,  f"[EarningsCall Copilot] AI 요약 로그: {datetime.now()}\n{'='*60}\n")
        self._write(self._indicator, f"[EarningsCall Copilot] 지표 추출 로그: {datetime.now()}\n{'='*60}\n")

    def _write(self, path: Path, text: str, mode="w"):
        try:
            with open(path, mode, encoding="utf-8") as f:
                f.write(text)
        except OSError:
            pass

    def log_cc(self, text: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self._write(self._cc, f"[{ts}] {text}\n", mode="a")

    def log_overview(self, text: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self._write(self._overview, f"\n[{ts}]\n{text}\n", mode="a")

    def log_indicator(self, data: dict):
        ts = datetime.now().strftime("%H:%M:%S")
        self._write(self._indicator, f"\n[{ts}]\n{json.dumps(data, ensure_ascii=False, indent=2)}\n", mode="a")

    def close(self):
        footer = f"\n{'='*60}\n[세션 종료] {datetime.now()}\n"
        for path in [self._cc, self._overview, self._indicator]:
            self._write(path, footer, mode="a")
