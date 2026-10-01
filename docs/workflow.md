# Used-car search workflow

This is the method. It assumes you have filled in [search-brief.md](../search-brief.md) and are working with an AI agent (or several) that can browse dealer sites and history reports. The agent does the legwork; you make every decision that costs money, commits you to a car, or puts you in touch with a seller.

The rules are deliberately cautious. They exist to stop the three things that go wrong most often when an agent researches cars: it fills gaps with plausible guesses, it reports more progress than it has made, and it treats a missing fact as a passing one.

## The search brief is the contract

Everything below reads from the brief: where you are, how far you'll drive, your budget target and stretch threshold, the models you want, your must-haves and preferences, and how the car will be used.

Changes to the brief are logged in its change log. When the brief changes, the agent re-scores the cars it affects rather than letting older scores drift out of line with the new rules.

## Operating model

One **coordinator** owns the records and the scoring. Research agents (workers) may submit evidence, but they cannot promote a car to the next stage, overwrite another agent's conclusion, contact a seller, or make an offer.

If your setup supports parallel agents, run at most three workers at a time:

1. **Dealer Mapper** builds the list of dealerships from each manufacturer's official dealer locator and the dealers' own sites. It records franchise status, distance, the used-inventory page, whether history reports are offered, pricing transparency, and the date checked.
2. **Inventory Scout A** searches an assigned, non-overlapping group of dealers for every model in the brief.
3. **Inventory Scout B** searches the remaining dealers the same way.

Once the dealer map is done, the Dealer Mapper becomes the **History Verifier** and independently checks the VINs you approve while the scouts keep inventory current.

Scouts are split by dealership, never by model or search engine, so two agents never report the same car from the same page. The VIN is the identity of a car; the stock number is secondary. With a single agent, the same roles simply run one after another.

### Working efficiently

Each worker gets only the brief, its assigned dealers or VINs, the evidence that already exists for them, and the fields it must return. Workers send back structured findings with source links and short notes on anything unusual. They don't repeat whole dossiers or conversation history.

- Record a dealer's phone, location, reputation and travel time once, not once per car.
- Share research that applies to a model, year or powertrain across every matching car: the manufacturer's maintenance schedule, known problems and campaigns, and what to check at inspection (for hybrids, include battery-condition evidence).
- Read each history report once and save where it came from, when it was checked and what it said. Re-read only reports that changed, passages in dispute, or claims that decide the outcome.
- Let code do the arithmetic: duplicate detection, listing ages, price changes, score totals and exports. Agents interpret evidence.
- Refresh only facts that changed or expired. Regenerate dealer questions only when the evidence behind them changes.
- Count pages fetched, reports read, repeat reads and blocked sources. Don't estimate savings that weren't measured.
- Chase the unknowns that could change eligibility or the buying decision before polishing details that can't.

## Gates and stopping points

The search moves through gates. At each one the agent stops, shows you its output, and waits for your approval before moving on.

```
Brief ─▶ 1 Dealer map ─▶ 2 Inventory ─▶ 3 History check ─▶ 4 Contact-ready ─▶ 5 Visit + inspection ─▶ 6 Offer
            you approve     you approve     you approve        you send           you go               you decide
```

### Gate 0: Search brief

The brief is filled in and you have agreed it is the contract. Nothing has been searched yet, and nothing in the repo implies any live findings.

### Phase 1: Dealer map

The Dealer Mapper:

- Starts with the official dealer locator for each make in the brief.
- Prioritizes dealers nearest home, then other franchise dealers of those makes, then credible franchise dealers of other brands that carry used inventory.
- Includes independent dealers only when their own site shows VINs, clear pricing, history-report access and permission for an independent inspection, and only if the brief allows them.
- Records realistic drive time and road distance separately.
- Keeps dealers with no matching cars on the list, to prove they were checked.

**Gate 1 output:** a dealer list (see [templates/dealerships.csv](../templates/dealerships.csv)), grouped as:

- **A:** franchise dealers near home
- **B:** other credible franchise dealers within range
- **C:** transparent independent dealers, or dealers at the edge of the drive range
- **Excluded:** with a specific reason

Inventory scouting starts only after you approve this list.

### Phase 2: Inventory discovery

The coordinator splits approved dealers into non-overlapping assignments. Each scout searches the dealer's own used-inventory pages and submits one row per VIN.

Required evidence for each car:

- The exact listing link on the dealer's site
- VIN and stock number
- Year, make, model, trim, powertrain and drivetrain
- Advertised price and mileage
- Evidence for each must-have in the brief (photos, window sticker, equipment list)
- History report link, or a note that none is offered
- Dealer phone number and the page it came from
- When the listing was first seen, by whom, how confident that date is, when it was last confirmed active, and any price changes or relisting
- Dealer, distance, drive time, and when it was checked

A car with an unknown VIN or any unconfirmed must-have goes to **Hold (needs verification)**. It is not assumed to pass and is not rejected early.

**Gate 2 output:** compact candidate cards with direct links, a preliminary score, evidence coverage, missing facts and must-have results. You approve a batch of roughly 5 to 8 cars for deeper checking. You can separately approve asking a dealer for a history report that isn't public, so a missing report doesn't block its own review. Manufacturer owner-portal checks happen only in a session you sign into yourself.

### Phase 3: Deduplication

The coordinator merges records on the 17-character VIN.

- One VIN, one record.
- Every listing URL and price change seen for that VIN is kept.
- Conflicting mileage, trim, drivetrain, price or history is flagged for review. Values are never averaged.
- A listing that disappears becomes **Unavailable (status unconfirmed)**, not "sold." It is marked sold only with evidence. All observations stay on file for duplicate detection and price comparison.
- Listings without a VIN sit in a separate queue and cannot receive a history score.

### Phase 4: Independent history check

Only cars you approved get the deep review. The History Verifier checks:

1. The VIN matches across the listing, history report, dealer documents and the vehicle's specification.
2. History report timeline: title, ownership pattern, accidents, structural damage, mileage progression, use type (rental, fleet, personal) and how regularly it was serviced.
3. The manufacturer's owner portal for recorded service, campaigns and recalls, where one exists. You sign in; agents never handle passwords.
4. NHTSA recall status.
5. NICB theft, salvage and flood check.
6. The manufacturer's maintenance schedule against the recorded service.
7. Major maintenance that isn't documented, and likely first-year costs. "Not documented" does not prove "not done," and a portal that won't load is different from a sparse record.

Every claim is labeled **Verified**, **Dealer claimed**, **Inferred**, **Conflicting** or **Missing**.

Every candidate card carries three questions for the dealer, specific to that VIN and based on known facts or clearly stated unknowns, plus negotiation evidence or an explicit "not yet researched." Full negotiation packets are saved for the 2 or 3 finalists. Price comparisons may look beyond your drive range, but each must explain why it's comparable, its history limitations, fees, and when it was checked. Listing age is kept per dealer and VIN and labeled as confirmed, seen by a third party, or our own lower-bound observation.

**Gate 3 output:** a dossier per car (see [templates/candidate-dossier.md](../templates/candidate-dossier.md)) with a **Green**, **Yellow**, **Red** or **Pending** verdict. You pick 2 or 3 finalists for repair orders, remaining contradictions, a written out-the-door price and detailed price comparison. Claims that decide the outcome, and any conflicts, get an independent source check rather than a repeat of the discovery pass.

### Phase 5: Dealer-document request

For approved cars only, the agent drafts a short request for:

- The full history report, not a badge or summary
- Service invoices and the reconditioning work order
- The certified pre-owned certificate, if CPO is claimed
- A written, itemized out-the-door price
- Confirmation of each must-have and permission for an independent inspection

Each contact-ready car comes with the dealer's phone number, the exact listing, the top three questions, and negotiation evidence such as comparable prices, documented condition costs, removable add-ons or well-sourced listing age. Missing service records support a question about records, not an assumed repair bill. Listing age can prompt questions about availability and reconditioning, but it never creates an automatic condition penalty or discount.

Messages are drafted for you to review and send. They are never sent automatically.

**Gate 4 output:** a contact-ready list with the exact missing evidence and draft questions.

### Phase 6: Visit and inspection

Right before you travel:

- Recheck availability, price and mileage.
- Confirm the car is physically on the lot.
- Confirm the VIN and that an independent pre-purchase inspection (PPI) is allowed.
- In person, check the VIN on the dash and door jamb, every must-have, and the warning lights.
- Use an independent mechanic for the PPI, not one the seller picks.

**Gate 5 output:** a comparison of visits and inspections with immediate repairs, unresolved risks and revised scores.

### Phase 7: Offer

Compare the finalists on written out-the-door price, inspection findings, known maintenance needs, history quality and expected ownership cost. No offer goes out without your explicit approval.

**Gate 6 output:** a side-by-side recommendation, the risks that would make you walk away, and a proposed out-the-door offer.

## Mandatory gates

A car cannot become a verified finalist until every one of these is confirmed:

- It is a model and year range from the brief
- Every must-have in the brief
- Within the approved travel range
- VIN consistent across documents
- No branded, salvage, rebuilt or flood title
- No odometer inconsistency, theft concern or reported structural damage
- Full history reviewed
- The seller permits an independent inspection

Missing information puts a car on hold. A confirmed failure, or a seller refusing an inspection, rejects it.

## Scoring rubric

The score measures how good the car is. **Evidence confidence is tracked separately**, so a thin listing can't outrank a well-documented car.

The defaults below fit most family-car searches. Change them in the brief's "Scoring choices" section, and keep `service/config.json` in step if you change the weights.

| Category | Default max | How points are earned |
|---|---:|---|
| Title, accident and history | 18 | Clean and consistent earns full credit. Documented minor damage can stay viable. Structural, title or odometer failures reject the car. |
| Service history | 22 | Continuous documented required service earns full credit. Explain documented gaps. Evidence you can't get stays unknown; it is not proof of neglect. |
| Price and out-the-door cost | 15 | Use the written itemized out-the-door price when you have one; otherwise label the estimate and its tax and fee assumptions. 15 at or below your target. 11 up to halfway between target and stretch. 6 up to the stretch threshold. 0 above it. A low price score doesn't remove a car from discovery, and no assumed discount ever enters the score. |
| Mileage and age | 10 | 10 at 60k or less; 9 at 60k–80k; 7 at 80k–100k; 4 at 100k–110k; 2 at 110k–125k; 0 above 125k. Newer wins within a band. |
| Powertrain preference | 10 | 10 for your preferred powertrain; 5 for anything else that meets the must-haves. With no preference, every eligible car gets 10. |
| Ownership pattern | 5 | 5 for one owner; 3 for two stable owners; 1 for three; 0 for four or more, or rapid turnover. |
| Condition and near-term costs | 10 | Tires, brakes, fluids, leaks, warning lights, body and interior, and eventually the inspection. |
| Use-case fit | 7 | How well it suits the use in the brief: child seats, cargo, climate features, towing, commute comfort, and so on. |
| Dealer and proximity | 3 | A nearby, transparent franchise dealer scores highest. Material transparency concerns score zero. |
| **Total** | **100** | |

How to read a score once it is well verified:

- 85 to 100: top candidate
- 75 to 84: strong candidate
- 65 to 74: worth considering with a clear price or condition advantage
- Below 65: low priority

### Never round up an incomplete score

A car missing half its evidence must not look like a 79/100. Show what is known, what is still possible, and how much has been checked:

`Known 54/68 · Maximum 86 · Coverage 68%`

- **Known** is the points earned out of the points that could be assessed.
- **Maximum** is the points earned plus every point not yet assessed: the best the car could still score.
- **Coverage** is the share of the rubric that has been assessed so far.

Rank cars only against others at the same stage, with your preferred powertrain first by default. Show the advertised price, the estimated out-the-door price and the written out-the-door price separately, including missing values and assumptions. A negotiation scenario never replaces a price you have actually seen or been quoted.

### Evidence confidence

- **A (purchase-grade):** VIN, direct listing, full history, NHTSA and NICB checks, manufacturer portal, supporting documents and inspection all checked.
- **B (shortlist-grade):** VIN, direct listing, full history and independent VIN checks done; portal or inspection pending.
- **C (discovery-grade):** a direct listing with incomplete history or unverified claims.
- **D (insufficient or conflicting):** no VIN, a summary-only report, conflicting facts or unsupported claims.

No car can be called a top candidate below confidence B.

## What you see

Until there is a dashboard (see [dashboard-spec.md](dashboard-spec.md)), the agent produces these as markdown and CSV files in `my-search/`.

### Candidate shortlist

Compact enough to read on a phone. Each card shows: vehicle, powertrain, drivetrain, mileage and owners; advertised and out-the-door prices; dealer and drive time; one reason to consider and one concern; listing age and when availability was last checked. Each card links to the dealer's phone number, the exact listing and the history report, followed by the three questions, the negotiation evidence and the score breakdown. Missing items are marked "pending research," never left blank or filled in.

### Dealer coverage

One row per dealer, including dealers with no matching cars. This makes the search auditable and shows where the gaps are.

### Per-car dossier

The top of the dossier gives the verdict, score, confidence, a two-to-four-sentence summary, reasons to pursue, reasons to walk, and direct evidence links. Below that: the must-have checks, history and service timeline, score explanation, open questions and missing documents.

### Review queue

One row per decision you need to make (see [templates/review-queue.csv](../templates/review-queue.csv)):

`Urgency | Candidate | Task | Why it matters | Evidence link | Agent finding | Suggested decision | Your decision | Next gate`

Routine research chores (a missing photo, a page to retry) belong to the agent's own task list, not your queue.

## Freshness and quality control

- Every price, availability and history claim carries an explicit timestamp with its time zone.
- Promising active listings are rechecked daily during an urgent search; dealer inventories every two to three days. The brief can change this.
- Material changes are logged. A price drop updates comparisons without throwing away your decisions. A new eligibility or history conflict reopens only the affected approval and keeps the earlier decision and its reason.
- Listing age and research freshness are separate: "seen for at least 47 days" can sit next to "availability checked yesterday." A page's last-modified date never establishes when the car was first listed. Age bands are prompts, not risk scores or discount estimates.
- Link to the exact vehicle page, not the dealer's homepage.
- Save a PDF or screenshot of pages that change, where the site allows it.
- Before you contact a dealer, and again before you travel, an independent pass spot-checks the top three candidates.
- When agents disagree, both readings and their evidence are shown. Unresolved safety or history questions keep a car at Yellow or Red.

## When results are thin

The agent never widens the search on its own. If there aren't enough good cars, it asks you to approve loosening the brief, one step at a time, in the order listed in the brief's "If results are thin" section.
