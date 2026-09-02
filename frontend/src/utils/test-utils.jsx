import React from 'react';
import { render } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { ToastProvider } from '@/components/ui/Toast';
import { LanguageProvider } from '@/i18n/LanguageContext';
import { ThemeProvider } from '@/theme/ThemeContext';

const AllTheProviders = ({ children }) => {
  return (
    <ThemeProvider>
      <LanguageProvider>
        <ToastProvider>
          {children}
        </ToastProvider>
      </LanguageProvider>
    </ThemeProvider>
  );
};

const customRender = (ui, { route = '/', ...options } = {}) => {
  window.history.pushState({}, 'Test page', route);

  return render(ui, {
    wrapper: ({ children }) => (
      <BrowserRouter>
        <AllTheProviders>{children}</AllTheProviders>
      </BrowserRouter>
    ),
    ...options,
  });
};

const customRenderWithMemoryRouter = (ui, { initialEntries = ['/'], ...options } = {}) => {
  return render(ui, {
    wrapper: ({ children }) => (
      <MemoryRouter initialEntries={initialEntries}>
        <AllTheProviders>{children}</AllTheProviders>
      </MemoryRouter>
    ),
    ...options,
  });
};

export * from '@testing-library/react';
export { customRender as render, customRenderWithMemoryRouter as renderWithMemoryRouter };
