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
