import React from "react";
import { createRoot } from "react-dom/client";

import App from "./App.jsx";
import { GCSStateProvider } from "./state/GCSStateContext.jsx";
import { ErrorBoundary } from "./components/ErrorBoundary.jsx";

createRoot(
  document.getElementById("root")
).render(
  <React.StrictMode>
    <ErrorBoundary>
      <GCSStateProvider>
        <App />
      </GCSStateProvider>
    </ErrorBoundary>
  </React.StrictMode>
);
