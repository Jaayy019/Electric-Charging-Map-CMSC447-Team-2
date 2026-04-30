import {useState} from "react";

// All styles are defined here as a single object so they stay out of the JSX
// and are easy to change and modify.
const styles = {

  // Full-page blue background, centers everything vertically and horizontally
  page: {

    backgroundColor: "#1a6fd4",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    width: "100vw",
    height: "100vh",
    fontFamily: "'Inter', 'Open Sans', sans-serif",

  },
 
  // Row that holds the bolt icon + "EV Charge Map" text above the card
  logo: {

    display: "flex",
    alignItems: "center",
    gap: "10px",
    marginBottom: "24px",

  },
 
  // White rounded square that the bolt SVG sits inside
  logoIcon: {

    width: "36px",
    height: "36px",
    backgroundColor: "white",
    borderRadius: "9px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",

  },
 
  // "Electric Vehicle Charge Map" text next to the icon
  logoText: {

    fontSize: "18px",
    fontWeight: "600",
    color: "white",
    letterSpacing: "-0.2px",

  },
 
  // The white card that contains the form
  card: {

    backgroundColor: "white",
    borderRadius: "14px",
    padding: "28px 28px 24px",
    width: "100%",
    maxWidth: "340px",
    boxSizing: "border-box",

  },
 
  // "Welcome back" heading inside the card
  cardTitle: {

    fontSize: "20px",
    fontWeight: "600",
    color: "#111",
    margin: "0 0 4px",

  },
 
  // "Sign in to your account" subtitle under the heading
  cardSub: {

    fontSize: "13px",
    color: "#888",
    margin: "0 0 22px",

  },
 
  // Field labels (Email, Password)
  label: {

    display: "block",
    fontSize: "12px",
    fontWeight: "500",
    color: "#555",
    marginBottom: "5px",

  },
 
  // Text inputs for email and password
  input: {

    width: "100%",
    boxSizing: "border-box",
    height: "38px",
    border: "1px solid #ddd",
    borderRadius: "8px",
    padding: "0 12px",
    fontSize: "14px",
    color: "#111",
    backgroundColor: "#fafafa",
    marginBottom: "14px",
    outline: "none",

  },
 
  // The main "Sign in" submit button
  buttonPrimary: {

    width: "100%",
    height: "40px",
    backgroundColor: "#1a6fd4",
    color: "white",
    border: "none",
    borderRadius: "8px",
    fontSize: "14px",
    fontWeight: "600",
    cursor: "pointer",
    marginTop: "4px",

  },
 
  // The row between the sign-in button and guest button
  divider: {

    display: "flex",
    alignItems: "center",
    gap: "10px",
    margin: "16px 0",

  },
 
  // The horizontal lines on either side of "or"
  dividerLine: {

    flex: 1,
    height: "1px",
    backgroundColor: "#eee",

  },
 
  // The "or" text in the middle of the divider
  dividerText: {

    fontSize: "12px",
    color: "#bbb",

  },
 
  // "Continue as guest" - outlined button, no fill
  buttonGhost: {

    width: "100%",
    height: "38px",
    backgroundColor: "white",
    color: "#1a6fd4",
    border: "1px solid #ddd",
    borderRadius: "8px",
    fontSize: "13px",
    fontWeight: "500",
    cursor: "pointer",

  },
 
  // "No account? Create one" line at the bottom of the card
  footer: {

    fontSize: "13px",
    color: "#999",
    textAlign: "center",
    marginTop: "16px",
    marginBottom: "0",

  },
 
  // The clickable "Create one" text - styled as a link but is a <button>
  footerLink: {

    color: "#1a6fd4",
    background: "none",
    border: "none",
    padding: "0",
    fontSize: "13px",
    cursor: "pointer",
    fontWeight: "500",

  },

};
 
// Small SVG of a lightning bolt used in the logo. - Format provided by AI
function BoltIcon() {

  return (

    <svg width="16" height="22" viewBox="0 0 14 20" fill="none">
      <path d="M8 0L0 11h6l-1 9 9-12H8L8 0z" fill="#1a6fd4" />
    </svg>

  );

}

function Login({ onLoginSuccess, goToSignUp, goToMap }) {

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // Holds an error string to show inline if login fails; empty string = no error shown
  const [error, setError] = useState("");

  async function loginHandler(e) {

    e.preventDefault();
    setError();

    const res = await fetch("http://localhost:5000/api/auth/sign-in", {

      method: "POST",
      credentials: "include",
      headers: {"Content-Type" : "application/json"},
      body: JSON.stringify({email, password})

    });

    if (res.ok) {

      onLoginSuccess();

    } 

    else{

      setError("Invalid login");

    }

  }

  return (

    <div style={styles.page}>
 
      {/* Logo row - bolt icon + app name above the card */}
      <div style={styles.logo}>

        <div style={styles.logoIcon}>
          <BoltIcon />
        </div>

        <span style={styles.logoText}>Electric Vehicle Charge Map</span>

      </div>

      {/* White card */}
      <div style={styles.card}>

        <p style={styles.cardTitle}>Welcome back</p>
        <p style={styles.cardSub}>Sign in to your account</p>
 
        {/* Login form */}
        <form onSubmit={loginHandler}>
 
          {/* Email field */}
          <label style={styles.label}>Email</label>

          <input

            style={styles.input}
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required

          />
 
          {/* Password field */}
          <label style={styles.label}>Password</label>

          <input

            style={styles.input}
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required

          />
 
          {/* Inline error message */}
          {error && (

            <p style={{ fontSize: "13px", color: "#c0392b", margin: "-6px 0 10px" }}>
              {error}
            </p>

          )}
 
          {/* Submit button */}
          <button type="submit" style={styles.buttonPrimary}>
            Sign in
          </button>

        </form>
 
        {/* Just a seperator */}
        <div style={styles.divider}>

          <div style={styles.dividerLine} />
          <span style={styles.dividerText}>or</span>
          <div style={styles.dividerLine} />

        </div>
 
        {/* Guest button - goes back to the map */}
        <button style={styles.buttonGhost} onClick={goToMap}>
          Continue as guest
        </button>
 
        {/* Footer link to the sign-up page */}
        <p style={styles.footer}>

          No account?{" "}

          <button style={styles.footerLink} onClick={goToSignUp}>
            Create one
          </button>

        </p>

      </div>

    </div>

  );

}

export default Login;