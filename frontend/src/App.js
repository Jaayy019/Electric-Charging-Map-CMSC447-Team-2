import React, { useState, useEffect } from 'react';
import MapView from "./MapView";
import Login from "./Login";
import SignUp from "./SignUp";

function App() {
  const [view, setView] = useState('map'); 
  const [user, setUser] = useState(null);

  async function fetchUser() {

    const res = await fetch("http://localhost:5000/api/auth/me", {

      credentials: "include"

    });

    if (res.ok) {

      const data = await res.json();
      setUser(data);

    } 
    
    else {

      setUser(null);

    }

  }

  useEffect(() => {

    fetchUser();

  }, []);

  async function handleLogout() {
  await fetch("http://localhost:5000/api/auth/sign-out", {

    method: "POST",
    credentials: "include"

  });

    setUser(null);
    setView("login");

  }

  if (view === 'login') {
    return (
      <Login
        onLoginSuccess={async () => {
          await fetchUser();
          setView('map')
        }}
        goToSignUp={() => setView('signup')}
        goToMap={() => setView('map')} 
      />
    );
  }

  if (view === 'signup') {
    return (
      <SignUp
        onLoginSuccess={async () => {
          await fetchUser();
          setView('map')
        }}
        goToLogin={() => setView('login')}
        goToMap={() => setView('map')} 
      />
    );
  }

  return (
    <div className="App">
      <MapView 
        user = {user}
        goToLogin={() => setView('login')} 
        handleLogout={handleLogout}  
      />
    </div>
  );
}

export default App;