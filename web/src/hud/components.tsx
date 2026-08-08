/**
 * HUD components. All interaction-critical information lives here in HTML, not
 * in the 3-D scene (plan 3.2): text stays sharp, touch targets stay large, and
 * nothing depends on 3-D picking.
 */

import type {
  Ball, Card, LegalAction, MaybeCard, PostMoveChoice, SeatState, Snapshot,
} from "../api/types";

const SEGMENTS: Ball[] = ["1", "2", "3", "Z3", "Z2", "Z1"];

const POST_MOVE_LABEL: Record<PostMoveChoice, string> = {
  P: "Punt",
  F: "Field Goal",
  C: "Clutch",
  S: "Short Punt",
};

const DISABLED_LABEL: Record<string, string> = {
  not_in_field_goal_range: "Need to be in the red zone",
  no_clutch_remaining: "No clutch tokens left",
  clutch_already_used_this_play: "Already used this play",
};

// -------------------------------------------------------------------- cards

export function CardFace({ card, onClick, disabled }: {
  card: MaybeCard;
  onClick?: () => void;
  disabled?: boolean;
}) {
  if (card === null) {
    return <div className="card facedown" aria-label="Face-down card" />;
  }
  const isJoker = card.value === "Joker";
  const cls = ["card", card.color === "red" ? "red" : "", isJoker ? "joker" : ""]
    .filter(Boolean).join(" ");

  if (!onClick) return <div className={cls} aria-label={card.display}>{card.display}</div>;

  return (
    <button className={cls} onClick={onClick} disabled={disabled}
            aria-label={`Play ${card.display}`}>
      {card.display}
    </button>
  );
}

// --------------------------------------------------------------- scoreboard

function Pips({ count, max, kind }: { count: number; max: number; kind: "mojo" | "clutch" }) {
  return (
    <span className="pips">
      {kind === "mojo" ? "MOJO" : "CLUTCH"}
      {Array.from({ length: max }, (_, i) => (
        <span key={i} className={`pip ${kind} ${i < count ? "on" : ""}`} />
      ))}
    </span>
  );
}

function TeamPanel({ team, side, hasBall }: {
  team: SeatState; side: "home" | "away"; hasBall: boolean;
}) {
  return (
    <div className={`team ${side}`}>
      <div className="team-name">
        <span className={`dot ${team.color}`} />
        {team.name}
      </div>
      <div className="score">{team.score}</div>
      <Pips count={team.mojo} max={2} kind="mojo" />
      <Pips count={team.clutch} max={3} kind="clutch" />
      <div className="possession">{hasBall ? "● Offense" : ""}</div>
    </div>
  );
}

export function Scoreboard({ snapshot }: { snapshot: Snapshot }) {
  return (
    <div className="scoreboard">
      <TeamPanel team={snapshot.home} side="home"
                 hasBall={snapshot.offense_seat === "home"} />
      <div className="center-col">
        <div className="quarter">QUARTER {snapshot.quarter}</div>
        <div className="playcount">
          Play {snapshot.play} of {snapshot.plays_in_quarter}
        </div>
        <div className="playcount">Ball: {snapshot.ball}</div>
      </div>
      <TeamPanel team={snapshot.away} side="away"
                 hasBall={snapshot.offense_seat === "away"} />
    </div>
  );
}

// -------------------------------------------------------------------- field

/** Flat 2-D placeholder. Phase 3 replaces this with the R3F tabletop. */
export function Field({ ball, offenseColor }: { ball: Ball; offenseColor: string }) {
  const index = Math.max(0, SEGMENTS.indexOf(ball));
  const left = `${((index + 0.5) / SEGMENTS.length) * 100}%`;
  return (
    <div className="field" role="img" aria-label={`Ball at segment ${ball}`}>
      {SEGMENTS.map((seg) => (
        <div key={seg} className={`seg ${seg.startsWith("Z") ? "endzone" : ""}`}>
          {seg}
        </div>
      ))}
      <div className="ball" style={{ left, borderColor: offenseColor }} />
    </div>
  );
}

// ------------------------------------------------------------- card battle

export function CardBattle({ snapshot }: { snapshot: Snapshot }) {
  const { play_cards: pc } = snapshot;
  const slots: Array<[string, MaybeCard]> = [
    ["Offense", pc.offense],
    ["Defense", pc.defense],
  ];
  if (pc.war) slots.push(["War", pc.war]);
  if (pc.clutch) slots.push(["Clutch", pc.clutch]);

  return (
    <div className="battle">
      {slots.map(([label, card]) => (
        <div className="battle-slot" key={label}>
          <span className="battle-label">{label}</span>
          <CardFace card={card} />
        </div>
      ))}
    </div>
  );
}

// --------------------------------------------------------------------- hand

export function Hand({ snapshot, locked, onPlay }: {
  snapshot: Snapshot;
  locked: boolean;
  onPlay: (index: number) => void;
}) {
  const own = snapshot.viewer_seat === "home" ? snapshot.home : snapshot.away;
  // Contract 2.2: absent means redacted, not empty. Never render a hand we
  // were not given.
  const hand: Card[] = own.hand ?? [];
  const canPlay = snapshot.required_action === "play_card" && !locked;

  return (
    <div>
      <div className="section-title">
        Your hand ({own.hand_count}) &middot; opponent holds{" "}
        {(snapshot.viewer_seat === "home" ? snapshot.away : snapshot.home).hand_count}
      </div>
      <div className="hand">
        {hand.map((card, i) => (
          <CardFace key={`${card.id}-${i}`} card={card} disabled={!canPlay}
                    onClick={() => onPlay(i)} />
        ))}
        {hand.length === 0 && <span className="status">No cards left this quarter.</span>}
      </div>
    </div>
  );
}

// ------------------------------------------------------------------ actions

export function ActionBar({ snapshot, locked, onAction }: {
  snapshot: Snapshot;
  locked: boolean;
  onAction: (action: LegalAction) => void;
}) {
  const actions = snapshot.legal_actions.filter((a) => a.type !== "play_card");
  if (actions.length === 0) return null;

  return (
    <div>
      <div className="section-title">
        {snapshot.required_action === "extra_point" ? "Extra point" : "Your call"}
      </div>
      <div className="actions">
        {actions.map((action) => {
          const label = action.type === "post_move"
            ? POST_MOVE_LABEL[action.choice]
            : action.choice === "K" ? "Kick PAT" : "Go for 2";
          const why = action.disabled_reason
            ? DISABLED_LABEL[action.disabled_reason] ?? action.disabled_reason
            : null;
          return (
            <button
              key={`${action.type}-${action.choice}`}
              className={`btn ${action.enabled ? "primary" : ""}`}
              disabled={!action.enabled || locked}
              onClick={() => onAction(action)}
            >
              {label}
              {why && <small>{why}</small>}
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------- log

export function GameLog({ log }: { log: string[] }) {
  return (
    <div>
      <div className="section-title">Play log</div>
      <div className="log">
        {log.slice(-12).map((line, i) => <div key={i}>{line}</div>)}
      </div>
    </div>
  );
}
