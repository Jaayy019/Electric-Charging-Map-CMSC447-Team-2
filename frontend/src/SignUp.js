import {useState} from "react";

function SignUp({ onLoginSuccess, goToLogin, goToMap }) {

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  async function signupHandler(e) {

    e.preventDefault();

    const res = await fetch("http://localhost:5000/api/auth/create-account", {

      method: "POST",
      credentials: "include",
      headers: {"Content-Type" : "application/json"},
      body: JSON.stringify({username, email, password})

    });

    if (res.ok) {

      onLoginSuccess();

    } 

    else{

      alert("Sign up failed");

    }

  }

  const body = {
    backgroundColor: '#0080ff', 
    fontFamily: "'Open Sans', sans-serif",
    display: 'flex',
    justifyContent: 'center',
    width: '100vw',
    height: '100vh',
    padding: '1rem'
  };

  const formBody = {
    width: '50vw',
    height: '40vh',
    padding: '1rem',
    backgroundColor: 'white'
  };

  return (
    <>
      <title>Sign Up</title>
      <div class="container" style={body}>
        <form class="loginForm" style={formBody} onSubmit={signupHandler}>

          <h1 style={{ textAlign: 'center' }}>Create an account</h1>
          <br/>

          <div class="input-group">
            <label class="label">Username: </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>

          <div class="input-group">
            <label for="email" class="label">Email: </label>
            <input
              type = "email"
              value = {email}
              onChange={(e) => setEmail(e.target.value)}
            ></input>
          </div>

          <div class="input-group">
            <label for="password" class="label">Password: </label>
            <input
              type = "password"
              value = {password}
              onChange={(e) => setPassword(e.target.value)}
            ></input>
          </div>

          <br/>
          <button type="submit">Sign Up</button>
          <button onClick={ goToLogin }>Already have an account? Login</button>
          <button type="button" onClick={goToMap}>Back to Map</button>

        </form>
      </div>
    </>
  );
}
export default SignUp;