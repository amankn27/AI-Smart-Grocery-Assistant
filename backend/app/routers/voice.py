"""/voice — voice assistant: STT → chat LLM → TTS.

This is just the Phase 0 chat wired between a speech-to-text front and a text-to-speech back,
so the assistant's reasoning stays in one place. Degrades cleanly: if STT can't transcribe
(no Whisper), the client is told to send typed text; if TTS is browser-mode, the answer text
is returned for the client to speak.
"""

from __future__ import annotations

import base64
import json

from fastapi import APIRouter, File, Form, UploadFile

from app.config.providers import get_llm, get_stt, get_tts
from app.routers.chat import SYSTEM_PROMPT

router = APIRouter(tags=["voice"])


@router.post("/voice")
async def voice(
    audio: UploadFile | None = File(default=None),
    text: str | None = Form(default=None),
    context: str | None = Form(default=None),
) -> dict:
    stt = get_stt()

    # Prefer typed text (client STT / fallback); else transcribe uploaded audio.
    if text:
        transcript, stt_engine = text, "client"
    elif audio is not None:
        result = stt.transcribe(await audio.read())
        transcript, stt_engine = result.text, result.engine
    else:
        transcript, stt_engine = "", stt.name

    if not transcript:
        return {
            "transcript": "", "answer": "", "stt_engine": stt_engine,
            "fallback": "no_speech_detected", "hint": "Send typed text or enable Whisper (STT_PROVIDER=whisper).",
        }

    ctx = json.loads(context) if context else None
    context_block = f"Context:\n{json.dumps(ctx, ensure_ascii=False)}\n\n" if ctx else ""
    llm = get_llm()
    answer = llm.complete(f"{context_block}Question: {transcript}", system=SYSTEM_PROMPT, max_tokens=256)

    tts = get_tts()
    speech = tts.synthesize(answer)
    return {
        "transcript": transcript,
        "answer": answer,
        "stt_engine": stt_engine,
        "llm_provider": llm.name,
        "tts_engine": speech.engine,
        # None → client speaks via Web Speech API; bytes → base64 audio the client can play.
        "audio_base64": base64.b64encode(speech.audio).decode() if speech.audio else None,
        "audio_mime": speech.mime,
    }
