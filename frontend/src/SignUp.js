import { useState } from "react";

function SignUp({ onLoginSuccess, goToLogin, goToMap }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  async function signupHandler(e) {
    e.preventDefault();
    try {
      const res = await fetch("http://localhost:5000/api/auth/sign-up", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, name: email }),
      });

      if (res.ok) {
        onLoginSuccess();
      } else {
        let msg = `Sign up failed (${res.status})`;
        try {
          const data = await res.json();
          if (typeof data.detail === "string") msg = data.detail;
          else if (data.detail) msg = JSON.stringify(data.detail);
        } catch {
          /* ignore */
        }
        alert(msg);
      }
    } catch (err) {
      alert(
        "Could not reach the API. Is the backend running on http://localhost:5000 ? " +
          (err?.message || "")
      );
    }
  }

  const body = {
    backgroundColor: "#0080ff",
    fontFamily: "'Open Sans', sans-serif",
    display: "flex",
    justifyContent: "center",
    width: "100vw",
    height: "100vh",
    padding: "1rem",
  };

  const formBody = {
    width: "50vw",
    height: "40vh",
    padding: "1rem",
    backgroundColor: "white",
  };

  return (
    <>
      <title>Sign Up</title>
      <div className="container" style={body}>
        <form className="loginForm" style={formBody} onSubmit={signupHandler}>
          <h1 style={{ textAlign: "center" }}>Create an account</h1>
          <br />

          <div className="input-group">
            <label htmlFor="email" className="label">
              Email:{" "}
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div className="input-group">
            <label htmlFor="password" className="label">
              Password:{" "}
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <br />
          <button type="submit">Sign Up</button>
          <button type="button" onClick={goToLogin}>
            Already have an account? Login
          </button>
          <button type="button" onClick={goToMap}>
            Back to Map
          </button>
        </form>
      </div>
    </>
  );
}

export default SignUp;
