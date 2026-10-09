function LibraryGraphic() {
  return (
    <svg
      aria-hidden="true"
      className="library-graphic"
      fill="none"
      viewBox="0 0 420 260"
    >
      <path
        className="library-graphic-folder"
        d="M54 76c0-9 7-16 16-16h92l22 24h166c9 0 16 7 16 16v112c0 9-7 16-16 16H70c-9 0-16-7-16-16V76Z"
      />
      <rect
        className="library-graphic-page library-graphic-page-back"
        height="154"
        rx="12"
        transform="rotate(-5 112 38)"
        width="222"
        x="112"
        y="38"
      />
      <rect
        className="library-graphic-page library-graphic-page-front"
        height="158"
        rx="12"
        width="226"
        x="126"
        y="52"
      />
      <path className="library-graphic-heading" d="M154 85h92" />
      <path className="library-graphic-lines" d="M154 111h164M154 130h142M154 149h164M154 168h104" />
      <path className="library-graphic-margin" d="M142 72v116" />
      <path className="library-graphic-bookmark" d="M286 52v54l17-11 17 11V52" />
      <circle className="library-graphic-mark" cx="326" cy="176" r="11" />
      <path className="library-graphic-check" d="m321 176 4 4 7-8" />
      <path className="library-graphic-shadow" d="M74 232h278" />
    </svg>
  );
}

export default LibraryGraphic;
