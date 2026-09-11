import test from "node:test";
import assert from "node:assert/strict";

import {
  validateEmail,
  validatePassword,
  validateSignupForm,
} from "./authUtils.js";


test("validates email and strong-password requirements", () => {
  assert.equal(validateEmail("student@example.com"), true);
  assert.equal(validateEmail("not-an-email"), false);
  assert.equal(validatePassword("LearnMate9"), true);
  assert.equal(validatePassword("weakpass"), false);
});

test("signup validation rejects mismatched passwords", () => {
  const message = validateSignupForm({
    fullName: "Student One",
    email: "student@example.com",
    password: "LearnMate9",
    confirmPassword: "LearnMate8",
  });

  assert.equal(message, "The passwords do not match.");
});

test("signup validation accepts complete valid details", () => {
  const message = validateSignupForm({
    fullName: "Student One",
    email: "student@example.com",
    password: "LearnMate9",
    confirmPassword: "LearnMate9",
  });

  assert.equal(message, "");
});
