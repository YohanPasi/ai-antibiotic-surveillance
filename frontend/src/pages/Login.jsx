import React, { useState, useEffect, useRef } from "react";
import { loginUser } from "../api/api_auth"; // Assuming api_auth.js is in ../api/
import { useAuth } from "../auth/useAuth"; // Assuming useAuth is in ../auth/
import { useNavigate } from "react-router-dom";

// --- Reusable AnimatedButton Component ---
// (Copied directly from the Register.jsx for consistency)
const AnimatedButton = ({ children, onClick, type = "button", variant = "primary", disabled, style }) => {
  const [hover, setHover] = useState(false);
  const baseStyles = {
    padding: "12px 24px",
    borderRadius: "10px",
    border: "none",
    cursor: disabled ? "not-allowed" : "pointer",
    fontSize: "1rem",
    fontWeight: 700,
    transition: "all 0.3s ease-out",
    boxShadow: "0 4px 15px rgba(0,0,0,0.1)",
    outline: "none",
  };

  const variantStyles = {
    primary: {
      background: hover && !disabled ? "linear-gradient(45deg, #0ea5e9, #0284c7)" : "linear-gradient(45deg, #0284c7, #0ea5e9)",
      color: "#ffffff",
      transform: hover && !disabled ? "translateY(-2px)" : "translateY(0)",
      boxShadow: hover && !disabled ? "0 8px 20px rgba(14, 165, 233, 0.4)" : "0 4px 15px rgba(14, 165, 233, 0.2)",
    },
    secondary: {
      background: "#f0f4f8",
      color: "#4a5568",
      transform: hover && !disabled ? "translateY(-2px)" : "translateY(0)",
      boxShadow: hover && !disabled ? "0 8px 20px rgba(74, 85, 104, 0.15)" : "0 4px 15px rgba(74, 85, 104, 0.08)",
    },
  }[variant];

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      style={{ ...baseStyles, ...variantStyles, ...(disabled && { opacity: 0.6, cursor: "not-allowed" }), ...style }}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      {children}
    </button>
  );
};

// --- Orbital Trail Background Component ---
// (Copied directly from the Register.jsx for consistency)
const OrbitalBackground = () => {
  const [orbPositions, setOrbPositions] = useState([]);
  const animationFrameRef = useRef();
  const startTimeRef = useRef(performance.now());

  // Orb configurations (size, speed, orbit radius, color, zIndex)
  const orbConfigs = [
    { size: 60, speed: 0.00004, orbitRadius: 200, color: "#10b981", zIndex: 1, initialOffset: 0 },
    { size: 40, speed: 0.00008, orbitRadius: 150, color: "#0ea5e9", zIndex: 2, initialOffset: Math.PI / 2 },
    { size: 70, speed: 0.00003, orbitRadius: 250, color: "#6366f1", zIndex: 0, initialOffset: Math.PI },
    { size: 50, speed: 0.00006, orbitRadius: 180, color: "#ef4444", zIndex: 2, initialOffset: 3 * Math.PI / 2 },
    { size: 30, speed: 0.0001, orbitRadius: 120, color: "#f59e0b", zIndex: 3, initialOffset: Math.PI / 3 },
    { size: 80, speed: 0.00002, orbitRadius: 300, color: "#8b5cf6", zIndex: 0, initialOffset: 2 * Math.PI / 3 },
    { size: 45, speed: 0.00007, orbitRadius: 160, color: "#0d9488", zIndex: 1, initialOffset: 4 * Math.PI / 3 },
  ];

  useEffect(() => {
    const animate = (currentTime) => {
      const elapsedTime = currentTime - startTimeRef.current;
      const newPositions = orbConfigs.map(orb => {
        const angle = (orb.speed * elapsedTime + orb.initialOffset) % (2 * Math.PI);
        const x = orb.orbitRadius * Math.cos(angle);
        const y = orb.orbitRadius * Math.sin(angle);
        return { x, y, size: orb.size, color: orb.color, zIndex: orb.zIndex };
      });
      setOrbPositions(newPositions);
      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animationFrameRef.current = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(animationFrameRef.current);
    };
  }, []);

  return (
    <div style={{
      position: "absolute",
      inset: 0,
      overflow: "hidden",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "linear-gradient(135deg, #1f2937, #0f172a)",
    }}>
      {orbPositions.map((orb, index) => (
        <div
          key={index}
          style={{
            position: "absolute",
            width: orb.size,
            height: orb.size,
            borderRadius: "50%",
            background: `radial-gradient(circle at 30% 30%, ${orb.color}AA, ${orb.color}33)`,
            boxShadow: `0 0 ${orb.size / 3}px ${orb.size / 6}px ${orb.color}66`,
            filter: "blur(2px)",
            transform: `translate(${orb.x}px, ${orb.y}px) scale(0.8)`,
            transition: "transform ease-out",
            zIndex: orb.zIndex,
            opacity: 0.7,
            animation: `orbPulse ${Math.random() * 3 + 2}s infinite alternate ease-in-out`,
          }}
        />
      ))}
      <div style={{
        position: "absolute",
        width: "300px",
        height: "300px",
        borderRadius: "50%",
        background: "radial-gradient(circle at center, rgba(30, 41, 59, 0.4), transparent 70%)",
        filter: "blur(50px)",
        zIndex: -1,
      }}/>
    </div>
  );
};


// --- Main Login Component ---
export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [formVisible, setFormVisible] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    setFormVisible(true); // Animate form entrance
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");

    if (!username || !password) {
      setError("Please enter both username and password.");
      setLoading(false);
      return;
    }

    try {
      const data = await loginUser(username, password);
      login(data.user, data.access_token);
      navigate("/modules");
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid username or password. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  // Define delay for staggered input animations
  const inputAnimationDelays = {
    username: 300,
    password: 400,
  };

  return (
    <div style={{
      minHeight: "100vh",
      width: "100vw", // Explicitly set width to cover full screen
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      fontFamily: "'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol'",
      color: "#ffffff",
      overflow: "hidden",
      position: "relative",
    }}>
      <OrbitalBackground /> {/* Our superb background component */}

      <div style={{
        background: "rgba(255, 255, 255, 0.95)",
        padding: "40px",
        borderRadius: "20px",
        boxShadow: "0 15px 45px rgba(0,0,0,0.25)",
        width: "100%",
        maxWidth: "450px",
        textAlign: "center",
        zIndex: 10,
        transition: "all 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94)",
        opacity: formVisible ? 1 : 0,
        transform: formVisible ? "translateY(0)" : "translateY(50px) scale(0.95)",
      }}>
        <h1 style={{
          fontSize: "2.5rem",
          fontWeight: 800,
          marginBottom: "20px",
          color: "#1a202c",
          background: "linear-gradient(90deg, #6366f1, #0ea5e9)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent"
        }}>
          Welcome Back
        </h1>
        <p style={{
          fontSize: "1rem",
          color: "#4a5568",
          marginBottom: "30px",
          lineHeight: 1.5,
        }}>
          Please log in to your account to continue.
        </p>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
          {["username", "password"].map((fieldName, index) => (
            <input
              key={fieldName}
              name={fieldName}
              type={fieldName === "password" ? "password" : "text"}
              placeholder={fieldName.charAt(0).toUpperCase() + fieldName.slice(1)}
              value={fieldName === "username" ? username : password}
              onChange={(e) => {
                if (fieldName === "username") setUsername(e.target.value);
                else setPassword(e.target.value);
                setError(""); // Clear error on input change
              }}
              style={{
                padding: "14px 18px",
                borderRadius: "10px",
                border: "1px solid #e2e8f0",
                fontSize: "1rem",
                color: "#2d3748",
                background: "#fdfdfd",
                transition: "all 0.3s ease-out",
                outline: "none",
                boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
                opacity: formVisible ? 1 : 0,
                transform: formVisible ? "translateY(0)" : "translateY(20px)",
                transitionDelay: `${inputAnimationDelays[fieldName]}ms`,
              }}
              onFocus={(e) => {
                e.target.style.borderColor = "#0ea5e9";
                e.target.style.boxShadow = "0 0 0 3px rgba(14, 165, 233, 0.2)";
              }}
              onBlur={(e) => {
                e.target.style.borderColor = "#e2e8f0";
                e.target.style.boxShadow = "0 2px 8px rgba(0,0,0,0.04)";
              }}
            />
          ))}

          {error && (
            <p style={{
              color: "#ef4444",
              marginTop: "10px",
              marginBottom: "5px",
              fontSize: "0.95rem",
              fontWeight: 600,
              animation: "shake 0.5s",
            }}>
              {error}
            </p>
          )}

          <AnimatedButton
            type="submit"
            disabled={loading}
            style={{ marginTop: "20px" }}
          >
            {loading ? "Logging in..." : "Login"}
          </AnimatedButton>

          <p
            onClick={() => navigate("/register")}
            style={{
              color: "#0ea5e9",
              cursor: "pointer",
              marginTop: "20px",
              fontSize: "0.95rem",
              fontWeight: 600,
              transition: "color 0.2s ease-out",
            }}
            onMouseEnter={(e) => e.target.style.color = "#0284c7"}
            onMouseLeave={(e) => e.target.style.color = "#0ea5e9"}
          >
            Don't have an account? <span style={{ textDecoration: "underline" }}>Create new account</span>
          </p>
        </form>
      </div>
    </div>
  );
}