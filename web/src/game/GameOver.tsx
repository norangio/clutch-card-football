/**
 * End of game.
 *
 * Without this a finished game is a dead end: `required_action` is "none" and
 * `legal_actions` is empty, so every control disables and there is no way out.
 *
 * The seed is shown here and only here. It is withheld for the whole live game
 * because it reconstructs the deck (contract 4.1), but once `result` is set the
 * game is decided and it becomes a shareable way to replay the exact same game.
 */

import type { Snapshot } from "../api/types";

export default function GameOver({ snapshot, onPlayAgain, onNewTeams, busy }: {
  snapshot: Snapshot;
  onPlayAgain: () => void;
  onNewTeams: () => void;
  busy?: boolean;
}) {
  const { result, home, away } = snapshot;
  if (!result) return null;

  const winner = result.is_tie
    ? null
    : result.winner === "home" ? home : away;
  const youWon = !result.is_tie && result.winner === snapshot.viewer_seat;

  const headline = result.is_tie
    ? "Tie game"
    : youWon ? `${winner?.name} win` : `${winner?.name} win`;

  return (
    <div className="panel gameover">
      <div className="section-title">Final</div>
      <h2 className="gameover-headline">{headline}</h2>

      <div className="gameover-score">
        <span className={result.winner === "home" ? "won" : ""}>
          <span className={`dot ${home.color}`} /> {home.name} {result.home_score}
        </span>
        <span className="dash">–</span>
        <span className={result.winner === "away" ? "won" : ""}>
          {away.name} {result.away_score} <span className={`dot ${away.color}`} />
        </span>
      </div>

      <dl className="gameover-stats">
        {[home, away].map((t) => (
          <div key={t.seat}>
            <dt>{t.name}</dt>
            <dd>
              {t.fg_made}/{t.fg_att} FG · {t.punts} punts · {t.segments} segments
            </dd>
          </div>
        ))}
      </dl>

      <div className="actions">
        <button className="btn primary" onClick={onPlayAgain} disabled={busy}>
          {busy ? "Dealing…" : "Play again"}
          <small>Same teams</small>
        </button>
        <button className="btn" onClick={onNewTeams} disabled={busy}>
          New teams
        </button>
      </div>

      {snapshot.seed !== undefined && (
        <p className="status gameover-seed">
          Seed <code>{snapshot.seed}</code> replays this exact game.
        </p>
      )}
    </div>
  );
}
