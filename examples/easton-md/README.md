# Example: an SUV search from Easton, Maryland

The search this repo grew out of: a used compact or midsize SUV, bought from a dealer within an hour of a small town, on a cash budget, in a hurry.

- [search-brief.md](search-brief.md) shows a filled-in brief.
- [config.json](config.json) shows the matching service config. The weights are the defaults; the three must-haves (AWD, dark interior, reverse camera) are added to `critical_fields` so a later listing can't silently overwrite them.

How it went, in outline: the dealer map covered 93 dealerships: 80 inside the search radius and 13 farther out, some kept only as price-comparison sources. Discovery turned up 42 candidate VINs; 6 were approved for the history check, 33 stayed in discovery and 3 were set aside. The listings, dealers and research themselves are deliberately not included: they go stale within days, and they aren't useful to anyone searching somewhere else.
