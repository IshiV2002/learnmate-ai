import { useEffect } from "react";

import Button from "../ui/Button.jsx";
import Icon from "../ui/Icon.jsx";
import Brand from "./Brand.jsx";
import Navigation from "./Navigation.jsx";

function MobileNavigation({ currentPage, onClose, onNavigate }) {
  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    function handleEscape(event) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = previousOverflow;
    };
  }, [onClose]);

  return (
    <div className="mobile-navigation">
      <button
        aria-label="Close navigation menu"
        className="mobile-navigation-backdrop"
        onClick={onClose}
        type="button"
      />
      <aside aria-label="Mobile navigation" aria-modal="true" className="mobile-navigation-panel" role="dialog">
        <div className="mobile-navigation-header">
          <Brand onNavigate={onNavigate} />
          <Button
            aria-label="Close navigation menu"
            autoFocus
            icon={<Icon name="close" />}
            onClick={onClose}
          />
        </div>
        <Navigation currentPage={currentPage} onNavigate={onNavigate} />
      </aside>
    </div>
  );
}

export default MobileNavigation;
