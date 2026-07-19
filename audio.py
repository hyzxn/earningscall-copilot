"""
WASAPI loopback으로 컴퓨터 재생 소리를 캡처한다.
청크 단위(float32 numpy array)로 queue에 넣는다.
"""
import asyncio
import queue
import threading
import numpy as np
import os
import sounddevice as sd


SAMPLE_RATE = 16000   # Whisper 요구 사항
CHUNK_SEC = 5         # 5초 청크마다 전사


def _find_loopback_device() -> int:
    """WASAPI loopback 장치 인덱스를 찾는다."""
    for i, dev in enumerate(sd.query_devices()):
        # Windows WASAPI loopback은 hostapi가 WASAPI이고 max_input_channels > 0
        if "wasapi" in sd.query_hostapis(dev["hostapi"])["name"].lower():
            if dev["max_input_channels"] > 0 and "loopback" in dev["name"].lower():
                return i

    # loopback 이름이 없는 경우 WASAPI 출력장치의 loopback 인덱스 탐색
    # (일부 시스템에서 '스피커 (loopback)' 형태로 표시됨)
    for i, dev in enumerate(sd.query_devices()):
        name = dev["name"].lower()
        if dev["max_input_channels"] > 0 and any(k in name for k in ["loopback", "stereo mix", "what u hear", "스테레오 믹스"]):
            return i

    raise RuntimeError(
        "WASAPI Loopback 장치를 찾을 수 없습니다.\n"
        "Windows 설정 > 소리 > 녹음 탭에서 '스테레오 믹스'를 활성화하거나,\n"
        "VB-Audio Virtual Cable을 설치하세요.\n\n"
        "현재 감지된 장치 목록:\n" + "\n".join(
            f"  [{i}] {d['name']} (in:{d['max_input_channels']})"
            for i, d in enumerate(sd.query_devices())
        )
    )


class AudioCapture:
    def __init__(self):
        self._q: queue.Queue[np.ndarray] = queue.Queue()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._device_idx = _find_loopback_device()
        self._buffer: list[np.ndarray] = []
        self._buffer_samples = CHUNK_SEC * SAMPLE_RATE

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3)

    def _capture_loop(self):
        def callback(indata, frames, time_info, status):
            audio = indata[:, 0].copy()  # mono
            self._buffer.append(audio)
            total = sum(len(a) for a in self._buffer)
            if total >= self._buffer_samples:
                chunk = np.concatenate(self._buffer)
                gain = float(os.getenv("AUDIO_GAIN", "1.0"))
                if gain != 1.0:
                    chunk = np.clip(chunk * gain, -1.0, 1.0)
                chunk = chunk[: self._buffer_samples]
                if len(chunk) > 0:
                    self._q.put(chunk)
                # 남은 오버플로우는 버퍼 첫 항목으로
                overflow = chunk[self._buffer_samples :]
                self._buffer = [overflow] if len(overflow) > 0 else []

        with sd.InputStream(
            device=self._device_idx,
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            callback=callback,
            blocksize=1024,
        ):
            while not self._stop_event.is_set():
                self._stop_event.wait(timeout=0.1)

    async def get_chunk_async(self) -> np.ndarray | None:
        """청크가 준비되면 반환, 없으면 None."""
        try:
            return self._q.get_nowait()
        except queue.Empty:
            return None


def list_devices():
    """디버그용: 현재 사용 가능한 입력 장치 출력."""
    print("=== 오디오 장치 목록 ===")
    for i, dev in enumerate(sd.query_devices()):
        if dev["max_input_channels"] > 0:
            api = sd.query_hostapis(dev["hostapi"])["name"]
            print(f"[{i}] {dev['name']} | API: {api} | in: {dev['max_input_channels']}")


if __name__ == "__main__":
    list_devices()
