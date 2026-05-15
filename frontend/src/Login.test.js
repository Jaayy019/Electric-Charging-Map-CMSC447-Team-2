import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import Login from "./Login";

// Mock the global fetch so we don't hit the real backend during tests
const mockFetch = (data, ok = true) => {
  global.fetch = jest.fn().mockResolvedValue({
    ok,
    json: () => Promise.resolve(data),
  });
};

const defaultProps = {
  onLoginSuccess: jest.fn(),
  goToSignUp: jest.fn(),
  goToMap: jest.fn(),
};

// Login Rendering Tests
describe("Login: Rendering", () => {

  test("renders login form with email and password fields", () => {
    render(<Login {...defaultProps} />);
    
    expect(screen.getByText(/welcome back/i)).toBeInTheDocument();
    expect(screen.getByText(/sign in to your account/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/you@example.com/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/••••••••/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });

  test("renders the logo and app name", () => {
    render(<Login {...defaultProps} />);
    expect(screen.getByText(/electric vehicle charge map/i)).toBeInTheDocument();
  });

});

// Login Interaction Tests
describe("Login: Interactions", () => {

  test("calls onLoginSuccess after successful sign-in", async () => {
    mockFetch({ message: "Success" });
    
    render(<Login {...defaultProps} />);
    
    fireEvent.change(screen.getByPlaceholderText(/you@example.com/i), { target: { value: "test@example.com" } });
    fireEvent.change(screen.getByPlaceholderText(/••••••••/i), { target: { value: "password123" } });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));
    
    await waitFor(() => expect(defaultProps.onLoginSuccess).toHaveBeenCalled());
  });

  test("shows error message on failed sign-in", async () => {
    mockFetch({ detail: "Invalid login" }, false);
    
    render(<Login {...defaultProps} />);
    
    fireEvent.change(screen.getByPlaceholderText(/you@example.com/i), { target: { value: "wrong@example.com" } });
    fireEvent.change(screen.getByPlaceholderText(/••••••••/i), { target: { value: "wrongpass" } });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));
    
    await waitFor(() => expect(screen.getByText(/invalid login/i)).toBeInTheDocument());
  });

  test("navigates to sign-up page when Create one is clicked", () => {
    render(<Login {...defaultProps} />);
    fireEvent.click(screen.getByText(/create one/i));
    expect(defaultProps.goToSignUp).toHaveBeenCalled();
  });

  test("navigates to map when Continue as guest is clicked", () => {
    render(<Login {...defaultProps} />);
    fireEvent.click(screen.getByText(/continue as guest/i));
    expect(defaultProps.goToMap).toHaveBeenCalled();
  });

});
