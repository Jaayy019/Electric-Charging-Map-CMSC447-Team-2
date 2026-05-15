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

// Global mock for react/leaflet to avoid ESM issues with Jest
jest.mock("react-leaflet", () => ({
    MapContainer: ({ children }) => <div data-testid="map-container">{children}</div>,
    TileLayer: () => null,
    Marker: () => null,
    useMap: () => ({ on: jest.fn(), getCenter: () => ({ lat: 0, lng: 0 }), getZoom: () => 10 }),
    Circle: () => null,
}));

// Global mock for leaflet
jest.mock("leaflet", () => {
    const mockL = { icon: jest.fn((options) => options) };
    return { ...mockL, default: mockL, __esModule: true };
});

// Mock window.scrollTo since JSDOM doesn't implement it
window.scrollTo = jest.fn();

// Mock Geolocation API to avoid "Geolocation not allowed" console errors
const mockGeolocation = {
    getCurrentPosition: jest.fn().mockImplementation((success) => success({ coords: { latitude: 38, longitude: -100, }, })),
    watchPosition: jest.fn(),
};
global.navigator.geolocation = mockGeolocation;
