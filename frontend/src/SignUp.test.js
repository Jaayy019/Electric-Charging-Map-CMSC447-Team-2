import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import SignUp from "./SignUp";

// Mock the global fetch so we don't hit the real backend during tests
const mockFetch = (data, ok = true, status = 200) => {
  global.fetch = jest.fn().mockResolvedValue({
    ok,
    status,
    json: () => Promise.resolve(data),
  });
};

const defaultProps = {
  onLoginSuccess: jest.fn(),
  goToLogin: jest.fn(),
  goToMap: jest.fn(),
};

// SignUp Rendering Tests
describe("SignUp: Rendering", () => {

  test("renders sign-up form with email and password fields", () => {
    render(<SignUp {...defaultProps} />);
    
    expect(screen.getByText(/create an account/i)).toBeInTheDocument();
    expect(screen.getByText(/start finding chargers near you/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/you@example.com/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/at least 8 characters/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /create account/i })).toBeInTheDocument();
  });

  test("password field enforces minimum length of 8", () => {
    render(<SignUp {...defaultProps} />);
    const passwordInput = screen.getByPlaceholderText(/at least 8 characters/i);
    expect(passwordInput).toHaveAttribute("minLength", "8");
  });

});

// SignUp Interaction Tests
describe("SignUp: Interactions", () => {

  test("calls onLoginSuccess after successful sign-up", async () => {
    mockFetch({ message: "Account created" });
    
    render(<SignUp {...defaultProps} />);
    
    fireEvent.change(screen.getByPlaceholderText(/you@example.com/i), { target: { value: "newuser@example.com" } });
    fireEvent.change(screen.getByPlaceholderText(/at least 8 characters/i), { target: { value: "password123" } });
    fireEvent.click(screen.getByRole("button", { name: /create account/i }));
    
    await waitFor(() => expect(defaultProps.onLoginSuccess).toHaveBeenCalled());
  });

  test("shows backend error message on failed sign-up", async () => {
    mockFetch({ detail: "Email already registered" }, false, 409);
    
    render(<SignUp {...defaultProps} />);
    
    fireEvent.change(screen.getByPlaceholderText(/you@example.com/i), { target: { value: "existing@example.com" } });
    fireEvent.change(screen.getByPlaceholderText(/at least 8 characters/i), { target: { value: "password123" } });
    fireEvent.click(screen.getByRole("button", { name: /create account/i }));
    
    await waitFor(() => expect(screen.getByText(/email already registered/i)).toBeInTheDocument());
  });

  test("navigates to login page when Sign in is clicked", () => {
    render(<SignUp {...defaultProps} />);
    fireEvent.click(screen.getByText(/sign in/i));
    expect(defaultProps.goToLogin).toHaveBeenCalled();
  });

});
