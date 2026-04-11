import React, { useState } from 'react';
import MapView from "./MapView";
import Login from "./Login";

function App() {
  const [view, setView] = useState('map'); 

  if (view === 'login') {
    return <Login onLoginSuccess={() => setView('map')} />;
  }

  return (
    <div className="App">
      <MapView goToLogin={() => setView('login')} />
    </div>
  );
}

export default App;