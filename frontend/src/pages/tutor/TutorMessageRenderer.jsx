import { useMemo } from "react";
import MermaidViewer from "./MermaidViewer.jsx";

function renderFormattedInline(text) {
  if (!text) return null;

  // Split on bold (**...**), italic (*...*), code (`...`)
  const regex = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
  const parts = [];
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }

    const token = match[0];
    if (token.startsWith("**") && token.endsWith("**")) {
      parts.push(
        <strong key={`b_${match.index}`} className="tutor-md-bold">
          {token.slice(2, -2)}
        </strong>
      );
    } else if (token.startsWith("*") && token.endsWith("*")) {
      parts.push(
        <em key={`i_${match.index}`} className="tutor-md-italic">
          {token.slice(1, -1)}
        </em>
      );
    } else if (token.startsWith("`") && token.endsWith("`")) {
      parts.push(
        <code key={`c_${match.index}`} className="tutor-md-code">
          {token.slice(1, -1)}
        </code>
      );
    }

    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts.length > 0 ? parts : text;
}

function renderTextChunk(chunk, baseKey) {
  const subBlocks = chunk.split(/\n\n+/).filter(Boolean);

  return subBlocks.map((block, idx) => {
    const trimmed = block.trim();
    const key = `${baseKey}_${idx}`;

    // Level 4 Heading (###)
    if (trimmed.startsWith("### ")) {
      return (
        <h4 key={key} className="tutor-md-h4">
          {renderFormattedInline(trimmed.slice(4).trim())}
        </h4>
      );
    }

    // Level 3 Heading (##)
    if (trimmed.startsWith("## ")) {
      return (
        <h3 key={key} className="tutor-md-h3">
          {renderFormattedInline(trimmed.slice(3).trim())}
        </h3>
      );
    }

    // Blockquote (> ...)
    if (trimmed.startsWith("> ")) {
      return (
        <blockquote key={key} className="tutor-md-quote">
          {renderFormattedInline(trimmed.slice(2).trim())}
        </blockquote>
      );
    }

    const lines = trimmed.split("\n").map((l) => l.trim()).filter(Boolean);

    // Bullet List (- ... or • ...)
    const isBulletList =
      lines.length > 0 &&
      lines.every((l) => l.startsWith("- ") || l.startsWith("• ") || l.startsWith("* "));
    if (isBulletList) {
      return (
        <ul key={key} className="tutor-md-ul">
          {lines.map((line, lIdx) => (
            <li key={lIdx}>
              {renderFormattedInline(line.replace(/^[-•*]\s*/, ""))}
            </li>
          ))}
        </ul>
      );
    }

    // Numbered List (1. ...)
    const isNumberedList =
      lines.length > 0 && lines.every((l) => /^\d+\.\s/.test(l));
    if (isNumberedList) {
      return (
        <ol key={key} className="tutor-md-ol">
          {lines.map((line, lIdx) => (
            <li key={lIdx}>
              {renderFormattedInline(line.replace(/^\d+\.\s*/, ""))}
            </li>
          ))}
        </ol>
      );
    }

    // Regular paragraph
    return (
      <p key={key} className="tutor-md-p">
        {lines.map((line, lineIdx) => (
          <span key={lineIdx}>
            {renderFormattedInline(line)}
            {lineIdx < lines.length - 1 && <br />}
          </span>
        ))}
      </p>
    );
  });
}

function isMermaidCode(lang, code) {
  const lowerLang = (lang || "").toLowerCase().trim();
  if (lowerLang === "mermaid" || lowerLang === "diagram") return true;

  const trimmed = code.trim();
  return (
    trimmed.startsWith("graph ") ||
    trimmed.startsWith("flowchart ") ||
    trimmed.startsWith("sequenceDiagram") ||
    trimmed.startsWith("classDiagram") ||
    trimmed.startsWith("stateDiagram") ||
    trimmed.startsWith("erDiagram") ||
    trimmed.startsWith("pie ")
  );
}

export default function TutorMessageRenderer({ content }) {
  const parsedSections = useMemo(() => {
    if (!content) return [];

    const sections = [];
    const codeBlockRegex = /```(\w+)?\s*\n([\s\S]*?)```/g;
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(content)) !== null) {
      if (match.index > lastIndex) {
        const textBefore = content.slice(lastIndex, match.index).trim();
        if (textBefore) {
          sections.push({ type: "text", content: textBefore });
        }
      }

      const lang = match[1] || "";
      const code = match[2] || "";

      if (isMermaidCode(lang, code)) {
        sections.push({ type: "mermaid", code: code.trim(), lang });
      } else {
        sections.push({ type: "code", code: code.trim(), lang });
      }

      lastIndex = codeBlockRegex.lastIndex;
    }

    if (lastIndex < content.length) {
      const remaining = content.slice(lastIndex).trim();
      if (remaining) {
        sections.push({ type: "text", content: remaining });
      }
    }

    return sections;
  }, [content]);

  if (!parsedSections.length) return null;

  return (
    <div className="tutor-formatted-message">
      {parsedSections.map((sec, idx) => {
        if (sec.type === "mermaid") {
          return <MermaidViewer key={`sec_${idx}`} chart={sec.code} />;
        }
        if (sec.type === "code") {
          return (
            <pre key={`sec_${idx}`} className="tutor-md-pre">
              <code>{sec.code}</code>
            </pre>
          );
        }
        return renderTextChunk(sec.content, `sec_${idx}`);
      })}
    </div>
  );
}
