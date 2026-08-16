import { useState } from "react";

import AppShell from "./components/layout/AppShell.jsx";
import Materials from "./pages/Materials.jsx";
import Quiz from "./pages/Quiz.jsx";
import Recommendations from "./pages/Recommendations.jsx";
import Tutor from "./pages/Tutor.jsx";

function App() {
  const [currentPage, setCurrentPage] = useState("quiz");
  const [handoffSubmission, setHandoffSubmission] = useState(null);
  const [handoffRecommendation, setHandoffRecommendation] = useState(null);
  const [tutorHandoff, setTutorHandoff] = useState(null);

  function handleNavigateToRecommendations(data) {
    if (data && data.recommendation_id) {
      setHandoffRecommendation(data);
      setHandoffSubmission(null);
    } else if (data && data.questions) {
      setHandoffSubmission(data);
      setHandoffRecommendation(null);
    }
    setCurrentPage("recommendations");
  }

  const handleLaunchTutorHandoff = (handoff) => {
    setTutorHandoff(handoff);
    setCurrentPage("tutor");
  };

  return (
    <AppShell currentPage={currentPage} onNavigate={setCurrentPage}>
      {currentPage === "materials" && <Materials />}
      {currentPage === "quiz" && (
        <Quiz onNavigateToRecommendations={handleNavigateToRecommendations} />
      )}
      {currentPage === "recommendations" && (
        <Recommendations
          initialSubmission={handoffSubmission}
          initialRecommendation={handoffRecommendation}
          onLaunchTutor={handleLaunchTutorHandoff}
        />
      )}
      {currentPage === "tutor" && (
        <Tutor
          initialHandoff={tutorHandoff}
          onClearHandoff={() => setTutorHandoff(null)}
        />
      )}
    </AppShell>
  );
}

export default App;
