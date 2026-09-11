import { createContext, useContext, useEffect, useState } from "react";

import { getCurrentUser, setApiAccessToken } from "../services/api.js";


const TOKEN_STORAGE_KEY = "learnmate_access_token";
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isAuthLoading, setIsAuthLoading] = useState(true);

  function logout() {
    sessionStorage.removeItem(TOKEN_STORAGE_KEY);
    setApiAccessToken(null);
    setUser(null);
    setIsAuthLoading(false);
  }

  function completeAuthentication(authentication) {
    sessionStorage.setItem(TOKEN_STORAGE_KEY, authentication.access_token);
    setApiAccessToken(authentication.access_token);
    setUser(authentication.user);
    setIsAuthLoading(false);
  }

  useEffect(() => {
    const storedToken = sessionStorage.getItem(TOKEN_STORAGE_KEY);
    if (!storedToken) {
      setIsAuthLoading(false);
      return;
    }

    setApiAccessToken(storedToken);
    getCurrentUser()
      .then(setUser)
      .catch(logout)
      .finally(() => setIsAuthLoading(false));
  }, []);

  useEffect(() => {
    window.addEventListener("learnmate:unauthorized", logout);
    return () => window.removeEventListener("learnmate:unauthorized", logout);
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, isAuthLoading, completeAuthentication, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }
  return context;
}
