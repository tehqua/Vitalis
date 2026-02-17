/**
 * ChatInput.jsx
 *
 * The compose bar at the bottom of the chat.
 * Supports:
 *   - Text input (auto-growing textarea, Enter to send)
 *   - Image attachment (file picker, previewed before send)
 *   - Voice recording (MediaRecorder API, recorded in-browser)
 */

import React, { useState, useRef, useEffect } from "react";

const s = {
  wrap: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    padding: "0.75rem 1.25rem 1rem",
    background:
      "linear-gradient(to top, rgba(248,250,252,1) 55%, rgba(248,250,252,0) 100%)",
  },

  inner: {
    maxWidth: "52rem",
    margin: "0 auto",
  },

  panel: {
    background: "rgba(255,255,255,0.78)",
    backdropFilter: "blur(16px)",
    WebkitBackdropFilter: "blur(16px)",
    border: "1px solid rgba(255,255,255,0.7)",
    borderRadius: "1.25rem",
    padding: "0.5rem",
    boxShadow: "0 4px 20px rgba(15,23,42,0.10)",
    transition: "box-shadow 200ms ease",
  },

  panelFocused: {
    boxShadow: "0 0 0 2px rgba(20,184,166,0.2), 0 4px 20px rgba(15,23,42,0.10)",
  },

  // Image preview strip
  previewStrip: {
    padding: "0.375rem 0.625rem 0",
    display: "flex",
    alignItems: "center",
    gap: "0.5rem",
  },

  previewImg: {
    width: "3rem",
    height: "3rem",
    objectFit: "cover",
    borderRadius: "0.5rem",
    border: "1px solid rgba(226,232,240,0.7)",
  },

  removeBtn: {
    padding: "0.25rem",
    borderRadius: "9999px",
    background: "#1e293b",
    border: "none",
    color: "#ffffff",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    lineHeight: 1,
  },

  previewLabel: {
    fontSize: "0.8rem",
    color: "#64748b",
    fontStyle: "italic",
  },

  textarea: {
    width: "100%",
    border: "none",
    outline: "none",
    resize: "none",
    background: "transparent",
    padding: "0.625rem 0.75rem",
    fontSize: "0.9375rem",
    fontFamily: "var(--font-body)",
    color: "#1e293b",
    lineHeight: 1.55,
    minHeight: "2.5rem",
    maxHeight: "8rem",
    overflowY: "auto",
  },

  bottomRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0.125rem 0.5rem 0.25rem",
  },

  tools: {
    display: "flex",
    alignItems: "center",
    gap: "0.25rem",
  },

  iconBtn: {
    padding: "0.4rem",
    borderRadius: "0.5rem",
    border: "none",
    background: "transparent",
    color: "#94a3b8",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    transition: "background 140ms ease, color 140ms ease",
    lineHeight: 1,
  },

  divider: {
    width: "1px",
    height: "1rem",
    background: "#e2e8f0",
    margin: "0 0.25rem",
  },

  attachRecordBtn: {
    display: "flex",
    alignItems: "center",
    gap: "0.35rem",
    padding: "0.35rem 0.65rem",
    borderRadius: "0.4rem",
    border: "1px solid #e2e8f0",
    background: "#f8fafc",
    color: "#64748b",
    fontSize: "0.75rem",
    fontWeight: 500,
    fontFamily: "var(--font-body)",
    cursor: "pointer",
    transition: "background 140ms ease, color 140ms ease",
  },

  sendBtn: {
    padding: "0.5rem",
    borderRadius: "0.625rem",
    border: "none",
    background: "#1e293b",
    color: "#ffffff",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    boxShadow: "0 2px 6px rgba(15,23,42,0.2)",
    transition: "background 140ms ease, transform 120ms ease",
    lineHeight: 1,
  },

  disclaimer: {
    textAlign: "center",
    fontSize: "0.65rem",
    color: "#94a3b8",
    marginTop: "0.5rem",
    padding: "0 0.25rem",
  },

  // Recording indicator
  recIndicator: {
    display: "flex",
    alignItems: "center",
    gap: "0.5rem",
    fontSize: "0.8125rem",
    color: "#dc2626",
    fontWeight: 500,
  },

  recDot: {
    width: "0.5rem",
    height: "0.5rem",
    borderRadius: "9999px",
    background: "#ef4444",
    animation: "pulse 1s ease infinite",
  },
};

function encodeWAV(audioBuffer) {
  const numChannels = 1;
  const sampleRate = audioBuffer.sampleRate;
  const samples = audioBuffer.getChannelData(0);
  
  const int16 = new Int16Array(samples.length);
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    int16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  
  const buffer = new ArrayBuffer(44 + int16.byteLength);
  const view = new DataView(buffer);
  
  function writeString(offset, str) {
    for (let i = 0; i < str.length; i++)
      view.setUint8(offset + i, str.charCodeAt(i));
  }
  
  writeString(0, "RIFF");
  view.setUint32(4, 36 + int16.byteLength, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, "data");
  view.setUint32(40, int16.byteLength, true);
  new Int16Array(buffer, 44).set(int16);
  
  return buffer;
}

export default function ChatInput({ onSendText, onSendImage, onSendAudio, disabled }) {
  const [text, setText] = useState("");
  const [focused, setFocused] = useState(false);
  const [pendingImage, setPendingImage] = useState(null);  // { file, url }
  const [recording, setRecording] = useState(false);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 128)}px`;
  }, [text]);

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleSend() {
    if (disabled) return;

    if (pendingImage) {
      onSendImage(text.trim() || null, pendingImage.file);
      setPendingImage(null);
      setText("");
      return;
    }

    if (text.trim()) {
      onSendText(text.trim());
      setText("");
    }
  }

  function handleFileSelect(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    setPendingImage({ file, url });
    e.target.value = "";
  }

  function removeImage() {
    if (pendingImage?.url) URL.revokeObjectURL(pendingImage.url);
    setPendingImage(null);
  }

  async function toggleRecording() {
      if (recording) {
        mediaRecorderRef.current?.stop();
        setRecording(false);
        return;
      }

      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        const mimeType = MediaRecorder.isTypeSupported("audio/ogg;codecs=opus")
          ? "audio/ogg;codecs=opus"
          : MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
          ? "audio/webm;codecs=opus"
          : "audio/webm";

        const recorder = new MediaRecorder(stream, { mimeType });
        audioChunksRef.current = [];

        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) audioChunksRef.current.push(e.data);
        };

        recorder.onstop = async () => {
          const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });

          try {
            // Convert webm → wav để librosa đọc được
            const arrayBuffer = await blob.arrayBuffer();
            const audioCtx = new AudioContext({ sampleRate: 16000 });
            const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);
            const wavBuffer = encodeWAV(audioBuffer);
            const wavBlob = new Blob([wavBuffer], { type: "audio/wav" });
            const file = new File([wavBlob], "recording.wav", { type: "audio/wav" });
            onSendAudio(file);
            audioCtx.close();
          } catch (err) {
            // Fallback nếu convert thất bại
            console.error("WAV convert failed:", err);
            const file = new File([blob], "recording.webm", { type: "audio/webm" });
            onSendAudio(file);
          }

          stream.getTracks().forEach((t) => t.stop());
        };

        mediaRecorderRef.current = recorder;
        recorder.start();
        setRecording(true);
      } catch {
        alert("Microphone access is required for voice messages.");
      }
  }

  const canSend = !disabled && (text.trim().length > 0 || pendingImage != null);

  return (
    <div style={s.wrap}>
      <div style={s.inner}>
        <div style={{ ...s.panel, ...(focused ? s.panelFocused : {}) }}>
          {/* Image preview */}
          {pendingImage && (
            <div style={s.previewStrip}>
              <img src={pendingImage.url} alt="Preview" style={s.previewImg} />
              <button style={s.removeBtn} onClick={removeImage}>
                <span className="material-symbols-outlined" style={{ fontSize: "0.875rem" }}>
                  close
                </span>
              </button>
              <span style={s.previewLabel}>{pendingImage.file.name}</span>
            </div>
          )}

          {/* Recording indicator */}
          {recording && (
            <div style={{ ...s.previewStrip }}>
              <div style={s.recIndicator}>
                <div style={s.recDot} />
                Recording… tap mic to stop
              </div>
            </div>
          )}

          <textarea
            ref={textareaRef}
            style={s.textarea}
            rows={1}
            placeholder={
              pendingImage
                ? "Add a message about this image…"
                : "Ask about symptoms, history, or upload a photo…"
            }
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            disabled={disabled}
          />

          <div style={s.bottomRow}>
            <div style={s.tools}>
              {/* Image upload */}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp,image/gif"
                style={{ display: "none" }}
                onChange={handleFileSelect}
              />
              <button
                style={s.iconBtn}
                title="Attach image"
                onClick={() => fileInputRef.current?.click()}
                disabled={disabled}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "rgba(204,251,241,0.4)";
                  e.currentTarget.style.color = "#0d9488";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "transparent";
                  e.currentTarget.style.color = "#94a3b8";
                }}
              >
                <span className="material-symbols-outlined" style={{ fontSize: "1.1rem" }}>
                  add_photo_alternate
                </span>
              </button>

              {/* Microphone */}
              <button
                style={{
                  ...s.iconBtn,
                  ...(recording ? { color: "#ef4444", background: "rgba(254,226,226,0.5)" } : {}),
                }}
                title={recording ? "Stop recording" : "Record voice message"}
                onClick={toggleRecording}
                disabled={disabled}
                onMouseEnter={(e) => {
                  if (!recording) {
                    e.currentTarget.style.background = "rgba(254,226,226,0.4)";
                    e.currentTarget.style.color = "#ef4444";
                  }
                }}
                onMouseLeave={(e) => {
                  if (!recording) {
                    e.currentTarget.style.background = "transparent";
                    e.currentTarget.style.color = "#94a3b8";
                  }
                }}
              >
                <span className="material-symbols-outlined" style={{ fontSize: "1.1rem" }}>
                  {recording ? "stop_circle" : "mic"}
                </span>
              </button>

              <div style={s.divider} />

            </div>

            {/* Send button */}
            <button
              style={{
                ...s.sendBtn,
                ...(canSend ? { background: "#0d9488" } : {}),
                ...(disabled ? { opacity: 0.5, cursor: "not-allowed" } : {}),
              }}
              onClick={handleSend}
              disabled={!canSend}
              title="Send"
              onMouseEnter={(e) => {
                if (canSend) e.currentTarget.style.transform = "translateY(-1px)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "translateY(0)";
              }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: "1.1rem" }}>
                arrow_upward
              </span>
            </button>
          </div>
        </div>

        <p style={s.disclaimer}>
          MedScreening can make mistakes. Please verify important information
          with a healthcare professional.
        </p>
      </div>
    </div>
  );
}
