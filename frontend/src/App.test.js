import { render, screen } from '@testing-library/react';
import App from './App';
// Replaced old test with this one
// As a more robust "sanity check" and because learn react link doesnt exist anymore.
test('renders login button', () => {
  render(<App />);
  const loginButton = screen.getByRole("button", { name: /login/i });
  expect(loginButton).toBeInTheDocument();
});
