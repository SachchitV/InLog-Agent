import React from "react";

export default function SchemaView({ schema, onConfirm }) {
  if (!schema?.tables?.length) return null;

  return (
    <div style={styles.container}>
      {schema.tables.map((table, i) => (
        <div key={i} style={styles.tableCard}>
          {/* Table header */}
          <div style={styles.tableHeader}>
            <span style={styles.tableName}>{table.name}</span>
            {table.description && (
              <span style={styles.tableDesc}>{table.description}</span>
            )}
          </div>

          {/* Column list */}
          <table style={styles.columnTable}>
            <thead>
              <tr>
                <th style={styles.th}>Column</th>
                <th style={styles.th}>Type</th>
                <th style={styles.th}>Description</th>
              </tr>
            </thead>
            <tbody>
              {table.columns.map((col, j) => (
                <tr key={j}>
                  <td style={styles.td}>
                    <code style={styles.code}>{col.name}</code>
                  </td>
                  <td style={styles.td}>
                    <span style={styles.type}>{col.type}</span>
                  </td>
                  <td style={styles.td}>{col.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}

      {/* Timestamp format and pattern info */}
      {schema.timestamp_format && (
        <div style={styles.meta}>
          Timestamp format: <code style={styles.code}>{schema.timestamp_format}</code>
        </div>
      )}
      {schema.line_pattern && (
        <div style={styles.meta}>
          Line pattern: <code style={styles.code}>{schema.line_pattern}</code>
        </div>
      )}

      {/* Confirm button */}
      <button
        style={styles.confirmBtn}
        onClick={() =>
          onConfirm("The schema looks good. Please parse the full file, store it in the database, and generate overview charts.")
        }
      >
        Confirm Schema
      </button>
    </div>
  );
}

const styles = {
  container: {
    marginTop: "12px",
  },
  tableCard: {
    border: "1px solid #e0e0e0",
    borderRadius: "8px",
    overflow: "hidden",
    marginBottom: "12px",
  },
  tableHeader: {
    padding: "10px 14px",
    background: "#f8f9fa",
    borderBottom: "1px solid #e0e0e0",
    display: "flex",
    alignItems: "center",
    gap: "10px",
  },
  tableName: {
    fontWeight: 700,
    fontSize: "0.95rem",
  },
  tableDesc: {
    fontSize: "0.8rem",
    color: "#666",
  },
  columnTable: {
    width: "100%",
    borderCollapse: "collapse",
    fontSize: "0.85rem",
  },
  th: {
    textAlign: "left",
    padding: "8px 14px",
    borderBottom: "1px solid #eee",
    color: "#888",
    fontWeight: 600,
    fontSize: "0.75rem",
    textTransform: "uppercase",
  },
  td: {
    padding: "6px 14px",
    borderBottom: "1px solid #f0f0f0",
  },
  code: {
    background: "#f0f0f0",
    padding: "2px 6px",
    borderRadius: "4px",
    fontSize: "0.8rem",
    fontFamily: "monospace",
  },
  type: {
    fontSize: "0.8rem",
    color: "#2563eb",
    fontFamily: "monospace",
  },
  meta: {
    fontSize: "0.8rem",
    color: "#666",
    marginBottom: "4px",
  },
  confirmBtn: {
    marginTop: "10px",
    padding: "8px 18px",
    borderRadius: "6px",
    border: "none",
    background: "#16a34a",
    color: "#fff",
    fontSize: "0.85rem",
    fontWeight: 600,
    cursor: "pointer",
  },
};
