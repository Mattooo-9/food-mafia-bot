import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { TonConnectUIProvider } from "@tonconnect/ui-react";
import App from "./App";
import "./styles.css";
import { normalizeLaunchUrl } from "./routing";
import { initTelegram } from "./telegram";

normalizeLaunchUrl();
initTelegram();

const manifestUrl = `${window.location.origin}/tonconnect-manifest.json`;

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <TonConnectUIProvider manifestUrl={manifestUrl}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </TonConnectUIProvider>
  </React.StrictMode>,
);
