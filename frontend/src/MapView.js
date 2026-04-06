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

export default function MapView() {

  // Sets up the arrays to store station data
  const [stations, setStations] = useState([]);

  // Gets the data from the backend route
  useEffect(() => {

    fetch("http://localhost:5000/api/charge-points")
      .then(res => res.json())
      .then(data => setStations(data.data))
      // If station data can't be retrieved
      .catch(err => console.error("Couldn't fetch station data:", err))

  }, []);

  return (

    // Makes the map container, basically just the HTML file but in javascript
    // Map wrapping and out-of-frame bounds now disabled
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
              station.AddressInfo.Latitude,
              station.AddressInfo.Longitude
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

  );

}