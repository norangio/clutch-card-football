# Contract Proposals

Proposed changes awaiting contract-owner review. These are not part of the
frozen v2.1 contract until accepted.

## Session retention (proposed for section 8)

Game sessions expire after **14 days without activity**, measured from
`updated_at`. The service may sweep expired sessions during startup or normal
request handling. An expired `game_id` behaves exactly like an unknown id:
endpoints return HTTP 404 with error code `game_not_found`, and the client may
start a fresh game. Accepted actions refresh `updated_at`; reads do not extend
retention.

## AI-vs-AI create option (proposed for sections 7.1 and 7.3)

`POST /api/games` may include optional `ai_vs_ai: boolean`, defaulting to
`false`. When true, both stable seats are controlled by the engine and the
initial server-side `pump()` runs the complete game to `GAME_OVER`; the create
response contains the full event batch and final snapshot at revision 0. No
action requests are required. Restart preserves the original `ai_vs_ai`
setting. The option is intended for soak tests, demos, and deterministic
replays; redaction and seed-release rules remain unchanged.
