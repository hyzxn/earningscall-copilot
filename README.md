# EarningsCall Copilot

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/UI-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![Whisper](https://img.shields.io/badge/STT-Whisper-yellow)](https://github.com/SYSTRAN/faster-whisper)
[![Ollama](https://img.shields.io/badge/LLM-Ollama-white)](https://ollama.com/)

> 실시간 어닝 콜 전사 및 AI 분석 코파일럿 (Real-time earnings call transcription and AI analysis copilot)

## 주요 기능 (Features)

- **실시간 전사 (Real-time Transcription):** 컴퓨터 재생 오디오를 WASAPI Loopback으로 캡처하여 Whisper로 실시간 전사합니다.
  <details>
  <summary><b>전사 설정 (Transcription Settings)</b></summary>

  - **모델 선택:** tiny / base / small / medium / large-v3
  - **언어 선택:** 한국어 / 영어 프롬프트 분리 지원
  - **청크 단위:** 환경변수로 조절 가능 (기본 3초)

  </details>

- **AI 분석 (AI Analysis):** Gemini API 또는 Ollama 로컬 모델로 전사 텍스트를 분석합니다.
  - **요약 분석:** 핵심 요약 및 경영진 톤 평가
  - **지표 추출:** EPS, 매출, 가이던스 등 구조화된 재무 지표 추출
  - **백엔드 선택:** `ANALYZER_BACKEND` 환경변수로 Gemini / Ollama 전환 가능

- **키워드 하이라이팅 (Keyword Highlighting):** 긍정/부정 키워드를 실시간으로 강조 표시합니다.

- **전사 검색 (Transcript Search):** 전사 텍스트 내 키워드 검색 및 자동 스크롤을 지원합니다.

- **패널 토글 (Panel Toggle):** 실시간 자막, AI 요약, 주요 지표 패널을 개별적으로 표시하거나 숨길 수 있습니다.

## 요구 사항 (Requirements)

- **OS:** Windows 10 / 11
- **Language:** Python 3.11+ (uv 패키지 매니저 권장)
- **GPU:** NVIDIA GPU (권장)
- **LLM Engine:** [Ollama](https://ollama.com/) (로컬 백엔드 사용 시)
- **Core Dependencies:** `fastapi`, `uvicorn`, `faster-whisper`, `sounddevice`, `numpy`, `httpx`, `pywebview`, `torch`

## 설치 방법 (Installation)

1. **의존성 설치:**
   ```bash
   uv sync
   ```
2. **환경 변수 설정:** `.env.example`을 `.env`로 복사한 후 설정값을 채웁니다.
3. **Ollama 설치 (선택):** 로컬 LLM을 사용할 경우 Ollama를 설치하고 모델을 받아옵니다.
   ```bash
   ollama pull qwen3.5:9b
   ```
4. **실행:**
   ```bash
   run.bat
   ```

## 사용법 (Usage)

1. `run.bat`를 실행하면 UI 창이 열립니다.
2. 상단 드롭다운에서 한국어 또는 영어를 선택합니다.
3. 시작 버튼을 누르면 오디오 캡처 및 전사가 시작됩니다.
4. AI 분석은 설정된 주기에 따라 자동 실행되며, 즉시 분석 버튼으로 수동 실행할 수도 있습니다.

## 프로젝트 구조 (Project Structure)

```text
earningscall-copilot/
├── prompts/
│   ├── summary.md              # AI 요약 프롬프트
│   ├── metrics.md              # 지표 추출 프롬프트
│   ├── whisper-initial-ko.md   # Whisper 한국어 초기 프롬프트
│   └── whisper-initial-en.md   # Whisper 영어 초기 프롬프트
├── static/
│   └── index.html              # 프론트엔드 UI
├── main.py                     # FastAPI + WebSocket 오케스트레이션
├── analyst.py                  # AI 분석 모듈 (Gemini/Ollama)
├── transcriber.py              # Whisper 전사 모듈
├── audio.py                    # WASAPI Loopback 오디오 캡처
├── logger.py                   # 세션 로깅
├── run.bat                     # 실행 파일
├── pyproject.toml              # 프로젝트 의존성 및 uv 설정
├── .env.example                # 환경 설정 파일 예시
└── README.md                   # 프로젝트 설명 문서
```

## 환경 변수 (Environment Variables)

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `ANALYZER_BACKEND` | AI 백엔드 선택 (gemini / ollama) | `ollama` |
| `GEMINI_API_KEY` | Gemini API 키 | — |
| `GEMINI_MODEL` | Gemini 모델명 | `gemini-2.0-flash` |
| `OLLAMA_BASE` | Ollama 서버 URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama 모델명 | `qwen3.5:9b` |
| `WHISPER_MODEL` | Whisper 모델 (tiny/base/small/medium/large-v3) | `small` |
| `WHISPER_LANG` | Whisper 언어 (ko / en) | `ko` |
| `WHISPER_DEVICE` | 실행 장치 (cuda / cpu) | `cuda` |
| `CHUNK_SEC` | 오디오 청크 단위 (초) | `3` |
| `SUMMARY_INTERVAL_SEC` | AI 분석 주기 (초, 0=비활성화) | `0` |
| `AUDIO_GAIN` | 오디오 증폭 배율 | `1.0` |

---

## 라이선스 (License)

[Apache License 2.0](./LICENSE)
