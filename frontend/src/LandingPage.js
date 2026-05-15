import { useState, useEffect } from "react";

// Subtle pulse animation for the logo dot
const landingAnimation = `
@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.15); opacity: 0.8; }
}
@keyframes fadeInUp {
  0% { transform: translateY(24px); opacity: 0; }
  100% { transform: translateY(0); opacity: 1; }
}`;

const styleTag = document.createElement("style");
styleTag.innerHTML = landingAnimation;
document.head.appendChild(styleTag);

export default function LandingPage({ onGetStarted }) {

  // Stagger the entrance animations
  const [visible, setVisible] = useState(false);

  useEffect(() => {

    // Small delay so the animation plays on mount
    const t = setTimeout(() => setVisible(true), 50);
    return () => clearTimeout(t);

  }, []);

  return (

    <div
      style={{
        minHeight: "100vh",
        width: "100vw",
        backgroundColor: "#1a6fd4",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "'Inter', 'Open Sans', sans-serif",
        padding: "32px 16px",
        boxSizing: "border-box",
      }}
    >

      {/* Logo / icon area */}
      <div
        style={{
          width: "80px",
          height: "80px",
          backgroundColor: "white",
          borderRadius: "24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "40px",
          marginBottom: "32px",
          boxShadow: "0 8px 32px rgba(0,0,0,0.18)",
          animation: visible ? "pulse 2.5s ease-in-out infinite" : "none",
        }}
      >
        ⚡
      </div>

      {/* Title */}
      <h1
        style={{
          fontSize: "38px",
          fontWeight: "800",
          color: "white",
          margin: "0 0 12px",
          textAlign: "center",
          letterSpacing: "-0.5px",
          opacity: visible ? 1 : 0,
          animation: visible ? "fadeInUp 0.5s ease-out forwards" : "none",
        }}
      >
        PlugPath
      </h1>

      {/* Subtitle */}
      <p
        style={{
          fontSize: "17px",
          color: "rgba(255,255,255,0.82)",
          margin: "0 0 48px",
          textAlign: "center",
          maxWidth: "340px",
          lineHeight: "1.5",
          opacity: visible ? 1 : 0,
          animation: visible ? "fadeInUp 0.5s ease-out 0.1s forwards" : "none",
        }}
      >
        Find EV charging stations near you, filter by connector type, and save your vehicles.
      </p>

      {/* Get Started button */}
      <button
        onClick={onGetStarted}
        style={{
          padding: "16px 48px",
          backgroundColor: "white",
          color: "#1a6fd4",
          border: "none",
          borderRadius: "12px",
          fontSize: "17px",
          fontWeight: "700",
          cursor: "pointer",
          boxShadow: "0 4px 20px rgba(0,0,0,0.18)",
          opacity: visible ? 1 : 0,
          animation: visible ? "fadeInUp 0.5s ease-out 0.2s forwards" : "none",
          transition: "transform 0.15s, box-shadow 0.15s",
        }}
        onMouseEnter={(e) => {
          e.target.style.transform = "translateY(-2px)";
          e.target.style.boxShadow = "0 6px 24px rgba(0,0,0,0.22)";
        }}
        onMouseLeave={(e) => {
          e.target.style.transform = "translateY(0)";
          e.target.style.boxShadow = "0 4px 20px rgba(0,0,0,0.18)";
        }}
      >
        Get Started
      </button>

      {/* Small credit line */}
      <p
        style={{
          position: "absolute",
          bottom: "20px",
          fontSize: "12px",
          color: "rgba(255,255,255,0.4)",
          margin: 0,
        }}
      >
        CMSC447 Team 2
      </p>

    </div>

  );

}