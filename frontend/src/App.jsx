import Materials from "./pages/Materials.jsx";

function App() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="LearnMate AI home">
          <span className="brand-mark" aria-hidden="true">
            LM
          </span>
          <span>
            <strong>LearnMate</strong>
            <small>AI learning assistant</small>
          </span>
        </a>

        <nav aria-label="Main navigation">
          <span className="nav-item nav-item-active" aria-current="page">
            Materials
          </span>
        </nav>
      </header>

      <main>
        <Materials />
      </main>
    </div>
  );
}

export default App;
