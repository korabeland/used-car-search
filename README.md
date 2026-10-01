# Used-car search

A method for buying a used car with an AI agent doing the research and you making the decisions.

You write down what you want in plain English. Your agent (Claude Code, Codex, or any agent that can read files and browse the web) maps the dealers near you, finds matching cars, checks their histories, and drafts the questions to ask. It stops at each step for your approval, and it never contacts a dealer or makes an offer for you.

## Why this exists

Agents are fast at the tedious parts of a car search: checking dozens of dealer sites, reading history reports, tracking price changes. Left to their own habits, they also do three things you don't want:

- **Fill gaps with guesses.** A listing that doesn't mention AWD becomes "probably AWD."
- **Overstate progress.** A car with half its history unchecked shows up as an 82/100.
- **Act too early.** Messages get sent, filters get loosened, a "sold" label gets applied to a listing that just moved.

This repo is a contract that prevents those things. Unknowns stay unknown, scores show how much has actually been checked, and every step that costs money or commits you to anything waits for you.

## How to use it

1. Copy this repo (use the green "Use this template" or "Fork" button, or clone it).
2. Fill in [search-brief.md](search-brief.md): where you are, how far you'll drive, your budget, the cars you want, and your must-haves. There's a [filled-in example](examples/easton-md/search-brief.md).
3. Open the folder in your agent and say: *"Read AGENTS.md and start the search."*
4. Approve, adjust or reject at each gate.

Your working files (dealer list, candidates, dossiers) go in `my-search/`, which git ignores so you don't publish the cars you're looking at. Your filled-in brief contains your location and budget, so keep your copy private if that matters to you.

## The steps

```
Brief ─▶ 1 Dealer map ─▶ 2 Inventory ─▶ 3 History check ─▶ 4 Contact-ready ─▶ 5 Visit + inspection ─▶ 6 Offer
            you approve     you approve     you approve        you send           you go               you decide
```

1. **Dealer map.** Every dealer in range, including the ones with nothing for you, so you can see the search was thorough.
2. **Inventory.** One record per car (by VIN) with direct links and evidence for each must-have. Anything unconfirmed goes on hold, not through.
3. **History check.** For the 5 to 8 cars you pick: history report, recalls, theft and flood checks, service records, and a verdict of Green, Yellow or Red.
4. **Contact-ready.** For your 2 or 3 finalists: the dealer's number, the exact listing, the three questions that matter most for that car, and price evidence. Drafted, never sent.
5. **Visit and inspection.** A pre-trip checklist and an independent mechanic's inspection.
6. **Offer.** A side-by-side comparison and a proposed out-the-door price. You decide.

The full method, including the scoring rubric, is in [docs/workflow.md](docs/workflow.md).

## What's here

| Path | What it is |
|---|---|
| [search-brief.md](search-brief.md) | The one file you fill in |
| [AGENTS.md](AGENTS.md) | The rules your agent follows (Claude Code reads it through `CLAUDE.md`) |
| [docs/workflow.md](docs/workflow.md) | The method: gates, evidence rules, scoring |
| [templates/](templates/) | Column layouts for dealer, candidate and review tables, and the per-car dossier |
| [service/](service/) | Optional local database and API that keeps one record per car and logs every change and decision (Python, no installs needed) |
| [docs/dashboard-spec.md](docs/dashboard-spec.md) | Design for a dashboard that isn't built yet |
| [examples/easton-md/](examples/easton-md/) | The real search this came from, with personal details removed |

To run the service's tests: `python3 -m unittest discover tests`

## Scores you can trust

Every car is scored out of 100 across history, service records, price, mileage, powertrain, ownership, condition, how well it fits your use, and the dealer. Until everything has been checked, a score looks like this:

`Known 54/68 · Maximum 86 · Coverage 68%`

That reads: 54 points earned out of the 68 that could be checked so far; the car could still reach 86; 68% of the evidence is in. A thin listing can't outrank a well-documented car, and no assumed discount ever improves a price score.

## Not advice

This is a research method, not financial, legal or mechanical advice. Listings change by the hour, and agents misread pages. Check anything that matters yourself, and always get an independent pre-purchase inspection.

## License

[MIT](LICENSE)
