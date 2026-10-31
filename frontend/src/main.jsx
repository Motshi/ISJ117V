import React from "react";
import ReactDOM from "react-dom/client";
import SmartCVApp from "./SmartCVApp.jsx";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <div style={{ minHeight: "100vh", display: "flex" }}>
      <SmartCVApp />
    </div>
  </React.StrictMode>
);
