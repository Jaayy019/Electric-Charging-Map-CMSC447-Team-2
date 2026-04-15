//Imports the necessary leaflet map components
import { MapContainer, TileLayer, Marker, useMap} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import chargerIcon from "./icons/marker.png"
import { useEffect, useState} from "react";

// Smooth slide-in animation
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
}`;

const styleTag = document.createElement("style");
styleTag.innerHTML = panelAnimation;
document.head.appendChild(styleTag);

const chargeIcon = L.icon({

  iconUrl: chargerIcon,
  iconSize: [40, 40],      
  iconAnchor: [20, 40],    
  popupAnchor: [0, -40]

});

function requestUserLocation(callback) {

  // Quick check if the browser supports it
  if (!navigator.geolocation) {

    console.error("Geolocation not allowed");
    return;

  }

  navigator.geolocation.getCurrentPosition(

    // Gets the users position
    (pos) => {

      const{latitude, longitude} = pos.coords;
      callback(latitude, longitude);

    },

    (err) => {

      console.error("User denied providing their location:", err);

    }

  );

}

// Calls the OCM API and gets stations in a 20km radius based on geolocation
function fetchStationsNearby(lat, lng, setStations) {

  fetch(`http://localhost:5000/api/charge-points?latitude=${lat}&longitude=${lng}&distance=20`)
    .then(res => res.json())
    .then(data => setStations(data.data))
    .catch(err => console.error("Could not fetch station data:", err));
}


// Handles all events for when certain map actions occur
function EventHandler() {

  const map = useMap();

  // Handles the moveend function
  useEffect(() => {

    map.on('moveend', function() {

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

function LoadMap() {

  const map = useMap();

  useEffect(() => {

    // Converts the string numbers into actual numbers
    const lat = parseFloat(localStorage.getItem("lat"));
    const lng = parseFloat(localStorage.getItem("lng"));
    const zoom = parseFloat(localStorage.getItem("zoom"));

    // Makes sure that parseFloat actually returns numbers
    if(!isNaN(lat) && !isNaN(lng) && !isNaN(zoom)) {

      map.setView([lat, lng], zoom);

    }

  }, [map]);

  return null;

}

export default function MapView({ user, goToLogin, handleLogout}) {

  // Sets up the arrays to store station data
  const [stations, setStations] = useState([]);
  const [selectedStation, setSelectedStation] = useState(null);

  // Gets the user location and then gets the stations
  useEffect(() => {

    requestUserLocation((lat, lng) => {

      fetchStationsNearby(lat, lng, setStations);
      
    });

  }, []);

  useEffect(() => {

    console.log("Stations received:", stations);

  }, [stations]);


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

    {/*Side panel*/}
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

        {/* Just prints out the information in the connections field*/}
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
            {/*Connector Type*/}
            <p style={{ margin: 0, fontWeight: 600, fontSize: "16px" }}>
              {c.port_type || "Unknown connector"}
            </p>

            {/*Charging Speed*/}
            <p style={{ margin: "4px 0", color: "#444" }}>
              <b>Speed:</b> {c.power_kw ? `${c.power_kw} kW` : "Unknown"}
            </p>

            {/*Current Type*/}
            <p style={{ margin: "4px 0", color: "#555" }}>
              <b>Current:</b> {c.current_type || "Unknown"}
            </p>

            {/*Quantity*/}
            <p style={{ margin: "4px 0", color: "#555" }}>
              <b>Quantity:</b> {c.quantity || 1}
            </p>

            {/*Working Status*/}
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
          {selectedStation.status || "Unknown"}
        </p>

        <h3 style={{ fontSize: "18px", marginTop: "20px", marginBottom: "10px", color: "#333" }}>
          Operator
        </h3>

        <p style={{ color: "#444" }}>
          {selectedStation.operator || "Unknown"}
        </p>

      </div>

    )}

    {/* Makes the map container, basically just the HTML file but in javascript */}
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

      <LoadMap />
      <EventHandler />

      {stations.map((station, idx) => (
      
        <Marker
          key = {idx}
          position={[
              station.location.latitude,
              station.location.longitude
            ]}
            icon = {chargeIcon}

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