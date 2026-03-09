//Imports the necessary leaflet map components
import { MapContainer, TileLayer, Marker, Popup, Circle } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import chargerIcon from "./icons/map-pin.svg"

const chargeIcon = L.icon({

  iconUrl: chargerIcon,
  iconSize: [40, 40],      
  iconAnchor: [20, 40],    
  popupAnchor: [0, -40]

});

export default function MapView() {

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

      <Marker position={[50, -0.09]} icon={chargeIcon}>
        <Popup>
          <b>Hello World!</b><br />I am a popup.
        </Popup>
      </Marker>

    </MapContainer>

  );

}