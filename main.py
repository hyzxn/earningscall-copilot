"""
FastAPI + WebSocket으로 오디오 캡처 → 전사 → AI 분석을 오케스트레이션한다.

메시지 타입 (서버 → 클라이언트):
  {"type": "transcript", "text": "..."}
  {"type": "summary",    "text": "..."}
  {"type": "metrics",    "data": {...}}
  {"type": "error",      "text": "..."}
  {"type": "status",     "text": "..."}
"""
import asyncio
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

from audio import AudioCapture
from transcriber import Transcriber
from analyst import Analyst
from logger import SessionLogger

app = FastAPI()
BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

SUMMARY_INTERVAL = int(os.getenv("SUMMARY_INTERVAL_SEC", "180"))


@app.get("/")
def index():
    return FileResponse(BASE_DIR / "static/index.html")


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    await ws.send_text(json.dumps({"type": "status", "text": "모델 로딩 중..."}))

    try:
        transcriber = Transcriber()
        analyst = Analyst()
    except Exception as e:
        await ws.send_text(json.dumps({"type": "error", "text": str(e)}))
        await ws.close()
        return

    logger = SessionLogger()
    audio = AudioCapture()
    full_transcript = ""
    last_analysis_time = time.time()
    last_analyzed_pos = 0
    analysis_task: asyncio.Task | None = None

    async def run_analysis(text: str):
        """AI 분석을 별도 태스크로 실행."""
        nonlocal last_analyzed_pos
        await ws.send_text(json.dumps({"type": "status", "text": "AI 분석 중..."}))
        try:
            summary, metrics = await asyncio.gather(
                asyncio.get_event_loop().run_in_executor(
                    None, analyst.get_summary, text
                ),
                asyncio.get_event_loop().run_in_executor(
                    None, analyst.get_metrics, text
                ),
            )
            if summary:
                await ws.send_text(json.dumps({"type": "summary", "text": summary}))
                logger.log_overview(summary)
            if metrics:
                await ws.send_text(json.dumps({"type": "metrics", "data": metrics}))
                logger.log_indicator(metrics)
            last_analyzed_pos = len(full_transcript)
        except Exception as e:
            await ws.send_text(json.dumps({"type": "error", "text": f"AI 분석 오류: {e}"}))
        finally:
            await ws.send_text(json.dumps({"type": "status", "text": "녹음 중..."}))

    try:
        audio.start()
        backend = os.getenv("ANALYZER_BACKEND", "ollama")
        if backend == "gemini":
            ai_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        else:
            ai_model = os.getenv("OLLAMA_MODEL", "qwen3.5:9b")
        await ws.send_text(json.dumps({
            "type": "status",
            "text": f"녹음 시작 ✓  모델: {os.getenv('WHISPER_MODEL','small')} / {ai_model} ({backend})"
        }))

        while True:
            # 클라이언트 메시지 확인 (non-blocking)
            force_analyze = False
            try:
                msg = await asyncio.wait_for(ws.receive_text(), timeout=0.01)
                if msg == "stop":
                    break
                elif msg == "analyze_now":
                    force_analyze = True
            except asyncio.TimeoutError:
                pass

            # 오디오 청크 처리 (Whisper는 항상 우선 실행)
            chunk = await audio.get_chunk_async()
            if chunk is not None:
                text = await asyncio.get_event_loop().run_in_executor(
                    None, transcriber.transcribe, chunk
                )
                if text:
                    full_transcript += " " + text
                    await ws.send_text(json.dumps({"type": "transcript", "text": text}))
                    logger.log_cc(text)

            # 주기적 AI 분석 (또는 즉시 분석 요청) - 별도 태스크로 실행
            now = time.time()
            if full_transcript and (force_analyze or (now - last_analysis_time) >= SUMMARY_INTERVAL):
                # 기존 분석 태스크가 진행 중이면 취소하지 않음 (리소스 절약)
                if analysis_task is None or analysis_task.done():
                    last_analysis_time = now
                    new_text = full_transcript[last_analyzed_pos:]
                    analysis_task = asyncio.create_task(run_analysis(new_text))

            await asyncio.sleep(0.05)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await ws.send_text(json.dumps({"type": "error", "text": str(e)}))
        except Exception:
            pass
    finally:
        # 분석 태스크가 진행 중이면 취소
        if analysis_task and not analysis_task.done():
            analysis_task.cancel()
        audio.stop()
        logger.close()


if __name__ == "__main__":
    import threading
    import time
    import webview
    import uvicorn

    PORT = 8765

    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="error")

    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(1.5)  # 서버 준비 대기

    webview.create_window(
        "EarningsCall Copilot",
        f"http://127.0.0.1:{PORT}",
        width=1400,
        height=860,
        resizable=True,
    )
    webview.start()
