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
];

export function getNavigationItem(pageId) {
  return navigationItems.find((item) => item.id === pageId) || navigationItems[0];
}
