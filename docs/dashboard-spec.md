# Dashboard design (planned)

## Status

This is the target design for an optional local dashboard. Nothing described here is built in this repo yet. The local service in `service/` already provides the data API a dashboard would read (`GET /api/state`, `POST /api/import`, `POST /api/decision`, `POST /api/research-request`, `GET /api/export`). Until a dashboard exists, agents produce the same views as markdown and CSV in `my-search/`. Examples below are illustrative, not live findings, and the sections should not be read as a claim that any proposed feature or research is complete.

The default screen is an action queue, not a collection of charts. Its job is to answer:

1. What changed since the last review?
2. Which cars need my decision?
3. Which evidence should I open?
4. Why does this car have this score?
5. What is ready for the next gate?

## Opening view

```text
┌─────────────────────────────────────────────────────────────────────┐
│ Car Search                    Illustrative mock     Reload findings │
├─────────────────────────────────────────────────────────────────────┤
│ Active 14 │ Verified 4 │ Needs review 6 │ New/changed 3 │ Stale 1  │
├─────────────────────────────────────────────────────────────────────┤
│ REVIEW QUEUE                                                        │
│ [Now] 2021 Model A Hybrid: confirm accident repair    Open evidence │
│ [Now] 2020 Model B Hybrid: approve manufacturer check Open dossier  │
│ [Soon] 2022 Model A: price reduced $1,200             Compare       │
├─────────────────────────────────────────────────────────────────────┤
│ TOP CANDIDATES                                      Filters ▾        │
│ Rank │ Score/coverage │ Vehicle │ Price │ Miles │ Risk │ Links      │
│  1   │ 86 · 92% A     │ ...     │ ...   │ ...   │ ...  │ List/CFX  │
│  2   │ 82 · 88% B     │ ...     │ ...   │ ...   │ ...  │ List/CFX  │
└─────────────────────────────────────────────────────────────────────┘
```

## Four dashboard views

### Cars (default, with compact decision queue)

This is the daily decision surface. Only actual user choices appear here: dealer approval, a suggested batch of 5–8 cars for verification, approved provisional document requests, and selection of 2–3 finalists. Missing photos and page retries remain research tasks.

**Top cards**

- Active candidates
- Purchase-grade candidates
- Items requiring user review
- New or materially changed since last refresh
- Stale listings needing recheck

**Queue columns**

`Urgency | Candidate | Decision needed | Why it matters | Agent finding | Evidence | Suggested action | User decision | Next gate`

Useful filters:

- Needs my review
- New since last visit
- Missing evidence
- Ready to contact
- Ready to visit/PPI
- Monitor price
- Rejected or sold

The queue should allow **Approve**, **Reject**, **Hold**, and **Need more evidence**. Decisions are written back to the local database with a timestamp; they never contact a dealer or advance a gate automatically.

### Cars (compact candidate cards)

A compact card leads for each car: vehicle/powertrain/drivetrain/miles/owners; advertised price, estimated OTD and written OTD separately; dealer/drive time; one reason to consider and one concern; listing age and last availability check. Default to **preferred powertrain first**, grouping and ranking within Discovery, Shortlist verification and Finalist investigation. Expand detailed fields instead of displaying all columns at once.

**Optional detailed table columns**

`Rank | Status | Score | Coverage | Confidence | Vehicle | Price | Mileage`

**Remaining columns**

`Powertrain | Owners | History | Service | Listed age | Dealer/distance | Phone | Key concern | Listing | CARFAX | Dossier | Next action | Last checked`

Filters:

- Model
- Powertrain
- Score range
- Evidence confidence
- Price and mileage
- Owner count
- History/service verdict
- Dealer priority
- Distance/drive time
- Status and next gate

Clicking a row opens a side panel rather than leaving the comparison view.

#### Candidate side panel

The panel shows, in this order:

1. Two-to-four-sentence verdict
2. Hard-requirement checklist
3. Score breakdown with one-line reasons
4. Evidence confidence and missing items
5. Biggest concern and likely first-year costs
6. History/service timeline
7. Questions for the dealer
8. Negotiation leverage with source links
9. Direct evidence links

Every listing card must expose these actions/details without opening a separate dossier:

- **Call dealer**: tap-to-call number, with the dealership page that confirms it
- **Open listing**: the exact vehicle page on the dealership's domain
- **Top 3 questions**: vehicle-specific, ordered by purchase risk or negotiating value
- **Negotiation leverage**: concise evidence summary plus the underlying comparable or repair/service source
- **Listing age**: days listed, the date/source used, and whether the age is confirmed or only a lower bound

Also expose **CARFAX** and **Compare** actions. Missing phone, report or negotiation evidence is visibly marked pending research; never invent it. All active cards contain three VIN-specific questions, including clearly stated unknowns. Asking price, estimated OTD assumptions and written dealer OTD have separate timestamps; no assumed discount enters the actual price or score.

Every source opens in a new tab:

- Exact dealer listing
- Full CARFAX or saved PDF
- Manufacturer service-history record or saved download
- NHTSA recall result
- NICB check/result record
- Original specification/window sticker
- Dealer reputation/licensing evidence
- Comparable-price evidence

#### Top three questions

Questions are generated from the evidence gaps for that VIN, not copied from a generic script. They appear both in the candidate row's expandable section and in the dossier.

Priority order:

1. The largest unresolved history, accident, ownership or service question
2. The largest likely near-term expense or missing maintenance item
3. The exact availability, reconditioning, removable-add-on or written-OTD question most likely to affect the deal

Examples:

- “The CARFAX shows front damage in May 2023. Do you have the repair invoice and alignment/ADAS calibration record?”
- “The service history does not show a transmission-fluid service by 92,000 miles. Was it completed, and can you provide the repair order?”
- “Please confirm this VIN is physically available and provide the itemized cash OTD price with every dealer-installed product listed separately.”

#### Negotiation leverage

Each candidate receives a short leverage block, or an explicit “Not yet researched”; reserve complete packets for the approved 2–3 finalists:

`Leverage strength | Evidence | Estimated value | Suggested use | Source link | Checked (local time)`

Timestamps are explicit local time with zone.

Permitted leverage includes:

- Lower-priced comparable vehicles outside the purchase radius
- Same-model comparables with fewer miles, newer year or better history at a similar price
- Documented price reductions or unusually long listing age
- Documented overdue maintenance with a sourced cost range; undocumented service supports a records question, not an assertion that it was not performed
- Tires, brakes, keys, cosmetic damage or other documented near-term costs
- Accident history or non-CPO status relative to cleaner/CPO comparables
- Removable dealer add-ons disclosed in an OTD quote
- Listing age, repeated relisting or price-cut history when supported by timestamped evidence

Comparables are labeled strong only when they match the same model/generation, powertrain and drivetrain, are within roughly one model year, have reasonably similar mileage, and have no known title/history mismatch. Weaker comparisons remain visible but cannot support a dollar-specific claim.

The purchase search remains limited to the approved radius. Negotiation-comparable searches may extend regionally or nationally because their purpose is price evidence, not travel.

#### Listing age and freshness

Every active vehicle displays:

`First listed/seen | Days listed | Age confidence | Last confirmed active | Price changes | Freshness/risk interpretation`

Listing age uses the best available timestamp in this order:

1. Explicit dealer original-listing date with supported meaning; page modification metadata does not establish the original listing date
2. A dated third-party inventory observation tied to the same VIN and dealer
3. The earliest time one of our agents observed the listing

The third option is labeled **observed for at least N days**, never presented as the true listing date. A dealer transfer or relisting creates a new per-dealer listing period, while the VIN record retains total observed market exposure and earlier URLs.

Default interpretation bands:

- **Fresh (0–14 days):** little listing-age leverage; verify quickly because good inventory may move.
- **Established (15–30 days):** normal exposure; compare price movement and competing inventory.
- **Aging (31–45 days):** moderate leverage signal; ask what has prevented sale and whether reconditioning is complete.
- **Longer exposure (46–60 days):** prompt to confirm availability and compare condition, pricing and reconditioning evidence.
- **Extended exposure (61+ days):** context for asking why it remains available; interpret alongside documented price, history and condition evidence.

These bands are prompts, not conclusions. Long age alone does not prove a defect or a specific discount. The dashboard strengthens the leverage flag when age is combined with price cuts, lower-priced comparables, unresolved maintenance or repeated relisting.

Listing age never automatically deducts condition points or creates a discount estimate. Display research freshness separately: “observed for at least 47 days” can coexist with “availability checked yesterday.” A portal access failure is distinct from sparse service records. Disappeared listings are **Unavailable (status unconfirmed)**, not automatically sold.

Listing-age risk flags include:

- Listing not re-confirmed within its freshness window
- VIN moved between dealer sites
- Listing removed and later relisted
- Mileage changed materially while listed
- Price unchanged despite extended age and weaker comparable pricing
- “Call for price,” unavailable CARFAX or missing photos persisting on an aging listing

### Compare

Compare up to three selected cars side by side, showing requirements, powertrain, owners, mileage, stage, coverage, all three price types, history/service findings, documented near-term costs, distance, listing age, freshness and next gate. Provide a printable call sheet with phone, VIN/stock number, exact listing URL, three questions, negotiation evidence and room for answers. Missing facts remain visible.

### Dealers

This view proves the search is thorough.

**Summary**

- Dealers identified
- Dealers checked
- Dealers due for recheck
- Current matches and near-matches
- Coverage by distance band, with bands derived from the brief's range

**Dealer table**

`Priority | Dealer | Type | Location | Distance/time | Direct site | Inventory | CARFAX access | Pricing transparency | PPI policy | Findings | Last checked | Coverage status`

An optional map is secondary to the table. The table remains the authoritative view because it shows exact coverage and links.

Assign agents non-overlapping dealer groups; each checks every model in the brief. Share dealer phone, travel and reputation research once across its cars.

### Changes

This is the audit trail.

**Change log**

- New listing discovered
- Price changed
- Mileage changed
- Listing removed/relisted or confirmed sold, preserving the distinction
- Evidence added or expired
- Score changed, including the category responsible
- User or agent decision changed

**Evidence audit**

`Candidate | Claim | Value | Evidence status | Source | Checked (local time) | Checked by | Live/saved/expired`

Timestamps are explicit local time with zone. This view makes disagreements visible and allows a reviewer to reproduce every material conclusion.

Price reductions update comparisons without resetting approvals. New eligibility/history conflicts reopen only affected gates and retain prior decisions. Keep routine research retries separate from decisions requiring the user.

## Score presentation

Never display an unexplained normalized score. Each candidate shows:

`Known 72/84 · Maximum 88 · Coverage 84% · Confidence B`

The detailed panel shows:

| Category | Score | Max |
|---|---:|---:|
| Title, accident and history | | 18 |
| Service history | | 22 |
| Price and likely OTD | | 15 |
| Mileage and age | | 10 |
| Powertrain preference | | 10 |
| Ownership pattern | | 5 |
| Condition and near-term costs | | 10 |
| Use-case fit | | 7 |
| Dealer and proximity | | 3 |

These maxima are defaults. The weights come from `service/config.json` and the search brief.

Each category includes a one-line explanation and a link to the evidence that supports it.

Coverage is assessed rubric weight; Maximum is known earned points plus unassessed points. Rank within the same research stage. The stretch threshold sets discovery priority; it is not an exclusion ceiling. Prefer written OTD; label supported estimates and missing fees. Unaccepted negotiation scenarios cannot improve a price score.

Use color only as reinforcement:

- Green + text: verified/strong
- Amber + text: concern or missing evidence
- Red + text: rejected/hard stop
- Gray + text: unknown or stale

## Data model

Use SQLite as the canonical store because multiple agent findings, price changes and evidence records are awkward to represent safely in one flat CSV. Continue producing CSV exports for manual inspection.

Core tables:

- `dealers`: one row per dealership
- `vehicles`: one row per VIN
- `listings`: all current and historical dealer URLs/prices for a VIN
- `observations`: timestamped facts reported by agents
- `evidence`: source links, saved files, freshness and verification state
- `scores`: rubric version plus category scores
- `review_tasks`: user decisions and gate approvals
- `change_log`: material changes between refreshes
- `dealer_contacts`: phone number, source URL and last verification time
- `dealer_questions`: three prioritized VIN-specific questions with their evidence basis
- `negotiation_evidence`: comparable listings, maintenance/condition costs, leverage strength and timestamps
- `listing_observations`: dealer/VIN URL, first seen, last active, price, mileage and availability for every refresh
- Shared model/year/powertrain research and cached report fingerprints/extractions: reused across matching candidates
- Scoped research requests: explicit handoff status rather than an unsupported claim that agents are running

Only the coordinator writes canonical records. Research agents submit staged findings tagged with agent, source and timestamp. This avoids concurrent overwrites and duplicate VIN rows.

## Refresh design

```text
Research agents
      ↓ staged findings
Coordinator validates + deduplicates by VIN
      ↓
SQLite canonical database
      ↓ snapshot builder
Reviewed dashboard JSON + CSV exports
      ↓
Local dashboard refresh
```

### Import completed research

After a completed research batch, the coordinator imports staged findings:

1. Reads staged agent findings.
2. Validates required fields and URLs.
3. Deduplicates by VIN.
4. Preserves conflicting values as review tasks.
5. Recalculates affected scores only.
6. Recomputes listing age from preserved observations without overwriting earlier first-seen evidence.
7. Updates phone records, questions and negotiation evidence only when supporting facts changed; expired facts become research tasks, not silently refreshed timestamps.
8. Writes a new timestamped dashboard snapshot and CSV exports.
9. Shows a refresh summary before replacing the visible view.

Example refresh summary:

`3 new vehicles · 2 price changes · 1 unavailable, status unconfirmed · 4 evidence items added · 2 scores changed · 1 conflict needs review`

### Dashboard controls

**Reload findings** reads saved database results only. **Research updates** records a scoped request for handoff to the coordinating agent. Without a connected dispatch mechanism, display “Request saved: send to the coordinating agent,” never “Research running.” Data reload time, research completion time and source-check time are separate. Reloading old evidence does not make it freshly verified.

The local service durably preserves notes, approvals, gate history and observations; browser filters persist too. A static page alone cannot claim to run agents or persist shared decisions.

### Research depth and efficiency

Discovery checks every approved dealer lightly. Approve 5–8 cars for history/service verification, then 2–3 finalists for remaining repair orders, contradictions, full comparison packets, written OTD and PPI. An explicitly approved document-only request can obtain reports before full history review is complete.

Workers receive assignment-specific context and return structured findings. Share model/year/powertrain maintenance and campaign references, including powertrain-specific inspection evidence such as hybrid battery checks. Cache each report extraction; independent verification rereads consequential or disputed claims. Code computes VIN deduplication, ages, price changes, scoring and exports. Track actual page/report reads, retries and token use where available. Prioritize unknowns that can alter eligibility or the buying decision.

### Agent-triggered refresh

At the end of each completed search batch, the coordinator runs the same refresh process. The dashboard layout, filters, decisions and record identities remain unchanged.

### Freshness rules

- Active promising listings: stale after 24 hours
- Other active listings: stale after 48 hours
- Dealer coverage: stale after 72 hours
- History evidence: refreshed when the listing or report changes
- Availability and price: always rechecked before contact and travel

Stale means “recheck required,” never “false” or zero.

## Interaction and safety boundaries

- Dashboard decisions do not send messages, submit forms, schedule inspections or make offers.
- Dealer contact remains a separate approved gate.
- Owner-site credentials never enter the database or dashboard.
- Saved service reports and CARFAX PDFs remain local and link by local evidence ID rather than exposing credentials or signed URLs.
- Every hard rejection retains its reason and evidence.
- Sold/rejected vehicles remain searchable for duplicate detection and price comparisons.

## First implementation scope

Version 1 should include:

- Cars, Compare, Dealers and Changes tabs, with compact decision queue above Cars
- Candidate filters and detail panel
- Score breakdown and evidence confidence
- Direct evidence links
- Dealer phone number and exact listing link on every active listing
- Three VIN-specific dealer questions on every active listing
- Negotiation leverage with comparable/repair evidence links and timestamps
- Listing age with provenance, confidence, last-active timestamp, price history and risk/leverage interpretation
- Approve/Reject/Hold/Need-more-evidence decisions
- Refresh summary and freshness indicators
- CSV export for all tables
- Responsive desktop and narrow-screen layouts
- Up-to-three-car comparison and printable call sheets
- Durable notes/decisions, separate price types, stage-specific ranking and explicit research-request handoff

Defer maps, automated dealer contact, alerts and historical price charts until the database has enough real rows to make them useful.

## Acceptance checks

- Every material claim has a direct link or is labeled missing/unverified.
- A hard-gate failure cannot appear as an eligible finalist.
- Score totals exactly reconcile to category scores.
- Unknown values never display as zero or “No.”
- One VIN produces one canonical candidate.
- Refresh preserves user decisions, filters and dossier links.
- Price, availability and evidence timestamps are visible.
- Listing age reconciles to its timestamped source and distinguishes confirmed age from an observed lower bound.
- The main review queue works at normal and narrow widths.
- Empty states explain whether there are no matches, no checked dealers or unavailable evidence.
- Reload/server restart preserves decisions and notes; filters survive reload.
- Three price types never overwrite one another; assumed discounts never affect scores.
- A disappeared listing is not labeled sold without supporting evidence.
- Research updates does not claim agent dispatch unless that integration exists.
- Examples/demo records are unmistakably labeled; no live findings are implied.
