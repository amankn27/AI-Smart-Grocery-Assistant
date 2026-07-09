import { useEffect, useRef, useState } from "react";
import type { DetectResponse } from "../api";

// Opens the device camera and captures a still frame on demand. Draws detection boxes over
// the last captured frame, highlighting low-confidence boxes that need user confirmation.
export function CameraCapture({
  onFrame,
  onBarcode,
  detection,
  busy,
}: {
  onFrame: (frame: Blob) => void;
  onBarcode: (frame: Blob) => void;
  detection: DetectResponse | null;
  busy: boolean;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let stream: MediaStream | null = null;
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: "environment" } })
      .then((s) => {
        stream = s;
        if (videoRef.current) videoRef.current.srcObject = s;
      })
      .catch(() => setError("Camera unavailable — you can still use manual entry."));
    return () => stream?.getTracks().forEach((t) => t.stop());
  }, []);

  function grabFrame(sink: (frame: Blob) => void) {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d")!.drawImage(video, 0, 0);
    canvas.toBlob((blob) => blob && sink(blob), "image/jpeg", 0.9);
  }

  return (
    <div className="rounded-xl border bg-white p-3 shadow-sm">
      <div className="relative">
        <video ref={videoRef} autoPlay playsInline muted className="w-full rounded-lg bg-black" />
        {detection && (
          <svg
            className="pointer-events-none absolute inset-0 h-full w-full"
            viewBox={`0 0 ${detection.width} ${detection.height}`}
            preserveAspectRatio="none"
          >
            {detection.detections.map((d, i) => (
              <g key={i}>
                <rect
                  x={d.bbox_xyxy[0]}
                  y={d.bbox_xyxy[1]}
                  width={d.bbox_xyxy[2] - d.bbox_xyxy[0]}
                  height={d.bbox_xyxy[3] - d.bbox_xyxy[1]}
                  fill="none"
                  stroke={d.needs_confirmation ? "#f59e0b" : "#22c55e"}
                  strokeWidth={3}
                />
                <text x={d.bbox_xyxy[0] + 4} y={d.bbox_xyxy[1] + 18} fill="#fff" fontSize={16}>
                  {d.label} {(d.confidence * 100).toFixed(0)}%
                </text>
              </g>
            ))}
          </svg>
        )}
      </div>
      <canvas ref={canvasRef} className="hidden" />
      {error && <p className="mt-2 text-sm text-amber-600">{error}</p>}
      <div className="mt-3 flex gap-2">
        <button
          onClick={() => grabFrame(onFrame)}
          disabled={busy}
          className="flex-1 rounded-lg bg-emerald-600 py-2 font-medium text-white disabled:opacity-50"
        >
          {busy ? "Analyzing…" : "📸 Scan product"}
        </button>
        <button
          onClick={() => grabFrame(onBarcode)}
          disabled={busy}
          className="flex-1 rounded-lg bg-slate-800 py-2 font-medium text-white disabled:opacity-50"
        >
          🔖 Scan barcode
        </button>
      </div>
      {detection?.detections.some((d) => d.needs_confirmation) && (
        <p className="mt-2 text-sm text-amber-600">
          Low confidence — please confirm the product manually.
        </p>
      )}
    </div>
  );
}
