import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import GamePage from "./game/GamePage";
import "./hud/hud.css";

const root = document.getElementById("root");
if (!root) throw new Error("#root missing from index.html");

createRoot(root).render(
  <StrictMode>
    <GamePage />
  </StrictMode>,
);
