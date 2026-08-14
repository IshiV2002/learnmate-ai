import { useState } from "react";
import Materials from "./pages/Materials.jsx";
import Recommendations from "./pages/Recommendations.jsx";

function App() {
  const [currentPage, setCurrentPage] = useState("recommendations");

  return (
    <div className="app-shell">
      <header className="topbar">
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            setCurrentPage("materials");
          }}
          aria-label="LearnMate AI home"
        >
          <span className="brand-mark" aria-hidden="true">
            LM
          </span>
          <span>
            <strong>LearnMate AI</strong>
            <small>Multi-Agent Learning Platform</small>
          </span>
        </a>

        <nav aria-label="Main navigation" className="nav-group">
          <button
            type="button"
            className={`nav-item ${currentPage === "materials" ? "nav-item-active" : ""}`}
            onClick={() => setCurrentPage("materials")}
          >
            📚 Materials & Retrieval
          </button>
          <button
            type="button"
            className={`nav-item ${currentPage === "recommendations" ? "nav-item-active" : ""}`}
            onClick={() => setCurrentPage("recommendations")}
          >
            🎯 Recommendations & AI Coach
          </button>
        </nav>
      </header>

      <main>
        {currentPage === "materials" && <Materials />}
        {currentPage === "recommendations" && <Recommendations />}
      </main>
    </div>
  );
}

export default App;
