import React, { createContext, useContext } from 'react';

const ThemeContext = createContext();

/**
 * FleetGuard Theme Provider — Fixed Light Theme
 * The application uses a single cohesive light theme.
 * This provider is kept for API compatibility but no longer toggles themes.
 */
export function ThemeProvider({ children }) {
  // Ensure no dark class remnants on the root element
  document.documentElement.classList.remove('dark');

  const value = {
    theme: 'light',
    resolvedTheme: 'light',
    setTheme: () => {},      // no-op — fixed theme
    toggleTheme: () => {},   // no-op — fixed theme
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useTheme = () => useContext(ThemeContext);
