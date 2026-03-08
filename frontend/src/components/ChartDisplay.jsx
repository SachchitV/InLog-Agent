import React from "react";

export default function ChartDisplay({ filePath }) {
  // Extract path relative to outputs/ directory
  // e.g. "../outputs/abc123/chart.png" → "abc123/chart.png"
  const idx = filePath.indexOf("outputs/");
  const relativePath = idx >= 0 ? filePath.slice(idx + 8) : filePath.split("/").pop();
  const url = `/outputs/${relativePath}`;

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
