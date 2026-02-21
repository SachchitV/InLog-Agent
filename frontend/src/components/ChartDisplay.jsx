import React from "react";

export default function ChartDisplay({ filePath }) {
  // Convert absolute path to URL served by the backend
  // e.g. "outputs/events_timeline.png" → "/outputs/events_timeline.png"
  // or "/home/.../outputs/foo.png" → "/outputs/foo.png"
  const filename = filePath.split("/").pop();
  const url = `/outputs/${filename}`;

  return (
    <div style={styles.container}>
      <img src={url} alt={filename} style={styles.image} />
      <div style={styles.caption}>{filename}</div>
    </div>
  );
}

const styles = {
  container: {
    marginTop: "12px",
  },
  image: {
    maxWidth: "100%",
    borderRadius: "8px",
    border: "1px solid #e0e0e0",
  },
  caption: {
    fontSize: "0.75rem",
    color: "#888",
    marginTop: "4px",
    fontFamily: "monospace",
  },
};
