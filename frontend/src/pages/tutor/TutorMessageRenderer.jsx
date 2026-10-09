import { useMemo } from "react";

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

export default function TutorMessageRenderer({ content }) {
  const blocks = useMemo(() => {
    if (!content) return [];
    return content.split(/\n\n+/).filter(Boolean);
  }, [content]);

  if (!blocks.length) return null;

  return (
    <div className="tutor-formatted-message">
      {blocks.map((block, idx) => {
        const trimmed = block.trim();

        // Level 4 Heading (###)
        if (trimmed.startsWith("### ")) {
          return (
            <h4 key={idx} className="tutor-md-h4">
              {renderFormattedInline(trimmed.slice(4).trim())}
            </h4>
          );
        }

        // Level 3 Heading (##)
        if (trimmed.startsWith("## ")) {
          return (
            <h3 key={idx} className="tutor-md-h3">
              {renderFormattedInline(trimmed.slice(3).trim())}
            </h3>
          );
        }

        // Blockquote (> ...)
        if (trimmed.startsWith("> ")) {
          return (
            <blockquote key={idx} className="tutor-md-quote">
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
            <ul key={idx} className="tutor-md-ul">
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
            <ol key={idx} className="tutor-md-ol">
              {lines.map((line, lIdx) => (
                <li key={lIdx}>
                  {renderFormattedInline(line.replace(/^\d+\.\s*/, ""))}
                </li>
              ))}
            </ol>
          );
        }

        // Regular paragraph with soft line breaks
        return (
          <p key={idx} className="tutor-md-p">
            {lines.map((line, lineIdx) => (
              <span key={lineIdx}>
                {renderFormattedInline(line)}
                {lineIdx < lines.length - 1 && <br />}
              </span>
            ))}
          </p>
        );
      })}
    </div>
  );
}
