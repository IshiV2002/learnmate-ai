export const navigationItems = [
  {
    id: "home",
    label: "Home",
    description: "Your study overview",
    title: "Home",
    icon: "home",
  },
  {
    id: "materials",
    label: "Materials",
    description: "Library & retrieval",
    title: "Materials Library",
    icon: "materials",
  },
  {
    id: "tutor",
    label: "Tutor",
    description: "Guided understanding",
    title: "Study Tutor",
    icon: "tutor",
  },
  {
    id: "quiz",
    label: "Quiz",
    description: "Active recall",
    title: "Quizzes & Assessments",
    icon: "quiz",
  },
  {
    id: "recommendations",
    label: "Recommendations",
    description: "Adaptive next steps",
    title: "Study Recommendations",
    icon: "recommendations",
  },
  {
    id: "account",
    label: "My Account",
    description: "Profile & activity",
    title: "My Account",
    icon: "account",
  },
];

const studyPageIds = new Set(["materials", "tutor", "quiz", "recommendations"]);

export function getNavigationItem(pageId) {
  return navigationItems.find((item) => item.id === pageId) || navigationItems[0];
}

export function getNavigationDirection(currentPageId, nextPageId) {
  const currentIndex = navigationItems.findIndex((item) => item.id === currentPageId);
  const nextIndex = navigationItems.findIndex((item) => item.id === nextPageId);

  if (currentIndex < 0 || nextIndex < 0 || nextIndex >= currentIndex) {
    return "forward";
  }

  return "backward";
}

export function getNavigationTransition(currentPageId, nextPageId) {
  return studyPageIds.has(currentPageId) && studyPageIds.has(nextPageId)
    ? "book"
    : "soft";
}
