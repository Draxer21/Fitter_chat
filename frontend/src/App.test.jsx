import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import App from "./App";

// stub window.scrollTo for jsdom
vi.stubGlobal("scrollTo", vi.fn());

describe("App", () => {
  it("renders the navbar and skip-link", () => {
    render(<App />);
    expect(screen.getByRole("navigation")).toBeInTheDocument();
    expect(screen.getByText(/skip to main content|saltar al contenido/i)).toBeInTheDocument();
  });

  it("renders the login CTA for unauthenticated users", () => {
    render(<App />);
    const loginLink = screen.getByRole("menuitem", { name: /iniciar sesión/i });
    expect(loginLink).toBeInTheDocument();
    expect(loginLink).toHaveAttribute("href", "/login");
  });

  it("renders the brand logo", () => {
    render(<App />);
    expect(screen.getByAltText(/fitter/i)).toBeInTheDocument();
  });
});
