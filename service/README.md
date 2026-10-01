# Local used-car research service

An optional local database and API for the search. It keeps one record per VIN, an append-only log of changes and your decisions, and computes honest partial scores. Agents import findings into it; you (or a future dashboard) read from it.

Run `python3 service/server.py` from the repo root. The API is then at http://127.0.0.1:4173. Options: `--port`, `--db`, `--static-dir`, `--config`. Defaults: port 4173, `service/search.sqlite`, `<repo>/dashboard`, `service/config.json`. Python 3.10+ standard library only. The database is created on first run and starts empty. Back up `search.sqlite` with the server stopped. The server only listens on this computer.

No dashboard ships yet (see [docs/dashboard-spec.md](../docs/dashboard-spec.md)). Until one is installed in `dashboard/` or passed with `--static-dir`, non-API paths return 404. Use `/api/state` and `/api/export?table=vehicles` for the data.

Research requests are saved as `queued_manual`, with a copyable task prompt; they do not launch agents. Give that prompt to your coordinating agent to run the approved research and import findings. Keep review decisions in the decisions table, not a regenerated CSV.

## Config

`service/config.json` sets the scoring rubric and the conflict-protected fields.

```json
{"weights": {"history": 18, "service": 22, "price": 15, "mileage": 10, "powertrain": 10, "ownership": 5, "condition": 10, "fit": 7, "dealer": 3},
 "critical_fields": ["drivetrain", "title", "title_status", "structural_damage", "flood", "odometer_conflict"]}
```

- `weights`: non-empty object of positive numbers. Keys are the rubric categories; the total possible score is their sum, so it need not be 100. `fit` is the use-case fit category. Keep these in step with the scoring choices in `search-brief.md`.
- `critical_fields`: vehicle fields whose value must never be silently overwritten (see conflict handling below). **Add one field name for each must-have in your brief**, for example `awd`, `third_row` or `interior_color`, and use the same names when importing.
- Both keys are required when the file exists. If the default `service/config.json` is missing, the built-in defaults above apply. If a file passed with `--config` is missing, or any config is invalid, the server exits with an error before starting.

## API

- `GET /api/state`: arrays `vehicles`, `dealers`, `evidence`, `observations`, `decisions`, `changes`, `research_requests`; plus `updated_at` and `rubric` (the active weights).
- `POST /api/import`: object with any of `vehicles`, `dealers`, `evidence`, `observations` arrays. JSON content type required. The entire batch is validated before anything is written. Records merge only the fields supplied. Reimporting identical evidence is a no-op. `scores` merge by rubric key. Vehicles require a valid 17-character `vin`; dealers and evidence require `id`; observations may supply `id` or receive a stable hash. VIN references, when present, must be valid. Use stable evidence IDs when updating the same finding. Other fields are flexible so linked source evidence fits.
- `POST /api/decision`: `{ "entity_id": "dealer-id-or-VIN", "decision": "approved", "note": "optional", "gate": "dealer-review" }`. Appends a durable timestamped decision that survives research refreshes.
- `POST /api/research-request`: `{ "scope": "Approved dealerships with changed inventory" }`. Returns the saved request with a human-readable `prompt`.
- `GET /api/export?table=vehicles`: CSV; also supports dealers, evidence, decisions, changes. Nested values are JSON strings. Formula-like strings are escaped for spreadsheet safety.

All mutations require a matching Origin when supplied and reject cross-site browser requests. Command-line imports may omit Origin but must use a loopback Host. No wildcard CORS. Maximum body size is 5 MiB.

## Scoring and uncertainty

Input `scores` holds earned points per rubric key, each between 0 and that key's weight. Omitted or null values are unknown. No score is inferred from listing attributes. Output `score_summary` contains `earned`, `checkable` (total weight of the categories scored so far), `coverage` (whole-number percentage of total weight that has been scored) and `maximum` (earned plus every unscored point). `score` is a compatibility alias with `max` instead of `maximum`. Show known versus possible, not a bare total, until coverage is complete.

If you change the weights after cars have been scored, any car whose stored scores no longer fit the rubric gets `score: null`, `score_summary: null` and a `score_problem` message naming the mismatch. Its stored scores are kept untouched. Re-score those cars rather than editing the numbers by hand.

## Conflicts and availability

For a conflicting value in a configured critical field, the service keeps the existing value and appends `{field, previous, incoming}` to `conflicts`, and sets `review_status` to `Needs conflict review`. The change log records which fields were affected. Earlier decisions stay in history; conflict review takes precedence until it is resolved. Inspect both sources before advancing.

A listing that disappears should be imported with `status: "unavailable (status unconfirmed)"`; the service never infers that a car sold. Listing age is worked out by the coordinating agent from dated evidence, separately from the latest availability check.

## Suggested fields

Vehicles: `vin`, `year`, `make`, `model`, `trim`, `powertrain`, `drivetrain`, `stage`, `status`, `asking_price`, `estimated_otd`, `written_otd`, `mileage`, `owners`, `interior_color`, one field per must-have in your brief, `dealer_id`, `dealer_name`, `listing_url`, `carfax_url`, `questions` (three strings), `negotiation_evidence` (objects with summary, url, strength), `scores`, `score_reasons`, `summary`, `key_concern`, `last_confirmed_active_at`, `listing_first_seen_at`, `listing_age_confidence`, `listing_date`.

Dealers: `id`, `name`, `phone`, `phone_source_url`, `official_site_url`, `used_inventory_url`, `distance_miles`, `drive_time_minutes`, `coverage_status`.

Evidence: `id`, `vin` when applicable, the claim, source URL, retrieved timestamp (with time zone) and confidence.
