/**
 * useChat.js
 *
 * Manages the full chat conversation state:
 * - Sending text, image, and audio messages
 * - Appending the user bubble immediately (optimistic UI)
 * - Appending the assistant reply when the API responds
 * - Error handling
 * - loadMessages: load history from backend into feed
 */

import { useState, useCallback, useRef } from "react";
import { sendMessage, sendMessageWithImage, sendAudioMessage } from "../services/api";

export function useChat() {
  // Each message: { id, role: "user"|"assistant", content, imageUrl?, metadata?, timestamp, error? }
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const idRef = useRef(0);

  function nextId() {
    idRef.current += 1;
    return idRef.current;
  }

  // Appends a new message object to the list
  function appendMessage(msg) {
    setMessages((prev) => [...prev, { id: nextId(), ...msg }]);
  }

  // Replaces the last message (used to update a placeholder with real content)
  function replaceLastMessage(msg) {
    setMessages((prev) => {
      const copy = [...prev];
      copy[copy.length - 1] = { ...copy[copy.length - 1], ...msg };
      return copy;
    });
  }

  /**
   * Load a list of existing messages into feed (used for View History).
   * Each message must have: { id, role, content, timestamp }
   * @param {Array} msgs
   */
  const loadMessages = useCallback((msgs) => {
    setMessages(msgs);
  }, []);

  /**
   * Sends a text-only message.
   * @param {string} text
   */
  const sendText = useCallback(async (text) => {
    if (!text.trim() || loading) return;

    const timestamp = new Date().toISOString();

    appendMessage({ role: "user", content: text, timestamp });
    appendMessage({ role: "assistant", content: null, timestamp, pending: true });

    setLoading(true);
    try {
      const data = await sendMessage(text);
      replaceLastMessage({
        content: data.response,
        metadata: data.metadata,
        timestamp: data.timestamp,
        pending: false,
      });
    } catch (err) {
      replaceLastMessage({
        content: null,
        error: err.message || "Failed to get a response. Please try again.",
        pending: false,
      });
    } finally {
      setLoading(false);
    }
  }, [loading]);

  /**
   * Sends a message with an attached image.
   * @param {string|null} text
   * @param {File} file
   */
  const sendImage = useCallback(async (text, file) => {
    if (!file || loading) return;

    const timestamp = new Date().toISOString();
    const localUrl = URL.createObjectURL(file);

    appendMessage({ role: "user", content: text || "", imageUrl: localUrl, timestamp });
    appendMessage({ role: "assistant", content: null, timestamp, pending: true });

    setLoading(true);
    try {
      const data = await sendMessageWithImage(text, file);
      replaceLastMessage({
        content: data.response,
        metadata: data.metadata,
        timestamp: data.timestamp,
        pending: false,
      });
    } catch (err) {
      replaceLastMessage({
        content: null,
        error: err.message || "Image analysis failed. Please try again.",
        pending: false,
      });
    } finally {
      setLoading(false);
    }
  }, [loading]);

  /**
   * Sends a voice recording.
   * @param {File} file
   */
  const sendAudio = useCallback(async (file) => {
    if (!file || loading) return;

    const timestamp = new Date().toISOString();

    appendMessage({ role: "user", content: "[Voice message]", timestamp });
    appendMessage({ role: "assistant", content: null, timestamp, pending: true });

    setLoading(true);
    try {
      const data = await sendAudioMessage(file);
      replaceLastMessage({
        content: data.response,
        metadata: data.metadata,
        timestamp: data.timestamp,
        pending: false,
      });
    } catch (err) {
      replaceLastMessage({
        content: null,
        error: err.message || "Audio transcription failed. Please try again.",
        pending: false,
      });
    } finally {
      setLoading(false);
    }
  }, [loading]);

  /**
   * Clears all messages locally (without hitting the server).
   */
  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return { messages, loading, sendText, sendImage, sendAudio, clearMessages, loadMessages };
}