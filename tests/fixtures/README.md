# Fixtures

Documents the console reads, one file per command, plus `<name>.exit` where the exit code is not 0.

Recorded from a real engine by `scripts/capture_fixtures.py` on a throwaway HOME with the station set to
`N0TST` / `FN31pr` (the engine's callsign check rejects `N0CALL`), scrubbed and scanned
(`tests/fixture_scan.py`). Review every file by eye for identifiers before committing: the scan is a net.

Hand-authored, because the engine cannot produce the shape today, each validated against the engine's own
JSON Schema (`schemas/`) by `tests/test_fixtures.py`:

- `regions.json`: the engine's documented example; recording it fetches Geofabrik's index.
- `logs.json`: a fresh machine has no runs; this carries every `result` word the schema documents.
- `update-all.json`: the E2 shape (issue #239): a retired unit as a row and exit 0. The `retired` state word
  is the proposal in that issue. Replace with a recording when #239 lands.
- `update-all-without.json` + `.exit`: engine 0.19.0 refusing `update` with exit 2 when the log names retired
  units. The message text is representative, not recorded.
- `plan-station-size-consent.json`: `plan-station` with a hand-authored `maps.terrain.topo.size_consent` (engine PR #260, topo-bound,
  not yet recorded); the published schema predates it, so `tests/test_fixtures.py` exempts it (`AHEAD_OF_SCHEMA`).

`list-all.json` carries the E1 fields (`members`, `installed`, `installed_size_bytes`), recorded from the
engine's `profile-state` branch (PR #259); `list-all-without.json` is the engine without them (recorded from
`main`). `schemas/<kind>[-without].json` are extracted from the engine's `docs/reference/json-interface.md`.
