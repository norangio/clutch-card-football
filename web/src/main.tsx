import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import GamePage from "./game/GamePage";
import SceneHarness from "./scene/SceneHarness";
import "./hud/hud.css";

// Dev-only scene harness: /?scene=1
const harness = new URLSearchParams(location.search).has("scene");

const root = document.getElementById("root");
if (!root) throw new Error("#root missing from index.html");

createRoot(root).render(
  <StrictMode>
    {harness ? <SceneHarness /> : <GamePage />}
  </StrictMode>,
);
