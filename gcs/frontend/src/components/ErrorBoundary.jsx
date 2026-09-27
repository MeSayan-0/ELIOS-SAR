import React from "react";

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.warn("Caught in ErrorBoundary:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 24, color: "#fff", background: "#111", fontFamily: "monospace" }}>
          <h2>System Display Notice</h2>
          <p style={{ color: "#ff6b6b" }}>{this.state.error?.message || "An unexpected error occurred."}</p>
          <button
            style={{
              padding: "8px 16px",
              background: "#333",
              color: "#fff",
              border: "1px solid #555",
              cursor: "pointer",
            }}
            onClick={() => this.setState({ hasError: false, error: null })}
          >
            Retry
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
