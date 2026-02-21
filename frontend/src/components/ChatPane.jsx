import React, { useState, useEffect, useRef } from "react";
import SchemaView from "./SchemaView";
import ChartDisplay from "./ChartDisplay";

export default function ChatPane({ fileId }) {
  // Messages per file: { [fileId]: [{ role, content, files }] }
  const [messagesByFile, setMessagesByFile] = useState({});
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const initialSentRef = useRef({});

  // Get current file's messages
  const messages = messagesByFile[fileId] || [];

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-send initial analysis message for new files
  useEffect(() => {
    if (!fileId || initialSentRef.current[fileId]) return;
    initialSentRef.current[fileId] = true;

    const initialMsg =
      "Analyze the log file. Read the file, infer the schema, " +
      "and show me the proposed table structure.";
    sendMessage(initialMsg);
  }, [fileId]);

  // Send a message to the agent
  const sendMessage = async (text) => {
    // Add user message to chat
    const userMsg = { role: "user", content: text, files: [] };
    setMessagesByFile((prev) => ({
      ...prev,
      [fileId]: [...(prev[fileId] || []), userMsg],
    }));

    setLoading(true);

    const res = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: text, file_id: fileId }),
    });
    const data = await res.json();

    // Append agent response after the user message already in chat
    const agentMsg = {
      role: "assistant",
      content: data.answer,
      files: data.files || [],
    };
    setMessagesByFile((prev) => ({
      ...prev,
      [fileId]: [...(prev[fileId] || []), agentMsg],
    }));

    setLoading(false);
  };

  // Handle form submit
  const handleSubmit = (e) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    sendMessage(text);
  };

  // Send a follow-up (used by SchemaView confirm button)
  const handleFollowUp = (text) => {
    if (loading) return;
    sendMessage(text);
  };

  return (
    <div style={styles.container}>
      {/* Message list */}
      <div style={styles.messages}>
        {messages.map((msg, i) => (
          <MessageBubble
            key={i}
            message={msg}
            onFollowUp={handleFollowUp}
          />
        ))}
        {loading && (
          <div style={styles.loadingWrapper}>
            <div style={styles.loading}>Analyzing...</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input bar */}
      <form onSubmit={handleSubmit} style={styles.inputBar}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your log file..."
          style={styles.input}
          disabled={loading}
        />
        <button type="submit" style={styles.sendBtn} disabled={loading}>
          Send
        </button>
      </form>
    </div>
  );
}

// Renders a single message, detecting schema JSON and chart files
function MessageBubble({ message, onFollowUp }) {
  const isUser = message.role === "user";

  // Detect schema JSON in assistant messages
  const schemaData = !isUser ? extractSchema(message.content) : null;

  // Detect chart files
  const chartFiles = message.files?.filter((f) => f.endsWith(".png")) || [];

  return (
    <div
      style={{
        ...styles.bubble,
        alignSelf: isUser ? "flex-end" : "flex-start",
        background: isUser ? "#2563eb" : "#fff",
        color: isUser ? "#fff" : "#1a1a1a",
        border: isUser ? "none" : "1px solid #e0e0e0",
      }}
    >
      {/* Render text content, stripping out schema JSON if detected */}
      <div style={styles.content}>
        {schemaData
          ? renderTextWithoutSchema(message.content)
          : message.content}
      </div>

      {/* Render schema if detected */}
      {schemaData && (
        <SchemaView schema={schemaData} onConfirm={onFollowUp} />
      )}

      {/* Render chart images */}
      {chartFiles.map((path, i) => (
        <ChartDisplay key={i} filePath={path} />
      ))}
    </div>
  );
}

// Try to extract schema JSON from message text
function extractSchema(text) {
  // Look for JSON block with "tables" key
  const jsonMatch = text.match(/```json\s*([\s\S]*?)```/);
  if (jsonMatch) {
    const parsed = safeParseJSON(jsonMatch[1]);
    if (parsed?.tables) return parsed;
  }

  // Try to find inline JSON with tables key
  const braceMatch = text.match(/\{[\s\S]*"tables"[\s\S]*\}/);
  if (braceMatch) {
    const parsed = safeParseJSON(braceMatch[0]);
    if (parsed?.tables) return parsed;
  }

  return null;
}

// Remove the schema JSON block from the text for display
function renderTextWithoutSchema(text) {
  return text.replace(/```json\s*[\s\S]*?```/, "").trim();
}

function safeParseJSON(str) {
  try {
    return JSON.parse(str);
  } catch {
    return null;
  }
}

const styles = {
  container: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
    background: "#f5f5f5",
  },
  messages: {
    flex: 1,
    overflowY: "auto",
    padding: "20px",
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  bubble: {
    maxWidth: "75%",
    padding: "12px 16px",
    borderRadius: "12px",
    fontSize: "0.9rem",
    lineHeight: 1.5,
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
  },
  content: {},
  loadingWrapper: {
    alignSelf: "flex-start",
  },
  loading: {
    padding: "12px 16px",
    borderRadius: "12px",
    background: "#fff",
    border: "1px solid #e0e0e0",
    fontSize: "0.9rem",
    color: "#888",
    fontStyle: "italic",
  },
  inputBar: {
    display: "flex",
    gap: "8px",
    padding: "12px 20px",
    borderTop: "1px solid #ddd",
    background: "#fff",
  },
  input: {
    flex: 1,
    padding: "10px 14px",
    borderRadius: "8px",
    border: "1px solid #ddd",
    fontSize: "0.9rem",
    outline: "none",
  },
  sendBtn: {
    padding: "10px 20px",
    borderRadius: "8px",
    border: "none",
    background: "#2563eb",
    color: "#fff",
    fontSize: "0.9rem",
    fontWeight: 600,
    cursor: "pointer",
  },
};
