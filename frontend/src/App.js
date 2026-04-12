import React, { useState } from 'react';
import MapView from "./MapView";
import Login from "./Login";
import SignUp from "./SignUp";

function App() {
  const [view, setView] = useState('map'); 

  if (view === 'login') {
    return (
      <Login
        onLoginSuccess={() => setView('map')}
        goToSignUp={() => setView('signup')}
      />
    );
  }

  if (view === 'signup') {
    return (
      <SignUp
        onLoginSuccess={() => setView('map')}
        goToLogin={() => setView('login')}
      />
    );
  }

  return (
    <div className="App">
      <MapView goToLogin={() => setView('login')} />
    </div>
  );
}

export default App;