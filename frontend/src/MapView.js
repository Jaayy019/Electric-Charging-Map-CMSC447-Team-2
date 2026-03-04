//Imports the necessary leaflet map components
import { MapContainer, TileLayer, Marker, Popup, Circle } from "react-leaflet";
import "leaflet/dist/leaflet.css";

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

      <Circle center={[40, -80]} radius={500} pathOptions={{ color: "red" }} />

      <Marker position={[50, -0.09]}>
        <Popup>
          <b>Hello World!</b><br />I am a popup.
        </Popup>
      </Marker>

    </MapContainer>

  );

}