export function validateEmail(email) {
  return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.trim());
}

export function validatePassword(password) {
  return (
    password.length >= 8 &&
    /[a-z]/.test(password) &&
    /[A-Z]/.test(password) &&
    /\d/.test(password)
  );
}

export function validateSignupForm(values) {
  if (values.fullName.trim().length < 2) {
    return "Enter your full name.";
  }
  if (!validateEmail(values.email)) {
    return "Enter a valid email address.";
  }
  if (!validatePassword(values.password)) {
    return "Use 8 or more characters with uppercase, lowercase, and a number.";
  }
  if (values.password !== values.confirmPassword) {
    return "The passwords do not match.";
  }
  return "";
}
