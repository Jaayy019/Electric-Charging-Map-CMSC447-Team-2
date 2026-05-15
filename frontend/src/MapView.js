//Imports the necessary leaflet map components
import { MapContainer, TileLayer, Marker, useMap, Circle, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import chargerIcon from "./icons/marker_default.png"
import chargerType1Icon from "./icons/marker_type1.png"
import chargerType2Icon from "./icons/marker_type2.png"
import chargerTeslaIcon from "./icons/marker_tesla.png"
import chargerCcs1Icon from "./icons/marker_ccs1.png"
import chargerCcs2Icon from "./icons/marker_ccs2.png"
import chargerChademoIcon from "./icons/marker_chademo.png"
import chargerNema5Icon from "./icons/marker_nema5.png"
import chargerNema14Icon from "./icons/marker_nema14.png"
import chargerMultipleIcon from "./icons/marker_multi.png"
import { useEffect, useState, useRef } from "react";

// Smooth slide-in animation for the station detail panel (right side)
const panelAnimation =
`@keyframes slideInPanel {
  0% {
    transform: translateX(100%);
    opacity: 0;
  }
  100% {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes slideInLeft {
  0% {
    transform: translateX(-100%);
    opacity: 0;
  }
  100% {
    transform: translateX(0);
    opacity: 1;
  }
}`;

const styleTag = document.createElement("style");
styleTag.innerHTML = panelAnimation;
document.head.appendChild(styleTag);

const chargeIcon = {

  iconUrl: chargerIcon,
  iconSize: [40, 40],
  iconAnchor: [20, 40],
  popupAnchor: [0, -40]

};

function getMarkerIcon(type) {

  const iconUrls = {
    'NACS / Tesla Supercharger': chargerTeslaIcon,
    'Tesla (Model S/X)': chargerTeslaIcon,
    'Type 1 (J1772)': chargerType1Icon,
    'Type 2 (Socket Only)': chargerType2Icon,
    'CCS (Type 1)': chargerCcs1Icon,
    'CCS (Type 2)': chargerCcs2Icon,
    'CHAdeMO': chargerChademoIcon,
    'NEMA 5-15R': chargerNema5Icon,
    'NEMA 5-20R': chargerNema5Icon,
    'NEMA 14-50': chargerNema14Icon,
    'Multiple': chargerMultipleIcon,
    'default': chargerIcon
  };

  return L.icon({
    ...chargeIcon,
    iconUrl: iconUrls[type] || iconUrls['default']
  });

}

const hasMultipleTypes = (station) => {

  if (station.connections?.[1]?.port_type) return true
  else return false

};

// Many EVs can charge on multiple connector types. This maps a vehicle's saved
// port_type to ALL compatible station port types so filtering works correctly.
const PORT_COMPATIBILITY = {
  "Tesla (NACS)": [
    "NACS / Tesla Supercharger",
    "Tesla (Model S/X)",
    "CCS (Type 1)",
    "Type 1 (J1772)",
  ],
  "CCS (Type 1)": [
    "CCS (Type 1)",
    "Type 1 (J1772)",
  ],
  "CCS (Type 2)": [
    "CCS (Type 2)",
    "Type 2 (Socket Only)",
  ],
  "Type 1 (J1772)": [
    "Type 1 (J1772)",
    "CCS (Type 1)",
  ],
  "Type 2 (Mennekes)": [
    "Type 2 (Socket Only)",
    "CCS (Type 2)",
  ],
  "CHAdeMO": [
    "CHAdeMO",
  ],
  "Nema 14-50": [
    "NEMA 14-50",
  ],
  "Nema 5-15": [
    "NEMA 5-15R",
    "NEMA 5-20R",
  ],
};

// Returns true if a station has at least one connection compatible with the
// vehicle's port type, using the multi-port compatibility map above.
function stationMatchesVehicle(station, vehiclePortType) {

  const compatiblePorts = PORT_COMPATIBILITY[vehiclePortType];

  if (!compatiblePorts) {

    // Fallback for unknown port types — substring match
    const vp = vehiclePortType.toLowerCase();
    return station.connections?.some((c) => {
      const sp = (c.port_type || "").toLowerCase();
      return sp.includes(vp) || vp.includes(sp);
    });

  }

  return station.connections?.some((c) =>
    compatiblePorts.includes(c.port_type)
  );

}


function requestUserLocation(callback) {

  // Quick check if the browser supports it
  if (!navigator.geolocation) {

    console.error("Geolocation not allowed");
    return;

  }

  navigator.geolocation.getCurrentPosition(

    // Gets the users position
    (pos) => {

      const { latitude, longitude } = pos.coords;
      callback(latitude, longitude);

    },

    (err) => {

      console.error("User denied providing their location:", err);

    }

  );

}

// Calls the OCM API and gets stations within the given distance radius
function fetchStationsNearby(lat, lng, setStations, distance = 5) {

  fetch(`/api/charge-points?latitude=${lat}&longitude=${lng}&distance=${distance}`)
    .then(res => res.json())
    .then(data => setStations(data.data || []))
    .catch(err => console.error("Could not fetch station data:", err));

}


// Handles all events for when certain map actions occur
function EventHandler() {

  const map = useMap();

  // Handles the moveend function
  useEffect(() => {

    map.on('moveend', function () {

      // Gets center (LatitudeLongitude) and the zoom level
      var center = map.getCenter();
      var zoom = map.getZoom();

      saveLocal(center.lat, center.lng, zoom);

    });

  }, [map]);

  return null;

}

function saveLocal(lat, lng, zoom) {

  // Sets the center and zoom to local storage so it can be loaded later
  localStorage.setItem('lat', lat);
  localStorage.setItem('lng', lng);
  localStorage.setItem('zoom', zoom);

}

function LoadMap({ userLocation }) {

  const map = useMap();

  useEffect(() => {

    // Converts the string numbers into actual numbers
    const lat = parseFloat(localStorage.getItem("lat"));
    const lng = parseFloat(localStorage.getItem("lng"));
    const zoom = parseFloat(localStorage.getItem("zoom"));

    // Makes sure that parseFloat actually returns numbers
    if (!isNaN(lat) && !isNaN(lng) && !isNaN(zoom)) {

      map.setView([lat, lng], zoom);

    }

    else if (userLocation) {

      map.setView([userLocation.lat, userLocation.lng], 13);

    }

  }, [map, userLocation]);

  return null;

}

// Listens for map clicks and calls onMapClick with the lat/lng
function MapClickHandler({ onMapClick }) {

  useMapEvents({

    click(e) {

      onMapClick(e.latlng.lat, e.latlng.lng);

    },

  });

  return null;

}

export default function MapView({ user, goToLogin, handleLogout, goToVehicles }) {

  // Sets up the arrays to store station data
  const [stations, setStations] = useState([]);
  const [selectedStation, setSelectedStation] = useState(null);
  const [userLocation, setUserLocation] = useState(null);
  const [markerKey, setMarkerKey] = useState(null);

  // clickedLocation: set when user clicks the map, used as search center instead of userLocation
  const [clickedLocation, setClickedLocation] = useState(null);

  // portFilter: set by clicking icons in the marker key legend
  // Empty array = show all, otherwise filters by port type string(s)
  const [portFilter, setPortFilter] = useState([]);

  // Vehicle selector panel state
  const [vehiclePanelOpen, setVehiclePanelOpen] = useState(false);

  // List of the user's saved vehicles fetched from the backend
  const [vehicles, setVehicles] = useState([]);

  // The currently active vehicle id
  const [activeVehicleId, setActiveVehicleId] = useState(null);

  // True while the active vehicle PUT is in flight
  const [settingActive, setSettingActive] = useState(false);

  // Distance filter
  const [filterDistance, setFilterDistance] = useState(5);

  // Pricing filter 
  const [filterPricingOnly, setFilterPricingOnly] = useState(false);

  // Debounce timer ref so the distance slider doesn't spam the API
  const distanceTimer = useRef(null);

  // Gets the user location and then gets the stations
  useEffect(() => {

    requestUserLocation((lat, lng) => {

      setUserLocation({ lat, lng });
      fetchStationsNearby(lat, lng, setStations, 5);

    });

  }, []);

  useEffect(() => {

    console.log("Stations received:", stations);

  }, [stations]);

  useEffect(() => {

    if (!user) {

      // Clear vehicle state on logout
      setVehicles([]);
      setActiveVehicleId(null);
      return;

    }

    fetchVehicles();

  }, [user]);

  // Fetches all vehicles for the logged-in user and finds the active one
  async function fetchVehicles() {

    try {

      const res = await fetch("/api/auth/me/vehicles", {

        credentials: "include",

      });

      if (res.ok) {

        const data = await res.json();
        setVehicles(data);

        // Find the active vehicle and store its id
        const active = data.find((v) => v.is_active);

        if (active) setActiveVehicleId(active.id);

      }

    } catch {

      console.error("Could not fetch vehicles");

    }

  }

  // Sets the selected vehicle as active
  async function handleSetActiveVehicle(vehicleId) {

    setSettingActive(true);

    try {

      const res = await fetch(`/api/auth/me/vehicles/${vehicleId}/active`, {

        method: "PUT",
        credentials: "include",

      });

      if (res.ok) {

        setActiveVehicleId(vehicleId);

      }

    } catch {

      console.error("Could not set active vehicle");

    } finally {

      setSettingActive(false);

    }

  }

  // Clean up the debounce timer when the component unmounts
  useEffect(() => {

    return () => {

      if (distanceTimer.current) clearTimeout(distanceTimer.current);

    };

  }, []);

  // Handles distance slider changes — debounces 500ms before re-fetching
  function handleDistanceChange(newDistance) {

    setFilterDistance(newDistance);

    // Clear selected station since it may no longer be in range
    setSelectedStation(null);

    // Clear any pending re-fetch
    if (distanceTimer.current) clearTimeout(distanceTimer.current);

    // Wait 500ms after the user stops dragging before hitting the API
    distanceTimer.current = setTimeout(() => {

      // Use clicked pin location if set, otherwise fall back to user's GPS location
      const searchLocation = clickedLocation || userLocation;

      if (searchLocation) {

        fetchStationsNearby(searchLocation.lat, searchLocation.lng, setStations, newDistance);

      }

    }, 500);

  }

  // Handles map click - drops a pin and re-fetches stations around that point
  function handleMapClick(lat, lng) {

    setClickedLocation({ lat, lng });
    setSelectedStation(null);
    fetchStationsNearby(lat, lng, setStations, filterDistance);

  }

  // Clears the clicked pin and returns to searching around user location
  function clearClickedLocation() {

    setClickedLocation(null);
    setSelectedStation(null);

    if (userLocation) {

      fetchStationsNearby(userLocation.lat, userLocation.lng, setStations, filterDistance);

    }

  }

  // Gets the display name for the active vehicle
  const activeVehicle = vehicles.find((v) => v.id === activeVehicleId);

  const filteredStations = stations.filter((station) => {

    // If a legend port filter is active, use ONLY that
    if (portFilter.length > 0) {

      if (portFilter.includes("Multiple")) return hasMultipleTypes(station);

      return station.connections?.some((c) => portFilter.includes(c.port_type));

    }

    // No legend filter - apply active vehicle compatibility filter
    // Uses PORT_COMPATIBILITY map so multi-port vehicles show all compatible stations
    if (activeVehicle) {

      if (!stationMatchesVehicle(station, activeVehicle.port_type)) return false;

    }

    // Pricing filter always applies
    if (filterPricingOnly && !station.price) return false;

    return true;

  });

  // Count active filters for the badge - distance baseline is 5km
  const activeFilterCount = [
    portFilter.length > 0,
    filterPricingOnly,
    filterDistance !== 5,
  ].filter(Boolean).length;

  return (
    <>

      {/* Login button on top-right corner, takes user to login page */}
      {!user && (
        <button
          onClick={goToLogin}
          style={{
            position: "absolute",
            top: "10px",
            right: "20px",
            zIndex: 1000,
            padding: "10px 15px",
            backgroundColor: "#3090ff",
            color: "white",
            border: "none",
            borderRadius: "5px",
            cursor: "pointer"
          }}
        >
          Login
        </button>
      )}

      {user && (
        <button
          onClick={handleLogout}
          style={{
            position: "absolute",
            top: "10px",
            right: "20px",
            zIndex: 1000,
            padding: "10px 15px",
            backgroundColor: "#ff4d4d",
            color: "white",
            border: "none",
            borderRadius: "5px",
            cursor: "pointer"
          }}
        >
          Logout
        </button>
      )}

      {user && (
        <button
          onClick={goToVehicles}
          style={{
            position: "absolute",
            top: "10px",
            right: "110px",
            zIndex: 1000,
            padding: "10px 15px",
            backgroundColor: "#1a6fd4",
            color: "white",
            border: "none",
            borderRadius: "5px",
            cursor: "pointer"
          }}
        >
          My Vehicles
        </button>
      )}

      {/* Car icon button */}
      {user && (
        <button
          onClick={() => setVehiclePanelOpen((prev) => !prev)}
          title={activeVehicle ? `Active: ${activeVehicle.year} ${activeVehicle.make} ${activeVehicle.model}` : "Select vehicle"}
          style={{
            position: "absolute",
            top: "80px",
            left: "10px",
            zIndex: 1000,
            padding: "8px 12px",
            backgroundColor: activeVehicle ? "#1a6fd4" : "white",
            color: activeVehicle ? "white" : "#555",
            border: "1px solid #ddd",
            borderRadius: "8px",
            cursor: "pointer",
            fontSize: "18px",
            display: "flex",
            alignItems: "center",
            gap: "6px",
            boxShadow: "0 2px 6px rgba(0,0,0,0.15)"
          }}
        >
          🚗
          {activeVehicle && (
            <span style={{ fontSize: "12px", fontWeight: "500", maxWidth: "120px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {activeVehicle.make} {activeVehicle.model}
            </span>
          )}
        </button>
      )}

      {/* Filter bar */}
      <div
        style={{
          position: "absolute",
          top: "10px",
          left: "50%",
          transform: "translateX(-50%)",
          zIndex: 1000,
          backgroundColor: "white",
          borderRadius: "10px",
          boxShadow: "0 2px 8px rgba(0,0,0,0.18)",
          padding: "8px 16px",
          display: "flex",
          alignItems: "center",
          gap: "16px",
          fontFamily: "'Inter', sans-serif",
          fontSize: "13px",
          whiteSpace: "nowrap",
        }}
      >

        {/* Distance slider */}
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>

          <label style={{ fontWeight: "500", color: "#555" }}>
            Distance
          </label>

          <input
            type="range"
            min="5"
            max="50"
            step="5"
            value={filterDistance}
            onChange={(e) => handleDistanceChange(parseInt(e.target.value, 10))}
            style={{ width: "90px", cursor: "pointer", accentColor: "#1a6fd4" }}
          />

          {/* Live distance label */}
          <span style={{ color: "#1a6fd4", fontWeight: "600", minWidth: "38px" }}>
            {filterDistance} km
          </span>

        </div>

        {/* Divider */}
        <div style={{ width: "1px", height: "24px", backgroundColor: "#eee" }} />

        {/* Pricing toggle */}
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>

          <input
            type="checkbox"
            id="pricingFilter"
            checked={filterPricingOnly}
            onChange={(e) => setFilterPricingOnly(e.target.checked)}
            style={{ cursor: "pointer", accentColor: "#1a6fd4" }}
          />

          <label
            htmlFor="pricingFilter"
            style={{ fontWeight: "500", color: "#555", cursor: "pointer" }}
          >
            Has pricing info
          </label>

        </div>

        {/* Clear pin button - shown when user has clicked the map */}
        {clickedLocation && (

          <button
            onClick={clearClickedLocation}
            style={{
              background: "#e74c3c",
              border: "none",
              borderRadius: "6px",
              color: "white",
              fontSize: "12px",
              fontWeight: "600",
              padding: "4px 10px",
              cursor: "pointer",
              whiteSpace: "nowrap",
            }}
          >
            📍 Clear pin
          </button>

        )}

        {/* Fixed-width slot so badge + reset don't shift the other controls */}
        <div style={{ width: "100px", display: "flex", alignItems: "center", gap: "6px" }}>

          {activeFilterCount > 0 && (

            <div style={{
              backgroundColor: "#1a6fd4",
              color: "white",
              borderRadius: "10px",
              padding: "2px 7px",
              fontSize: "11px",
              fontWeight: "600",
            }}>
              {activeFilterCount} active
            </div>

          )}

          {activeFilterCount > 0 && (

            <button
              onClick={() => {

                setFilterPricingOnly(false);
                setFilterDistance(5);
                setPortFilter([]);

                if (userLocation) {

                  fetchStationsNearby(userLocation.lat, userLocation.lng, setStations, 5);

                }

              }}
              style={{
                background: "none",
                border: "none",
                color: "#c0392b",
                fontSize: "12px",
                cursor: "pointer",
                fontWeight: "500",
                padding: 0,
              }}
            >
              Reset
            </button>

          )}

        </div>

      )}

      {/* Vehicle selector panel */}
      {vehiclePanelOpen && user && (

        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "300px",
            height: "100vh",
            backgroundColor: "#ffffff",
            boxShadow: "4px 0 12px rgba(0,0,0,0.15)",
            padding: "25px",
            zIndex: 2000,
            overflowY: "auto",
            fontFamily: "'Inter', sans-serif",
            animation: "slideInLeft 0.35s ease-out"
          }}
        >

          {/* Close button */}
          <button
            onClick={() => setVehiclePanelOpen(false)}
            style={{
              position: "absolute",
              top: "15px",
              right: "15px",
              background: "none",
              border: "none",
              fontSize: "22px",
              cursor: "pointer",
              color: "#555"
            }}
          >
            X
          </button>

          {/* Panel title */}
          <h2
            style={{
              marginTop: "10px",
              marginBottom: "6px",
              fontSize: "18px",
              fontWeight: "600",
              color: "#222"
            }}
          >
            Active Vehicle
          </h2>

          <p style={{ fontSize: "13px", color: "#888", marginBottom: "20px" }}>
            Select the vehicle you're driving to filter compatible chargers.
          </p>

          <hr style={{ margin: "0 0 20px", borderColor: "#eee" }} />

          {/* No vehicles state */}
          {vehicles.length === 0 && (

            <div>

              <p style={{ fontSize: "14px", color: "#999", textAlign: "center", marginBottom: "16px" }}>
                No vehicles saved yet.
              </p>

              <button
                onClick={() => { setVehiclePanelOpen(false); goToVehicles(); }}
                style={{
                  width: "100%",
                  padding: "10px",
                  backgroundColor: "#1a6fd4",
                  color: "white",
                  border: "none",
                  borderRadius: "8px",
                  cursor: "pointer",
                  fontSize: "14px",
                  fontWeight: "500"
                }}
              >
                Add a Vehicle
              </button>

            </div>

          )}

          {/* Vehicle dropdown */}
          {vehicles.length > 0 && (

            <div>

              <label
                style={{ fontSize: "12px", fontWeight: "500", color: "#555", display: "block", marginBottom: "6px" }}
              >
                Select vehicle
              </label>

              <select
                value={activeVehicleId || ""}
                onChange={(e) => {

                  const val = e.target.value;

                  if (!val) {

                    setActiveVehicleId(null);
                    return;

                  }

                  const id = parseInt(val, 10);
                  handleSetActiveVehicle(id);

                }}
                disabled={settingActive}
                style={{
                  width: "100%",
                  height: "40px",
                  border: "1px solid #ddd",
                  borderRadius: "8px",
                  padding: "0 10px",
                  fontSize: "14px",
                  color: "#111",
                  backgroundColor: settingActive ? "#f0f0f0" : "#fafafa",
                  cursor: settingActive ? "not-allowed" : "pointer",
                  outline: "none"
                }}
              >

                <option value="">No active vehicle</option>

                {vehicles.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.year} {v.make} {v.model} — {v.port_type}
                  </option>
                ))}

              </select>

              {/* Show the active vehicle's compatible ports below the dropdown */}
              {activeVehicle && (

                <p style={{ fontSize: "13px", color: "#1a6fd4", marginTop: "10px", fontWeight: "500" }}>
                  Filtering for {
                    PORT_COMPATIBILITY[activeVehicle.port_type]
                      ? PORT_COMPATIBILITY[activeVehicle.port_type].join(", ")
                      : activeVehicle.port_type
                  } connectors
                </p>

              )}

              {settingActive && (

                <p style={{ fontSize: "12px", color: "#aaa", marginTop: "8px" }}>
                  Updating...
                </p>

              )}

            </div>

          )}

          {/* Link to manage vehicles */}
          <button
            onClick={() => { setVehiclePanelOpen(false); goToVehicles(); }}
            style={{
              marginTop: "24px",
              width: "100%",
              padding: "10px",
              backgroundColor: "white",
              color: "#1a6fd4",
              border: "1px solid #ddd",
              borderRadius: "8px",
              cursor: "pointer",
              fontSize: "13px",
              fontWeight: "500"
            }}
          >
            Manage My Vehicles
          </button>

        </div>

        {filteredStations.map((station, idx) => (

      {/* Side panel - station details */}
      {selectedStation && (
        <div
          style={{
            position: "absolute",
            top: 0,
            right: 0,
            width: "380px",
            height: "100vh",
            backgroundColor: "#ffffff",
            boxShadow: "-4px 0 12px rgba(0,0,0,0.15)",
            padding: "25px",
            zIndex: 2000,
            overflowY: "auto",
            fontFamily: "'Inter', sans-serif",
            animation: "slideInPanel 0.35s ease-out"
          }}
        >
          {/* Close button */}
          <button
            onClick={() => setSelectedStation(null)}
            style={{
              position: "absolute",
              top: "15px",
              right: "15px",
              background: "none",
              border: "none",
              fontSize: "22px",
              cursor: "pointer",
              color: "#555"
            }}
          >
            X
          </button>

          <h2
            style={{
              marginTop: "10px",
              marginBottom: "10px",
              fontSize: "22px",
              fontWeight: "600",
              color: "#222222"
            }}
          >
            {selectedStation.location.address}
          </h2>

          <p style={{ color: "#666666", marginBottom: "20px" }}>
            {selectedStation.location.country}
          </p>

          <hr style={{ margin: "15px 0", borderColor: "#d14949" }} />

          <h3 style={{ fontSize: "18px", marginBottom: "10px", color: "#333333" }}>
            Connector Type
          </h3>

          {/* Prints out the information in the connections field */}
          {selectedStation.connections?.map((c, i) => (
            <div
              key={i}
              style={{
                padding: "10px",
                background: "#f7f9fc",
                borderRadius: "8px",
                marginBottom: "10px",
                border: "1px solid #dde0e6"
              }}
            >
              <p style={{ margin: 0, fontWeight: 600, fontSize: "16px" }}>
                {c.port_type || "Unknown connector"}
              </p>

              <p style={{ margin: "4px 0", color: "#444" }}>
                <b>Speed:</b> {c.power_kw ? `${c.power_kw} kW` : "Unknown"}
              </p>

              <p style={{ margin: "4px 0", color: "#555" }}>
                <b>Current:</b> {c.current_type || "Unknown"}
              </p>

              <p style={{ margin: "4px 0", color: "#555" }}>
                <b>Quantity:</b> {c.quantity || 1}
              </p>

              <p style={{ margin: "4px 0", color: c.status === "Available" ? "green" : "#b00" }}>
                <b>Status:</b> {c.status || "Unknown"}
              </p>
            </div>
          ))}

          <h3 style={{ fontSize: "18px", marginTop: "20px", marginBottom: "10px", color: "#333" }}>
            Pricing
          </h3>

          <p style={{ color: "#444" }}>
            {selectedStation.price || "No pricing information available"}
          </p>

          <h3 style={{ fontSize: "18px", marginTop: "20px", marginBottom: "10px", color: "#333" }}>
            Availability
          </h3>

          <p style={{ color: "#444" }}>
            {selectedStation.availability || "Unknown"}
          </p>

          <h3 style={{ fontSize: "18px", marginTop: "20px", marginBottom: "10px", color: "#333" }}>
            Operator
          </h3>

          <p style={{ color: "#444" }}>
            {selectedStation.operator || "Unknown"}
          </p>

        </div>
      )}

      {/* Key for port types */}
      {(
        <div
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            width: "200px",
            height: markerKey ? "68vh" : "1vh",
            backgroundColor: "#ffffff",
            boxShadow: "-4px 0 12px rgba(0,0,0,0.15)",
            padding: "25px",
            zIndex: 2000,
            overflowY: "auto",
            fontFamily: "'Inter', sans-serif",
            borderRadius: "15px 15px 0 0"
          }}
        >
          {/* Open and close button */}
          <button
            onClick={() => setMarkerKey(!markerKey)}
            style={{
              position: "absolute",
              top: markerKey ? "1%" : "20%",
              left: "15px",
              background: "none",
              border: "none",
              fontSize: "30px",
              cursor: "pointer",
              color: "#000"
            }}
          >
            <b>{markerKey ? "-" : "+"}</b>
          </button>

          {/* Marker key - clicking each row filters the map to that type */}
          {markerKey && (
            <div style={{ fontSize: "13px", color: "#888" }}>

              <div style={{ padding: "5px" }} />

              <div
                onClick={() => setPortFilter(["Type 1 (J1772)"])}
                style={{ padding: "3px", display: "flex", alignItems: "center", cursor: "pointer", backgroundColor: portFilter.includes("Type 1 (J1772)") ? "#e8f2ff" : "transparent", borderRadius: "6px" }}
              >
                <img src={chargerType1Icon} style={{ width: "30px", height: "30px" }} alt="type1" />
                <div><p>Type 1 chargers</p></div>
              </div>

              <div
                onClick={() => setPortFilter(["Type 2 (Socket Only)"])}
                style={{ padding: "3px", display: "flex", alignItems: "center", cursor: "pointer", backgroundColor: portFilter.includes("Type 2 (Socket Only)") ? "#e8f2ff" : "transparent", borderRadius: "6px" }}
              >
                <img src={chargerType2Icon} style={{ width: "30px", height: "30px" }} alt="type2" />
                <div><p>Type 2 chargers</p></div>
              </div>

              <div
                onClick={() => setPortFilter(["NACS / Tesla Supercharger", "Tesla (Model S/X)"])}
                style={{ padding: "3px", display: "flex", alignItems: "center", cursor: "pointer", backgroundColor: portFilter.includes("NACS / Tesla Supercharger") ? "#e8f2ff" : "transparent", borderRadius: "6px" }}
              >
                <img src={chargerTeslaIcon} style={{ width: "30px", height: "30px" }} alt="tesla" />
                <div><p>Tesla chargers</p></div>
              </div>

              <div
                onClick={() => setPortFilter(["CCS (Type 1)"])}
                style={{ padding: "3px", display: "flex", alignItems: "center", cursor: "pointer", backgroundColor: portFilter.includes("CCS (Type 1)") ? "#e8f2ff" : "transparent", borderRadius: "6px" }}
              >
                <img src={chargerCcs1Icon} style={{ width: "30px", height: "30px" }} alt="ccs1" />
                <div><p>CCS Type 1 chargers</p></div>
              </div>

              <div
                onClick={() => setPortFilter(["CCS (Type 2)"])}
                style={{ padding: "3px", display: "flex", alignItems: "center", cursor: "pointer", backgroundColor: portFilter.includes("CCS (Type 2)") ? "#e8f2ff" : "transparent", borderRadius: "6px" }}
              >
                <img src={chargerCcs2Icon} style={{ width: "30px", height: "30px" }} alt="ccs2" />
                <div><p>CCS Type 2 chargers</p></div>
              </div>

              <div
                onClick={() => setPortFilter(["CHAdeMO"])}
                style={{ padding: "3px", display: "flex", alignItems: "center", cursor: "pointer", backgroundColor: portFilter.includes("CHAdeMO") ? "#e8f2ff" : "transparent", borderRadius: "6px" }}
              >
                <img src={chargerChademoIcon} style={{ width: "30px", height: "30px" }} alt="chademo" />
                <div><p>CHAdeMO chargers</p></div>
              </div>

              <div
                onClick={() => setPortFilter(["NEMA 5-15R", "NEMA 5-20R"])}
                style={{ padding: "3px", display: "flex", alignItems: "center", cursor: "pointer", backgroundColor: portFilter.includes("NEMA 5-15R") ? "#e8f2ff" : "transparent", borderRadius: "6px" }}
              >
                <img src={chargerNema5Icon} style={{ width: "30px", height: "30px" }} alt="nema5" />
                <div><p>NEMA 5 chargers</p></div>
              </div>

              <div
                onClick={() => setPortFilter(["NEMA 14-50"])}
                style={{ padding: "3px", display: "flex", alignItems: "center", cursor: "pointer", backgroundColor: portFilter.includes("NEMA 14-50") ? "#e8f2ff" : "transparent", borderRadius: "6px" }}
              >
                <img src={chargerNema14Icon} style={{ width: "30px", height: "30px" }} alt="nema14" />
                <div><p>NEMA 14 chargers</p></div>
              </div>

              <div
                onClick={() => setPortFilter(["Multiple"])}
                style={{ padding: "3px", display: "flex", alignItems: "center", cursor: "pointer", backgroundColor: portFilter.includes("Multiple") ? "#e8f2ff" : "transparent", borderRadius: "6px" }}
              >
                <img src={chargerMultipleIcon} style={{ width: "30px", height: "30px" }} alt="multi" />
                <div><p>Multiple-type chargers</p></div>
              </div>

              {/* Clear filter */}
              <div
                onClick={() => setPortFilter([])}
                style={{ padding: "3px", display: "flex", alignItems: "center", cursor: "pointer", backgroundColor: portFilter.length === 0 ? "#e8f2ff" : "transparent", borderRadius: "6px" }}
              >
                <img src={chargerIcon} style={{ width: "30px", height: "30px" }} alt="all" />
                <div><p>All chargers</p></div>
              </div>

            </div>
          )}

        </div>

      )}

      {/* Makes the map container */}
      <MapContainer
        center={[38, -100]}
        zoom={4}
        style={{ height: "100vh", width: "100%" }}
        maxBounds={[[-90, -180], [90, 180]]}
        maxBoundsViscosity={1.0}
        minZoom={3}
      >

        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          noWrap={true}
        />

        <LoadMap userLocation={userLocation} />
        <EventHandler />
        <MapClickHandler onMapClick={handleMapClick} />

        {/* Blue dot showing the user's current location */}
        {userLocation && (

          <>

            <Circle
              center={[userLocation.lat, userLocation.lng]}
              radius={40}
              pathOptions={{ color: "#1a6fd4", fillColor: "#1a6fd4", fillOpacity: 1 }}
            />

            <Circle
              center={[userLocation.lat, userLocation.lng]}
              radius={600}
              pathOptions={{ color: "#1a6fd4", fillColor: "#1a6fd4", fillOpacity: 0.15, weight: 1 }}
            />

          </>

        )}

        {/* Red pin at the clicked location */}
        {clickedLocation && (

          <Marker
            position={[clickedLocation.lat, clickedLocation.lng]}
            icon={L.divIcon({
              className: "",
              html: `<div style="
                width: 22px;
                height: 22px;
                background: #e74c3c;
                border: 3px solid white;
                border-radius: 50% 50% 50% 0;
                transform: rotate(-45deg);
                box-shadow: 0 2px 6px rgba(0,0,0,0.3);
              "></div>`,
              iconSize: [22, 22],
              iconAnchor: [11, 22],
            })}
          />

        )}

        {filteredStations.map((station, idx) => (

          <Marker
            key={idx}
            position={[
              station.location.latitude,
              station.location.longitude
            ]}
            icon={hasMultipleTypes(station)
              ? getMarkerIcon('Multiple')
              : getMarkerIcon(station.connections?.[0]?.port_type)}
            eventHandlers={{
              click: () => setSelectedStation(station)
            }}
          >
          </Marker>

        ))}

      </MapContainer>
    </>
  );
  
}