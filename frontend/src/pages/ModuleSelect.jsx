import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

// A small helper component for animated buttons
const AnimatedModuleButton = ({ children, onClick, color, gradientStart, gradientEnd, delay }) => {
  const [hover, setHover] = useState(false);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(true);
    }, delay);
    return () => clearTimeout(timer);
  }, [delay]);

  return (
    <button
      onClick={onClick}
      style={{
        width: "100%",
        padding: "16px 24px",
        marginBottom: "16px",
        background: `linear-gradient(45deg, ${gradientStart}, ${gradientEnd})`,
        borderRadius: "12px", // Softer corners
        color: "#fff",
        fontWeight: 700, // Bolder text
        cursor: "pointer",
        border: "none",
        fontSize: "1.1rem", // Slightly larger font
        letterSpacing: "0.03em",
        transition: "all 0.3s ease-out", // Smooth transitions for hover and animation
        boxShadow: hover ? `0 8px 25px ${color}66` : `0 4px 15px ${color}44`, // Dynamic shadow
        transform: hover ? "translateY(-3px) scale(1.01)" : "translateY(0) scale(1)", // Lift and slight scale on hover
        opacity: visible ? 1 : 0,
        transformOrigin: "center center",
        transform: visible ? (hover ? "translateY(-3px) scale(1.01)" : "translateY(0) scale(1)") : "translateY(20px)",
      }}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      {children}
    </button>
  );
};

export default function ModuleSelect() {
  const navigate = useNavigate();
  const [containerVisible, setContainerVisible] = useState(false);

  useEffect(() => {
    // Trigger animation for the main container
    setContainerVisible(true);
  }, []);

  // Define your color palette for a modern look
  const palette = {
    backgroundPrimary: "#f0f4f8",
    backgroundSecondary: "#e2e8f0",
    cardBackground: "#ffffff",
    textColorPrimary: "#1a202c",
    textColorSecondary: "#4a5568",
    gradientMRSA: ["#6366f1", "#8b5cf6"], // Indigo to Violet
    gradientESBL: ["#10b981", "#06b6d4"], // Emerald to Cyan
    shadowSubtle: "0 10px 30px rgba(0,0,0,0.08)",
    shadowHover: "0 15px 40px rgba(0,0,0,0.12)",
  };

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: `linear-gradient(45deg, ${palette.backgroundPrimary}, ${palette.backgroundSecondary})`,
      fontFamily: "'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol'",
      overflow: "hidden", // Ensure no scrollbars from animations
      position: "relative",
    }}>

      {/* Optional: Subtle Background Animation Effect (Purely CSS-like, but within style object) */}
      <div style={{
        position: "absolute",
        inset: 0,
        background: `radial-gradient(circle at top left, ${palette.backgroundPrimary} 10%, transparent 50%),
                     radial-gradient(circle at bottom right, ${palette.backgroundSecondary} 10%, transparent 50%)`,
        backgroundSize: "400% 400%", // Large enough to animate
        animation: "bg-pan 20s infinite alternate ease-in-out", // Custom animation name
      }}/>
      {/* Note: `animation` property works with `keyframes` defined in a global CSS or styled-components.
          Since we're restricted to inline, you'd typically define `@keyframes bg-pan` in your global CSS.
          For a truly inline, JS-only approach to this animation, you'd need more complex `useState`/`useEffect`
          logic to update `backgroundPosition` over time. For this example, I'll provide the style property
          as if you have `bg-pan` defined externally.
          
          Example CSS for bg-pan (would be in your index.css or global stylesheet):
          @keyframes bg-pan {
            0% { background-position: 0% 0%; }
            100% { background-position: 100% 100%; }
          }
      */}


      <div style={{
        background: palette.cardBackground,
        padding: "40px", // More generous padding
        borderRadius: "20px", // More rounded
        boxShadow: palette.shadowSubtle,
        width: "100%",
        maxWidth: "400px", // Increased max width
        textAlign: "center",
        zIndex: 1, // Ensure content is above background effect
        transition: "all 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94)", // Smooth ease-out for entrance
        opacity: containerVisible ? 1 : 0,
        transform: containerVisible ? "translateY(0)" : "translateY(30px)",
      }}>
        <h2 style={{
          fontWeight: 800,
          marginBottom: "24px", // More space below heading
          fontSize: "2rem", // Larger heading
          color: palette.textColorPrimary,
          background: `linear-gradient(90deg, ${palette.gradientMRSA[0]}, ${palette.gradientESBL[1]})`,
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent"
        }}>
          Select a Dashboard
        </h2>

        <p style={{
          color: palette.textColorSecondary,
          marginBottom: "32px", // More space below description
          fontSize: "1rem"
        }}>
          Choose a module to access specific surveillance data and insights.
        </p>

        <AnimatedModuleButton
          onClick={() => navigate("/mrsa")}
          color={palette.gradientMRSA[0]}
          gradientStart={palette.gradientMRSA[0]}
          gradientEnd={palette.gradientMRSA[1]}
          delay={200} // Staggered animation
        >
          MRSA Surveillance
        </AnimatedModuleButton>

        <AnimatedModuleButton
          onClick={() => navigate("/esbl")}
          color={palette.gradientESBL[0]}
          gradientStart={palette.gradientESBL[0]}
          gradientEnd={palette.gradientESBL[1]}
          delay={350} // Staggered animation
        >
          ESBL Surveillance
        </AnimatedModuleButton>
      </div>
    </div>
  );
}