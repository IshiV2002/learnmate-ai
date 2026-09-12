const iconPaths = {
  sparkles: (
    <>
      <path d="m12 3 1.912 5.813a2 2 0 0 0 1.275 1.275L21 12l-5.813 1.912a2 2 0 0 0-1.275 1.275L12 21l-1.912-5.813a2 2 0 0 0-1.275-1.275L3 12l5.813-1.912a2 2 0 0 0 1.275-1.275L12 3Z" />
      <path d="M5 3v4M3 5h4M19 17v4M17 19h4" />
    </>
  ),
  target: (
    <>
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5" />
      <circle cx="12" cy="12" r="1.5" fill="currentColor" />
    </>
  ),
  brain: (
    <>
      <path d="M9.5 4a3.5 3.5 0 0 0-3.5 3.5c0 .3.05.6.14.88A4 4 0 0 0 4 12a4 4 0 0 0 2 3.46 3.5 3.5 0 0 0 4 3.54h.5" />
      <path d="M14.5 4a3.5 3.5 0 0 1 3.5 3.5c0 .3-.05.6-.14.88A4 4 0 0 1 20 12a4 4 0 0 1-2 3.46 3.5 3.5 0 0 1-4 3.54h-.5" />
      <path d="M12 4v16M8 8h4M8 12h4M8 16h4M16 8h-4M16 12h-4M16 16h-4" />
    </>
  ),
  document: (
    <>
      <path d="M6 3h8l4 4v14H6V3Z" />
      <path d="M14 3v5h5M9 12h6M9 16h6" />
    </>
  ),
  pages: (
    <>
      <path d="M5 5h10v14H5z" />
      <path d="M9 2h10v14h-4M8 9h4M8 13h4" />
    </>
  ),
  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 3" />
    </>
  ),
  award: (
    <>
      <circle cx="12" cy="8" r="6" />
      <path d="m15.5 13.5 3.5 8.5-7-3.5-7 3.5 3.5-8.5" />
    </>
  ),
  trash: (
    <>
      <path d="M4 7h16M9 7V4h6v3M7 7l1 14h8l1-14M10 11v6M14 11v6" />
    </>
  ),
  refresh: <path d="M20 7v5h-5M4 17v-5h5M18.5 10A7 7 0 0 0 6 6.5L4 12m16 0-2 5.5A7 7 0 0 1 5.5 14" />,
  shield: <path d="M12 3 5 6v5c0 4.5 2.7 8.2 7 10 4.3-1.8 7-5.5 7-10V6l-7-3Zm-3 9 2 2 4-4" />,
  search: <path d="m20 20-4.3-4.3M18 10.5a7.5 7.5 0 1 1-15 0 7.5 7.5 0 0 1 15 0Z" />,
  check: <path d="m5 12 4 4L19 6" />,
  close: <path d="m6 6 12 12M18 6 6 18" />,
  layers: (
    <>
      <path d="m12 2 10 5-10 5L2 7l10-5Z" />
      <path d="m2 17 10 5 10-5M2 12l10 5 10-5" />
    </>
  ),
  play: <path d="m7 4 13 8-13 8V4Z" fill="currentColor" />,
  arrowLeft: <path d="m15 18-6-6 6-6" />,
  arrowRight: <path d="m9 18 6-6-6-6" />,
  help: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3M12 17h.01" />
    </>
  ),
  book: (
    <>
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z" />
    </>
  ),
};

function QuizIcon({ name, size = 20, className = "" }) {
  return (
    <svg
      aria-hidden="true"
      className={`quiz-icon ${className}`.trim()}
      fill="none"
      height={size}
      viewBox="0 0 24 24"
      width={size}
    >
      <g stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.7">
        {iconPaths[name] || iconPaths.target}
      </g>
    </svg>
  );
}

export default QuizIcon;
