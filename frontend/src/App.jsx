import { useCallback, useEffect, useState } from "react";

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
import {
  getNavigationDirection,
  getNavigationTransition,
} from "./components/layout/navigation.js";

function App() {
  const { user, isAuthLoading, completeAuthentication, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [currentPage, setCurrentPage] = useState("home");
  const [navigationDirection, setNavigationDirection] = useState("forward");
  const [navigationTransition, setNavigationTransition] = useState("soft");
  const [playEntryAnimation, setPlayEntryAnimation] = useState(false);
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

  function navigateToPage(nextPage) {
    if (nextPage === currentPage) {
      return;
    }

    setNavigationDirection(getNavigationDirection(currentPage, nextPage));
    setNavigationTransition(getNavigationTransition(currentPage, nextPage));
    setCurrentPage(nextPage);
  }

  function handleNavigateToRecommendations(data) {
    if (data && data.recommendation_id) {
      setHandoffRecommendation(data);
      setHandoffSubmission(null);
    } else if (data && data.questions) {
      setHandoffSubmission(data);
      setHandoffRecommendation(null);
    }
    navigateToPage("recommendations");
  }

  const handleLaunchTutorHandoff = (handoff) => {
    setTutorHandoff(handoff);
    navigateToPage("tutor");
  };

  function handleAuthentication(authentication, authenticationMode) {
    setNavigationDirection("forward");
    setNavigationTransition("soft");
    setCurrentPage("home");
    setPlayEntryAnimation(authenticationMode === "login");
    completeAuthentication(authentication);
  }

  function handleLogout() {
    setPlayEntryAnimation(false);
    logout();
  }

  const finishEntryAnimation = useCallback(() => {
    setPlayEntryAnimation(false);
  }, []);

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
      navigationDirection={navigationDirection}
      navigationTransition={navigationTransition}
      onEntryAnimationComplete={finishEntryAnimation}
      onLogout={handleLogout}
      onNavigate={navigateToPage}
      onToggleTheme={toggleTheme}
      onViewPlans={openPlans}
      playEntryAnimation={playEntryAnimation}
      theme={theme}
      user={user}
    >
      {currentPage === "home" && <Home onNavigate={navigateToPage} user={user} />}
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
