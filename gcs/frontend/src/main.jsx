import React from "react";
import { createRoot } from "react-dom/client";

import App from "./App.jsx";
import { GCSStateProvider } from "./state/GCSStateContext.jsx";

createRoot(
  document.getElementById("root")
).render(
  <React.StrictMode>
    <GCSStateProvider>
      <App />
    </GCSStateProvider>
  </React.StrictMode>
);
