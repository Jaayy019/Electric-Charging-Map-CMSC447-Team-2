// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// To help Suppress the harmless act warnings in React/Jest tests 
// that appear when components update state asynchronously during tests.
const originalError = console.error;
console.error = (...args) => {
    if (/act\(...\)/.test(args[0])) return;
    originalError.call(console, ...args);
};

