//Imports the necessary leaflet map components
import { MapContainer, TileLayer, Marker, Popup, Circle } from "react-leaflet";
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

export default function MapView() {

  // Sets up the arrays to store station data
  const [stations, setStations] = useState([]);

  // Gets the data from the backend route
  useEffect(() => {

    fetch("http://localhost:5000/api/charge-points")
      .then(res => res.json())
      .then(data => setStations(data))
      // If station data can't be retrieved
      .catch(err => console.error("Couldn't fetch station data:", err))

  }, []);

  return (

    // Makes the map container, basically just the HTML file but in javascript
    <MapContainer
      center={[38, -100]}
      zoom={4}
      style={{ height: "100vh", width: "100%" }}
    >

      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

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

            <b>{station.AddressInfo.Title}</b><br />
            {station.AddressInfo.AddressLine1}

          </Popup>


        </Marker>
      
      ))}

    </MapContainer>

  );

}