import React, { useState } from 'react';
import MapView from "./MapView";
import Login from "./Login";
import SignUp from "./SignUp";

function App() {
  const [view, setView] = useState('map'); 

  async function handleLogout() {
  await fetch("http://localhost:5000/api/auth/sign-out", {

    method: "POST",
    credentials: "include"

  });

    setView("login");

  }

  if (view === 'login') {
    return (
      <Login
        onLoginSuccess={() => setView('map')}
        goToSignUp={() => setView('signup')}
        goToMap={() => setView('map')} 
      />
    );
  }

  if (view === 'signup') {
    return (
      <SignUp
        onLoginSuccess={() => setView('map')}
        goToLogin={() => setView('login')}
        goToMap={() => setView('map')} 
      />
    );
  }

  return (
    <div className="App">
      <MapView goToLogin={() => setView('login')} 
        handleLogout={handleLogout}  
      />
    </div>
  );
}

export default App;