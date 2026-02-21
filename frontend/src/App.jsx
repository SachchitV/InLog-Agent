import React, { useState, useCallback } from "react";
import FileDrop from "./components/FileDrop";
import FileList from "./components/FileList";
import ChatPane from "./components/ChatPane";

export default function App() {
  // List of uploaded files: [{ file_id, filename }]
  const [files, setFiles] = useState([]);
  // Currently active file for chat context
  const [activeFileId, setActiveFileId] = useState(null);
  // App mode: "landing" or "workspace"
  const [mode, setMode] = useState("landing");

  // Called after a successful upload
  const handleFileUploaded = useCallback((fileInfo) => {
    setFiles((prev) => [...prev, fileInfo]);
    setActiveFileId(fileInfo.file_id);
    setMode("workspace");
  }, []);

  // Landing page — centered file drop zone
  if (mode === "landing") {
    return (
      <div style={styles.landing}>
        <h1 style={styles.title}>Inlog Agent</h1>
        <p style={styles.subtitle}>
          Drop a timestamped log file to get started
        </p>
        <FileDrop onFileUploaded={handleFileUploaded} />
      </div>
    );
  }

  // Workspace — two-pane layout
  return (
    <div style={styles.workspace}>
      <div style={styles.sidebar}>
        <FileList
          files={files}
          activeFileId={activeFileId}
          onSelectFile={setActiveFileId}
          onFileUploaded={handleFileUploaded}
        />
      </div>
      <div style={styles.main}>
        <ChatPane fileId={activeFileId} />
      </div>
    </div>
  );
}

const styles = {
  landing: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "100vh",
    padding: "2rem",
  },
  title: {
    fontSize: "2rem",
    fontWeight: 700,
    marginBottom: "0.5rem",
  },
  subtitle: {
    fontSize: "1rem",
    color: "#666",
    marginBottom: "2rem",
  },
  workspace: {
    display: "flex",
    height: "100vh",
  },
  sidebar: {
    width: "240px",
    borderRight: "1px solid #ddd",
    background: "#fff",
    flexShrink: 0,
  },
  main: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
  },
};
