function Brand({ onNavigate }) {
  return (
    <button className="app-brand" onClick={() => onNavigate("materials")} type="button">
      <span className="app-brand-mark" aria-hidden="true">LM</span>
      <span className="app-brand-copy">
        <strong>LearnMate AI</strong>
        <small>Knowledge Universe</small>
      </span>
    </button>
  );
}

export default Brand;
