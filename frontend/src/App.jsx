import { useEffect, useState } from "react";

import AppShell from "./components/layout/AppShell.jsx";
import { useAuth } from "./auth/AuthContext.jsx";
import Auth from "./pages/Auth.jsx";
import Home from "./pages/Home.jsx";
import Materials from "./pages/Materials.jsx";
import Plans from "./pages/Plans.jsx";
import Quiz from "./pages/Quiz.jsx";
import Recommendations from "./pages/Recommendations.jsx";
import Tutor from "./pages/Tutor.jsx";
import { useTheme } from "./theme/useTheme.js";

function App() {
  const { user, isAuthLoading, completeAuthentication, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [currentPage, setCurrentPage] = useState("home");
  const [handoffSubmission, setHandoffSubmission] = useState(null);
  const [handoffRecommendation, setHandoffRecommendation] = useState(null);
  const [tutorHandoff, setTutorHandoff] = useState(null);
  const [showPlans, setShowPlans] = useState(
    () => window.location.pathname === "/plans",
  );

  useEffect(() => {
    function handleBrowserNavigation() {
      setShowPlans(window.location.pathname === "/plans");
    }

    window.addEventListener("popstate", handleBrowserNavigation);
    return () => window.removeEventListener("popstate", handleBrowserNavigation);
  }, []);

  function openPlans() {
    if (window.location.pathname !== "/plans") {
      window.history.pushState({}, "", "/plans");
    }
    setShowPlans(true);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function closePlans() {
    if (window.location.pathname === "/plans") {
      window.history.pushState({}, "", "/");
    }
    setShowPlans(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

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

  function handleAuthentication(authentication) {
    setCurrentPage("home");
    completeAuthentication(authentication);
  }

  if (showPlans) {
    return (
      <Plans
        isAuthenticated={Boolean(user)}
        onGetStarted={closePlans}
        onToggleTheme={toggleTheme}
        theme={theme}
      />
    );
  }

  if (isAuthLoading) {
    return <div className="auth-loading">Restoring your secure workspace…</div>;
  }

  if (!user) {
    return (
      <Auth
        onAuthenticated={handleAuthentication}
        onViewPlans={openPlans}
      />
    );
  }

  return (
    <AppShell
      currentPage={currentPage}
      onLogout={logout}
      onNavigate={setCurrentPage}
      onToggleTheme={toggleTheme}
      onViewPlans={openPlans}
      theme={theme}
      user={user}
    >
      {currentPage === "home" && <Home onNavigate={setCurrentPage} user={user} />}
      {currentPage === "materials" && <Materials />}
      {currentPage === "quiz" && (
        <Quiz onNavigateToRecommendations={handleNavigateToRecommendations} />
      )}
      {currentPage === "recommendations" && (
        <Recommendations
          initialSubmission={handoffSubmission}
          initialRecommendation={handoffRecommendation}
          onLaunchTutor={handleLaunchTutorHandoff}
          onToggleTheme={toggleTheme}
          theme={theme}
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
