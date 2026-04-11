//Imports the necessary leaflet map components
import { MapContainer, TileLayer, Marker, Popup, useMap} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import chargerIcon from "./icons/marker.png"
import { useEffect, useState} from "react";

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

export default function MapView({ goToLogin }) {

  // Sets up the arrays to store station data
  const [stations, setStations] = useState([]);

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
    <button 
        onClick={goToLogin}
        style={{
          position: "absolute",
          top: "10px",
          right: "10px",
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
        >

            <Popup>

              <b>{station.location.address}</b><br />
              {station.location.country}

            </Popup>


          </Marker>
        

    ))}

    </MapContainer>
  </>
  );

}