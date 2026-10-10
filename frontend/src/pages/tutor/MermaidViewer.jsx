import { useEffect, useState, useRef } from "react";
import mermaid from "mermaid";

let mermaidInitialized = false;

function initMermaid() {
  if (!mermaidInitialized && typeof window !== "undefined") {
    try {
      mermaid.initialize({
        startOnLoad: false,
        securityLevel: "loose",
        theme: "neutral",
        fontFamily: "'Outfit', 'Inter', -apple-system, sans-serif",
        flowchart: {
          htmlLabels: true,
          curve: "basis",
          padding: 16,
        },
      });
      mermaidInitialized = true;
    } catch (e) {
      console.warn("Mermaid init warning:", e);
    }
  }
}

export default function MermaidViewer({ chart, title = "Process Flow Diagram" }) {
  const [svgHtml, setSvgHtml] = useState("");
  const [error, setError] = useState(null);
  const [showCode, setShowCode] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const containerRef = useRef(null);

  useEffect(() => {
    let isMounted = true;
    initMermaid();

    const cleanChart = (chart || "").trim();
    if (!cleanChart) {
      setIsLoading(false);
      return;
    }

    const uniqueId = `mermaid_diag_${Math.random().toString(36).substring(2, 9)}_${Date.now().toString(36)}`;

    async function renderChart() {
      setIsLoading(true);
      setError(null);
      try {
        const { svg } = await mermaid.render(uniqueId, cleanChart);
        if (isMounted) {
          setSvgHtml(svg);
          setIsLoading(false);
        }
      } catch (err) {
        console.warn("Mermaid render error:", err);
        if (isMounted) {
          setError(err?.message || "Could not parse diagram syntax");
          setIsLoading(false);
        }
      }
    }

    renderChart();

    return () => {
      isMounted = false;
      const el = document.getElementById(uniqueId);
      if (el) el.remove();
      const elD = document.getElementById(`d${uniqueId}`);
      if (elD) elD.remove();
    };
  }, [chart]);

  return (
    <div className="mermaid-viewer-card" aria-label="Process Flow Diagram">
      <div className="mermaid-viewer-header">
        <div className="mermaid-viewer-title">
          <span className="mermaid-icon" aria-hidden="true">📊</span>
          <span className="mermaid-label">{title}</span>
          <span className="mermaid-badge">Architecture Flow</span>
        </div>
        <button
          type="button"
          className="mermaid-toggle-btn"
          onClick={() => setShowCode(!showCode)}
          title={showCode ? "Show Visual Diagram" : "Show Diagram Definition"}
        >
          {showCode ? "Show Visual" : "View Code"}
        </button>
      </div>

      {showCode ? (
        <pre className="mermaid-code-view">
          <code>{chart}</code>
        </pre>
      ) : (
        <div className="mermaid-diagram-canvas" ref={containerRef}>
          {isLoading && (
            <div className="mermaid-loading">
              <span className="mermaid-spinner" /> Generating visual architecture...
            </div>
          )}

          {!isLoading && error && (
            <div className="mermaid-fallback-box">
              <p className="mermaid-error-hint">
                Visual flow preview unavailable: showing definition below.
              </p>
              <pre className="mermaid-code-fallback">
                <code>{chart}</code>
              </pre>
            </div>
          )}

          {!isLoading && !error && svgHtml && (
            <div
              className="mermaid-svg-container"
              dangerouslySetInnerHTML={{ __html: svgHtml }}
            />
          )}
        </div>
      )}
    </div>
  );
}
