import React, { useState, useRef } from "react";

export default function FileDrop({ onFileUploaded }) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  // Upload file to backend
  const uploadFile = async (file) => {
    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch("/upload", { method: "POST", body: formData });
    const data = await res.json();

    setUploading(false);
    onFileUploaded(data);
  };

  // Handle drag events
  const handleDragOver = (e) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = () => setDragging(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
  };

  // Handle click-to-browse
  const handleClick = () => fileInputRef.current?.click();

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) uploadFile(file);
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
      style={{
        ...styles.dropZone,
        borderColor: dragging ? "#2563eb" : "#ccc",
        background: dragging ? "#eff6ff" : "#fafafa",
      }}
    >
      <input
        ref={fileInputRef}
        type="file"
        onChange={handleFileChange}
        style={{ display: "none" }}
      />
      {uploading ? (
        <p style={styles.text}>Uploading...</p>
      ) : (
        <>
          <p style={styles.icon}>+</p>
          <p style={styles.text}>
            Drag & drop a log file here, or click to browse
          </p>
        </>
      )}
    </div>
  );
}

const styles = {
  dropZone: {
    width: "400px",
    height: "200px",
    border: "2px dashed #ccc",
    borderRadius: "12px",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    cursor: "pointer",
    transition: "all 0.15s ease",
  },
  icon: {
    fontSize: "2rem",
    color: "#999",
    marginBottom: "0.5rem",
  },
  text: {
    fontSize: "0.9rem",
    color: "#666",
  },
};
