function Brand({ onNavigate }) {
  return (
    <button className="app-brand" onClick={() => onNavigate("home")} type="button">
      <span className="app-brand-mark" aria-hidden="true">LM</span>
      <span className="app-brand-copy">
        <strong>LearnMate</strong>
        <small>Study workspace</small>
      </span>
    </button>
  );
}

export default Brand;
