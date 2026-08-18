import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AuthForm } from "@/components/auth/auth-form";
import { ProtectedRoute } from "@/components/auth/protected-route";

jest.mock("@/lib/api", () => ({
  loginUser: jest.fn(),
  registerUser: jest.fn(),
  getCurrentUser: jest.fn(),
  logoutUser: jest.fn(),
}));

const mockPush = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockPush,
    refresh: jest.fn(),
  }),
}));

const { loginUser, registerUser, getCurrentUser } = jest.requireMock("@/lib/api");

describe("auth UI flow", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders login form and submits successfully", async () => {
    loginUser.mockResolvedValue({ user: { id: "1" }, csrf_token: "token" });

    render(<AuthForm mode="login" />);

    await userEvent.type(screen.getByLabelText("Email"), "user@example.com");
    await userEvent.type(screen.getByLabelText("Password"), "password123");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(loginUser).toHaveBeenCalledWith({
        email: "user@example.com",
        password: "password123",
      });
    });

    expect(mockPush).toHaveBeenCalledWith("/onboarding");
  });

  it("renders signup form and submits successfully", async () => {
    registerUser.mockResolvedValue({ user: { id: "1" }, csrf_token: "token" });

    render(<AuthForm mode="signup" />);

    await userEvent.type(screen.getByLabelText("Display name"), "Test User");
    await userEvent.type(screen.getByLabelText("Email"), "new@example.com");
    await userEvent.type(screen.getByLabelText("Password"), "password123");
    await userEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(registerUser).toHaveBeenCalledWith({
        email: "new@example.com",
        password: "password123",
        display_name: "Test User",
      });
    });

    expect(mockPush).toHaveBeenCalledWith("/onboarding");
  });

  it("redirects unauthenticated users away from protected routes", async () => {
    getCurrentUser.mockRejectedValue(new Error("Unauthorized"));

    render(<ProtectedRoute requireOnboarded={true}>children</ProtectedRoute>);

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/auth/login");
    });
  });
});
