"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";

const STORAGE_KEY = "track_user_id";

interface UserContextValue {
  userId: string;
  setUserId: (id: string) => void;
}

const UserContext = createContext<UserContextValue>({ userId: "u1", setUserId: () => {} });

export function UserProvider({ children }: { children: ReactNode }) {
  const [userId, setUserIdState] = useState("u1");

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) setUserIdState(stored);
    } catch {
      /* private mode / storage blocked — default stands */
    }
  }, []);

  const setUserId = (id: string) => {
    setUserIdState(id);
    try {
      localStorage.setItem(STORAGE_KEY, id);
    } catch {
      /* ignore */
    }
  };

  return <UserContext.Provider value={{ userId, setUserId }}>{children}</UserContext.Provider>;
}

export const useUser = () => useContext(UserContext);
