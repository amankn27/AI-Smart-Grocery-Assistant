import { useRef, useState } from "react";
import { api } from "../api";

// Records a short clip via MediaRecorder, sends it to /voice (Whisper → chat), and speaks the
// answer with the Web Speech API when the server uses browser-mode TTS (the default).
export function VoiceAssistant() {
  const [recording, setRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [answer, setAnswer] = useState("");
  const [note, setNote] = useState<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  function speak(text: string, mime?: string, b64?: string | null) {
    if (b64) {
      new Audio(`data:${mime ?? "audio/mpeg"};base64,${b64}`).play();
    } else if ("speechSynthesis" in window) {
      window.speechSynthesis.speak(new SpeechSynthesisUtterance(text));
    }
  }

  async function start() {
    setNote(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const rec = new MediaRecorder(stream);
      chunksRef.current = [];
      rec.ondataavailable = (e) => chunksRef.current.push(e.data);
      rec.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        const res = await api.voice(blob);
        if (res.fallback) {
          setNote(res.hint ?? "No speech detected.");
          return;
        }
        setTranscript(res.transcript);
        setAnswer(res.answer);
        speak(res.answer, res.audio_mime, res.audio_base64);
      };
      rec.start();
      recorderRef.current = rec;
      setRecording(true);
    } catch {
      setNote("Microphone unavailable.");
    }
  }

  function stop() {
    recorderRef.current?.stop();
    setRecording(false);
  }

  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold">🎙️ Voice assistant</h2>
        <button
          onClick={recording ? stop : start}
          className={`rounded-lg px-4 py-1 text-sm font-medium text-white ${
            recording ? "bg-red-600" : "bg-slate-800"
          }`}
        >
          {recording ? "■ Stop" : "● Ask by voice"}
        </button>
      </div>
      {note && <p className="mt-2 text-sm text-amber-600">{note}</p>}
      {transcript && <p className="mt-2 text-sm text-slate-500">You: {transcript}</p>}
      {answer && <p className="mt-1 text-sm">{answer}</p>}
    </div>
  );
}
