const iconPaths = {
  sparkles: (
    <>
      <path d="m12 3 1.912 5.813a2 2 0 0 0 1.275 1.275L21 12l-5.813 1.912a2 2 0 0 0-1.275 1.275L12 21l-1.912-5.813a2 2 0 0 0-1.275-1.275L3 12l5.813-1.912a2 2 0 0 0 1.275-1.275L12 3Z" />
      <path d="M5 3v4M3 5h4M19 17v4M17 19h4" />
    </>
  ),
  brain: (
    <>
      <path d="M9.5 4a3.5 3.5 0 0 0-3.5 3.5c0 .3.05.6.14.88A4 4 0 0 0 4 12a4 4 0 0 0 2 3.46 3.5 3.5 0 0 0 4 3.54h.5" />
      <path d="M14.5 4a3.5 3.5 0 0 1 3.5 3.5c0 .3-.05.6-.14.88A4 4 0 0 1 20 12a4 4 0 0 1-2 3.46 3.5 3.5 0 0 1-4 3.54h-.5" />
      <path d="M12 4v16M8 8h4M8 12h4M8 16h4M16 8h-4M16 12h-4M16 16h-4" />
    </>
  ),
  ladder: (
    <>
      <path d="M6 3v18M18 3v18M6 7h12M6 12h12M6 17h12" />
    </>
  ),
  target: (
    <>
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5" />
      <circle cx="12" cy="12" r="1.5" fill="currentColor" />
    </>
  ),
  book: (
    <>
      <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z" />
      <path d="M6 6h10M6 10h10M6 14h6" />
    </>
  ),
  document: (
    <>
      <path d="M6 3h8l4 4v14H6V3Z" />
      <path d="M14 3v5h5M9 12h6M9 16h6" />
    </>
  ),
  message: (
    <>
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </>
  ),
  send: (
    <>
      <path d="m22 2-7 20-4-9-9-4Z" />
      <path d="M22 2 11 13" />
    </>
  ),
  search: (
    <>
      <path d="m20 20-4.3-4.3M18 10.5a7.5 7.5 0 1 1-15 0 7.5 7.5 0 0 1 15 0Z" />
    </>
  ),
  shield: (
    <path d="M12 3 5 6v5c0 4.5 2.7 8.2 7 10 4.3-1.8 7-5.5 7-10V6l-7-3Zm-3 9 2 2 4-4" />
  ),
  check: <path d="m5 12 4 4L19 6" />,
  close: <path d="m6 6 12 12M18 6 6 18" />,
  trash: (
    <>
      <path d="M4 7h16M9 7V4h6v3M7 7l1 14h8l1-14M10 11v6M14 11v6" />
    </>
  ),
  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 3" />
    </>
  ),
  history: (
    <>
      <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
      <path d="M3 3v5h5M12 7v5l4 2" />
    </>
  ),
  user: (
    <>
      <circle cx="12" cy="8" r="4" />
      <path d="M6 20v-2a6 6 0 0 1 12 0v2" />
    </>
  ),
  bot: (
    <>
      <rect x="4" y="8" width="16" height="12" rx="2" />
      <path d="M2 14h2M20 14h2M9 13v2M15 13v2M12 5v3M9 5h6" />
    </>
  ),
  lightbulb: (
    <>
      <path d="M9 18h6M10 22h4M12 2a7 7 0 0 0-7 7c0 2.38 1.19 4.47 3 5.74V17a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-2.26c1.81-1.27 3-3.36 3-5.74a7 7 0 0 0-7-7Z" />
    </>
  ),
  quote: (
    <>
      <path d="M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V20c0 1 0 1 1 1Z" />
      <path d="M15 21c3 0 7-1 7-8V5c0-1.25-.757-2.017-2-2h-4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2h.75c0 2.25.25 4-2.75 4v3c0 1 0 1 1 1Z" />
    </>
  ),
  layers: (
    <>
      <path d="m12 2 10 5-10 5L2 7l10-5Z" />
      <path d="m2 17 10 5 10-5M2 12l10 5 10-5" />
    </>
  ),
  refresh: (
    <path d="M20 7v5h-5M4 17v-5h5M18.5 10A7 7 0 0 0 6 6.5L4 12m16 0-2 5.5A7 7 0 0 1 5.5 14" />
  ),
  "arrow-right": <path d="M5 12h14M12 5l7 7-7 7" />,
  "chevron-right": <path d="m9 18 6-6-6-6" />,
};

export default function TutorIcon({
  name,
  size = 18,
  className = "",
  strokeWidth = 1.8,
}) {
  const content = iconPaths[name] || iconPaths.sparkles;

  return (
    <svg
      aria-hidden="true"
      className={`tutor-icon ${className}`.trim()}
      fill="none"
      height={size}
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={strokeWidth}
      viewBox="0 0 24 24"
      width={size}
    >
      {content}
    </svg>
  );
}
