import React, { useRef } from "react";

export default function FileList({ files, activeFileId, onSelectFile, onFileUploaded }) {
  const fileInputRef = useRef(null);

  // Upload additional file
  const handleAddFile = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch("/upload", { method: "POST", body: formData });
    const data = await res.json();
    onFileUploaded(data);
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span style={styles.headerText}>Files</span>
        <button
          style={styles.addBtn}
          onClick={() => fileInputRef.current?.click()}
          title="Upload another file"
        >
          +
        </button>
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleAddFile}
          style={{ display: "none" }}
        />
      </div>

      <div style={styles.list}>
        {files.map((f) => (
          <div
            key={f.file_id}
            onClick={() => onSelectFile(f.file_id)}
            style={{
              ...styles.item,
              background: f.file_id === activeFileId ? "#e8f0fe" : "transparent",
              fontWeight: f.file_id === activeFileId ? 600 : 400,
            }}
          >
            {f.filename}
          </div>
        ))}
      </div>
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "12px 16px",
    borderBottom: "1px solid #eee",
  },
  headerText: {
    fontSize: "0.85rem",
    fontWeight: 600,
    textTransform: "uppercase",
    color: "#888",
    letterSpacing: "0.05em",
  },
  addBtn: {
    width: "28px",
    height: "28px",
    border: "1px solid #ddd",
    borderRadius: "6px",
    background: "#fff",
    cursor: "pointer",
    fontSize: "1.1rem",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "#666",
  },
  list: {
    flex: 1,
    overflowY: "auto",
    padding: "8px",
  },
  item: {
    padding: "8px 12px",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "0.9rem",
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
    marginBottom: "2px",
  },
};
