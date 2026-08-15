import { useState } from "react";
import Materials from "./pages/Materials.jsx";
import Recommendations from "./pages/Recommendations.jsx";
import Tutor from "./pages/Tutor.jsx";

function App() {
  const [currentPage, setCurrentPage] = useState("recommendations");
  const [tutorHandoff, setTutorHandoff] = useState(null);

  const handleLaunchTutorHandoff = (handoff) => {
    setTutorHandoff(handoff);
    setCurrentPage("tutor");
  };

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
          <button
            type="button"
            className={`nav-item ${currentPage === "tutor" ? "nav-item-active" : ""}`}
            onClick={() => setCurrentPage("tutor")}
          >
            💬 Socratic AI Tutor
          </button>
        </nav>
      </header>

      <main>
        {currentPage === "materials" && <Materials />}
        {currentPage === "recommendations" && (
          <Recommendations onLaunchTutor={handleLaunchTutorHandoff} />
        )}
        {currentPage === "tutor" && (
          <Tutor
            initialHandoff={tutorHandoff}
            onClearHandoff={() => setTutorHandoff(null)}
          />
        )}
      </main>
    </div>
  );
}

export default App;

