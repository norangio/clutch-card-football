/**
 * Team and difficulty selection.
 *
 * Every control is bounded by the same ranges the server validates (contract
 * 7.1), so the UI can never offer a value the API will reject. An out-of-range
 * rating used to be accepted and left that team unable to advance the ball at
 * all, which was unwinnable and gave no clue why.
 */

import { useState } from "react";

import {
  CLUTCH_RANGE, KICK_RANGE, RATING_RANGE,
  type CardColor, type CreateGameRequest, type Difficulty,
} from "../api/types";

const DIFFICULTIES: Array<{ value: Difficulty; label: string; hint: string }> = [
  { value: "easy", label: "Easy", hint: "Plays a mostly random card" },
  { value: "medium", label: "Medium", hint: "Plays for yardage" },
  { value: "hard", label: "Hard", hint: "Runs rollouts and counts cards" },
];

function Stepper({ label, hint, value, min, max, onChange }: {
  label: string; hint: string; value: number;
  min: number; max: number; onChange: (v: number) => void;
}) {
  const id = `f-${label.replace(/\s+/g, "-").toLowerCase()}`;
  return (
    <div className="field">
      <label htmlFor={id}>
        {label} <span className="field-hint">{hint}</span>
      </label>
      <div className="stepper">
        <button type="button" className="chip" aria-label={`Decrease ${label}`}
                disabled={value <= min} onClick={() => onChange(value - 1)}>
          −
        </button>
        <output id={id}>{value}</output>
        <button type="button" className="chip" aria-label={`Increase ${label}`}
                disabled={value >= max} onClick={() => onChange(value + 1)}>
          +
        </button>
      </div>
    </div>
  );
}

export interface SetupResult extends CreateGameRequest {}

export default function SetupScreen({ onStart, busy }: {
  onStart: (setup: SetupResult) => void;
  busy?: boolean;
}) {
  const [homeName, setHomeName] = useState("Wolverines");
  const [awayName, setAwayName] = useState("Buckeyes");
  const [homeColor, setHomeColor] = useState<CardColor>("red");
  const [rating, setRating] = useState(7);
  const [kick, setKick] = useState(2);
  const [clutch, setClutch] = useState(2);
  const [aiRating, setAiRating] = useState(6);
  const [difficulty, setDifficulty] = useState<Difficulty>("medium");

  const namesOk = homeName.trim().length > 0 && awayName.trim().length > 0;

  const submit = () => {
    if (!namesOk || busy) return;
    onStart({
      home: {
        name: homeName.trim(), rating, kick_rating: kick,
        color: homeColor, clutch,
      },
      // Colour is derived server-side: the engine only has red and black.
      away: { name: awayName.trim(), rating: aiRating, kick_rating: kick, clutch },
      difficulty,
      seed: null,
    });
  };

  return (
    <div className="app">
      <div className="panel setup">
        <h1 className="setup-title">Clutch Card Football</h1>

        <div className="setup-grid">
          <div className="field">
            <label htmlFor="home-name">Your team</label>
            <input id="home-name" value={homeName} maxLength={24}
                   onChange={(e) => setHomeName(e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="away-name">Opponent</label>
            <input id="away-name" value={awayName} maxLength={24}
                   onChange={(e) => setAwayName(e.target.value)} />
          </div>
        </div>

        <div className="field">
          <label>Your colour</label>
          <div className="group">
            {(["red", "black"] as CardColor[]).map((c) => (
              <button key={c} type="button" className="chip"
                      aria-pressed={homeColor === c} onClick={() => setHomeColor(c)}>
                <span className={`dot ${c}`} /> {c}
              </button>
            ))}
          </div>
          <span className="field-hint">
            A card matching your colour scores bonus movement. The opponent takes
            the other colour.
          </span>
        </div>

        <div className="setup-grid">
          <Stepper label="Your rating" hint={`${RATING_RANGE.min}-${RATING_RANGE.max}`}
                   value={rating} min={RATING_RANGE.min} max={RATING_RANGE.max}
                   onChange={setRating} />
          <Stepper label="Opponent rating" hint={`${RATING_RANGE.min}-${RATING_RANGE.max}`}
                   value={aiRating} min={RATING_RANGE.min} max={RATING_RANGE.max}
                   onChange={setAiRating} />
          <Stepper label="Kick rating" hint={`${KICK_RANGE.min}-${KICK_RANGE.max}`}
                   value={kick} min={KICK_RANGE.min} max={KICK_RANGE.max}
                   onChange={setKick} />
          <Stepper label="Clutch tokens" hint={`${CLUTCH_RANGE.min}-${CLUTCH_RANGE.max}`}
                   value={clutch} min={CLUTCH_RANGE.min} max={CLUTCH_RANGE.max}
                   onChange={setClutch} />
        </div>

        <div className="field">
          <label>Difficulty</label>
          <div className="group">
            {DIFFICULTIES.map((d) => (
              <button key={d.value} type="button" className="chip"
                      aria-pressed={difficulty === d.value}
                      onClick={() => setDifficulty(d.value)}>
                {d.label}
              </button>
            ))}
          </div>
          <span className="field-hint">
            {DIFFICULTIES.find((d) => d.value === difficulty)?.hint}
          </span>
        </div>

        <div className="actions">
          <button className="btn primary" onClick={submit} disabled={!namesOk || busy}>
            {busy ? "Dealing…" : "Kick off"}
          </button>
        </div>
      </div>
    </div>
  );
}
