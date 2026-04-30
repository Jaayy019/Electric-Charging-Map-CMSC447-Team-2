import { useState } from "react";

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
    marginBottom: "6px",
    outline: "none",

  },
 
  // Grey tip under password box
  tip: {

    fontSize: "11px",
    color: "#aaa",
    margin: "0 0 14px",

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
 
  // "Already have an account? Sign in" line at the bottom of the card
  footer: {

    fontSize: "13px",
    color: "#999",
    textAlign: "center",
    marginTop: "16px",
    marginBottom: "0",

  },
 
  // The clickable "Sign in" text - styled as a link but is a <button>
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


function SignUp({ onLoginSuccess, goToLogin, goToMap }) {

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // Holds an error string to show inline if login fails; empty string = no error shown
  const [error, setError] = useState("");

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

      } 
      
      else {

        let msg = `Sign up failed (${res.status})`;

        try {

          const data = await res.json();

          if (typeof data.detail === "string") msg = data.detail;
          else if (data.detail) msg = JSON.stringify(data.detail);

        } catch {

          /* ignore */

        }

        setError(msg);
      }
    } 
    
    catch (err) {

      setError(
        "Could not reach the API. Is the backend running on http://localhost:5000 ? " +
          (err?.message || "")
      );

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

        <p style={styles.cardTitle}>Create an account</p>
        <p style={styles.cardSub}>Start finding chargers near you</p>
 
        {/* Sign-up form - onSubmit wired to signupHandler above */}
        <form onSubmit={signupHandler}>
 
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
 
          {/* Password field - minLength enforced both here and in the backend */}
          <label style={styles.label}>Password</label>

          <input

            style={styles.input}
            type="password"
            placeholder="At least 8 characters"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}

          />
 
          {/* Hint text shown under the password field */}
          <p style={styles.tip}>Use a mix of letters, numbers and symbols</p>
 
          {/* Inline error message - only renders if error state is non-empty */}
          {error && (

            <p style={{ fontSize: "13px", color: "#c0392b", margin: "-4px 0 10px" }}>
              {error}
            </p>

          )}
 
          {/* Submit button */}
          <button type="submit" style={styles.buttonPrimary}>
            Create account
          </button>

        </form>
 
        {/* Footer link back to the login page */}
        <p style={styles.footer}>

          Already have an account?{" "}

          <button style={styles.footerLink} onClick={goToLogin}>
            Sign in
          </button>

        </p>

      </div>

    </div>

  );

}
 
export default SignUp;