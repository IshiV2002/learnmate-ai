const paths = {
  materials: (
    <>
      <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H11v16H6.5A2.5 2.5 0 0 0 4 21.5v-16Z" />
      <path d="M20 5.5A2.5 2.5 0 0 0 17.5 3H13v16h4.5a2.5 2.5 0 0 1 2.5 2.5v-16Z" />
    </>
  ),
  tutor: (
    <>
      <path d="M7 17.5 3.5 20l1-4A7.5 7.5 0 1 1 7 17.5Z" />
      <path d="M8.5 10h7M8.5 13.5H13" />
    </>
  ),
  quiz: (
    <>
      <path d="M9 5h10M9 12h10M9 19h10" />
      <path d="m3.5 5 1.2 1.2L7 3.8M3.5 12l1.2 1.2L7 10.8M3.5 19l1.2 1.2L7 17.8" />
    </>
  ),
  recommendations: (
    <>
      <path d="M12 3v5M12 16v5M3 12h5M16 12h5" />
      <path d="m5.6 5.6 3.1 3.1m6.6 6.6 3.1 3.1m0-12.8-3.1 3.1m-6.6 6.6-3.1 3.1" />
      <circle cx="12" cy="12" r="3" />
    </>
  ),
  menu: <path d="M4 7h16M4 12h16M4 17h16" />,
  close: <path d="m6 6 12 12M18 6 6 18" />,
  network: (
    <>
      <circle cx="6" cy="7" r="2" />
      <circle cx="18" cy="5" r="2" />
      <circle cx="16" cy="18" r="2" />
      <circle cx="5" cy="17" r="2" />
      <path d="m8 6 8-1M7.5 8.5l7 7.5M7 17h7M17.5 7l-1 9" />
    </>
  ),
};

function Icon({ name, size = 20, className = "" }) {
  return (
    <svg
      aria-hidden="true"
      className={`ui-icon ${className}`.trim()}
      fill="none"
      height={size}
      viewBox="0 0 24 24"
      width={size}
    >
      <g stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.7">
        {paths[name] || paths.network}
      </g>
    </svg>
  );
}

export default Icon;
