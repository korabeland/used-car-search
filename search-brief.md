# Search brief

Fill this in before you start. Your agent reads it first, and everything else in this repo (the gates, the scoring, which facts get checked) is driven by what you write here. Plain English is fine. Leave a line blank if you don't care, and the agent will treat it as "no preference," not as a guess.

When you change something after the search has started, add a line to the change log at the bottom. The agent re-scores affected cars instead of quietly drifting.

For a filled-in example, see [examples/easton-md/search-brief.md](examples/easton-md/search-brief.md).

## Where

- Home base (town or ZIP):
- How far you'll drive to buy (miles or minutes of normal driving):
- What to do with dealers just past that line (ask me / include / skip):

## Budget

- Target price (the number you want to pay, all-in or before tax and fees, say which):
- Stretch threshold (asking prices up to here are searched first; above it, cars stay visible but score zero on price):
- Paying with (cash / financing / trade-in):

The stretch threshold is not a ceiling. Cars above it are kept so you can see them, but the agent never assumes a dealer will come down to your number.

## Which cars

- Makes, models and model years:
- Years, generations or engines to avoid (with the reason, if you know it):

## Must-haves

Each must-have becomes a hard gate: a car can't become a finalist until the agent has evidence it passes. If the evidence is missing, the car goes on hold rather than being rejected or assumed to pass. Keep this list to things you would truly walk away over.

These are always on, whatever you write:

- A VIN that matches across the listing, the history report and the dealer's documents
- Clean title (no salvage, rebuilt, flood or other brand)
- No odometer problem, theft record or reported structural damage
- A full history report reviewed, not just a summary badge
- The seller allows an independent pre-purchase inspection

Add your own (examples: AWD, a third row, a specific color, a backup camera, a tow package):

-
-
-

## Strong preferences

These raise a car's score but don't rule anything out.

- Preferred powertrain (e.g. hybrid, a specific engine), if any:
- Mileage you'd like to stay under:
- Owners (e.g. one owner preferred):
- Service records (e.g. dealer-documented maintenance preferred):
- Anything else:

## How the car will be used

This feeds the "use-case fit" part of the score.

- Miles per year:
- Climate and roads (snow, hills, gravel, mostly highway):
- Passengers and gear (child seats, pets, sports equipment, towing):
- Anything else that matters day to day:

## Sellers

- Franchise dealers of the brands above (yes / no):
- Other-brand franchise dealers (yes / no):
- Independent dealers (only if they publish VINs, clear pricing, history reports and allow an independent inspection; yes / no):
- Private sellers (yes / no; note that the workflow is written around dealers):

## Timing

- How soon you need the car:
- How often listings should be rechecked (default: promising cars daily, other dealers every two to three days):

## Scoring choices

The defaults are in [docs/workflow.md](docs/workflow.md#scoring-rubric). Change them here only if they don't fit. If you change category weights, also update `service/config.json`.

- Price bands (default: full points at or below target, partial points up to the stretch threshold, zero above it):
- Mileage bands (default: 60k / 80k / 100k / 110k / 125k):
- Category weights (default: history 18, service 22, price 15, mileage 10, powertrain 10, ownership 5, condition 10, use-case fit 7, dealer 3):

## If results are thin

The agent never widens the search on its own. If there aren't enough good cars, it asks you to approve loosening in this order. Reorder or edit the list to suit you.

1. Accept somewhat higher mileage when the service history is exceptional.
2. Give more weight to cars without your preferred powertrain.
3. Look harder at the over-stretch cars already found (without assuming a discount).
4. Widen the drive distance.

## Change log

| Date | What changed | Why |
|---|---|---|
| | Brief created | |
