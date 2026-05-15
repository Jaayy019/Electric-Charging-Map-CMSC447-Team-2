import { getMarkerIcon, hasMultipleTypes } from "./MapView";
import L from "leaflet";

// Map Icon Logic Tests
describe("MapView: Icon Selection", () => {

  test("returns Tesla icon for Tesla charger types", () => {
    const icon = getMarkerIcon('NACS / Tesla Supercharger');
    expect(icon.iconUrl).toContain('marker_tesla');
    
    const icon2 = getMarkerIcon('Tesla (Model S/X)');
    expect(icon2.iconUrl).toContain('marker_tesla');
  });

  test("returns CCS1 icon for CCS (Type 1)", () => {
    const icon = getMarkerIcon('CCS (Type 1)');
    expect(icon.iconUrl).toContain('marker_ccs1');
  });

  test("returns CHAdeMO icon for CHAdeMO", () => {
    const icon = getMarkerIcon('CHAdeMO');
    expect(icon.iconUrl).toContain('marker_chademo');
  });

  test("returns default icon for unknown types", () => {
    const icon = getMarkerIcon('Unknown Type');
    expect(icon.iconUrl).toContain('marker_default');
  });

  test("returns Multiple icon for Multiple type", () => {
    const icon = getMarkerIcon('Multiple');
    expect(icon.iconUrl).toContain('marker_multi');
  });

});

describe("MapView: Multiple Types detection", () => {

  test("returns true if multiple connections exist", () => {
    const station = {
      connections: [
        { port_type: 'CCS (Type 1)' },
        { port_type: 'CHAdeMO' }
      ]
    };
    expect(hasMultipleTypes(station)).toBe(true);
  });

  test("returns false if only one connection exists", () => {
    const station = {
      connections: [
        { port_type: 'CCS (Type 1)' }
      ]
    };
    expect(hasMultipleTypes(station)).toBe(false);
  });

  test("returns false if connections is empty or missing", () => {
    expect(hasMultipleTypes({})).toBe(false);
    expect(hasMultipleTypes({ connections: [] })).toBe(false);
  });

});
