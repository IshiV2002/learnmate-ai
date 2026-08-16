import { useEffect, useRef, useState } from "react";

import AmbientBackground from "./AmbientBackground.jsx";
import MobileNavigation from "./MobileNavigation.jsx";
import Sidebar from "./Sidebar.jsx";
import TopBar from "./TopBar.jsx";

function AppShell({ children, currentPage, onNavigate }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const contentRef = useRef(null);
  const previousPage = useRef(currentPage);

  useEffect(() => {
    setMobileMenuOpen(false);

    if (previousPage.current !== currentPage) {
      contentRef.current?.focus({ preventScroll: true });
      previousPage.current = currentPage;
    }
  }, [currentPage]);

  function handleNavigate(pageId) {
    onNavigate(pageId);
    setMobileMenuOpen(false);
  }

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <AmbientBackground />
      <Sidebar currentPage={currentPage} onNavigate={handleNavigate} />

      <div className="app-workspace">
        <TopBar currentPage={currentPage} onOpenMenu={() => setMobileMenuOpen(true)} />
        <main className="app-content" id="main-content" ref={contentRef} tabIndex={-1}>
          <div className="app-page-frame" key={currentPage}>{children}</div>
        </main>
      </div>

      {mobileMenuOpen && (
        <MobileNavigation
          currentPage={currentPage}
          onClose={() => setMobileMenuOpen(false)}
          onNavigate={handleNavigate}
        />
      )}
    </div>
  );
}

export default AppShell;
