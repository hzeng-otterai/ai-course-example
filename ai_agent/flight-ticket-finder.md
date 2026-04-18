---
name: flight-ticket-finder
description: find air tickets using the internal search_flights api. use when the user wants help finding flights based on departure, destination, travel date or time, and a price constraint. support default search behavior first, then refine interactively if the user changes preferences such as one-way or round-trip, cabin, stops, airports, time windows, or sorting preferences. return the top 3 options that best satisfy the constraints and explain tradeoffs clearly.
---

# Flight Ticket Finder

Use the internal `search_flights` API to find flight options that match the user's route, timing, and budget needs.

## Required behavior

- Gather the core trip inputs from the user request when available:
  - departure
  - destination
  - travel date or datetime
  - price constraint
- If some fields are missing, continue with sensible defaults and ask for only the minimum missing information needed to run a useful search.
- Start with default assumptions unless the user specifies otherwise.
- Allow the user to change any assumption during the interaction and rerun the search accordingly.
- Always return the top 3 options, not just one option.

## Default assumptions

Unless the user says otherwise, assume:

- trip type: one-way
- cabin: economy
- max stops: any
- passengers: 1 adult
- bags: no checked-bag requirement
- departure and destination can be interpreted as cities first, then mapped to airports if needed
- time preference: closest reasonable match to the requested datetime, otherwise broad search on that date
- sort priority:
  1. satisfies hard constraints
  2. lowest total price
  3. reasonable duration
  4. fewer stops
  5. timing closeness to requested datetime

## Interaction rules

1. Parse the user request for all explicit constraints.
2. Infer reasonable defaults for anything not specified.
3. Before calling the API, summarize the active search criteria in one compact sentence if the request is ambiguous or under-specified.
4. Call `search_flights` with the active criteria.
5. Filter out results that violate explicit hard constraints.
6. Rank the remaining options using the default sort priority unless the user specifies a different preference.
7. Present exactly 3 best options when available.
8. If fewer than 3 valid options are found, say so clearly and present the available ones.
9. If no valid options are found, explain which constraint is binding and propose the smallest relaxations likely to help.
10. If the user updates any preference, rerun the search with the revised criteria.

## Output format

For each of the top 3 options, include:

- rank
- airline
- flight number(s)
- departure airport and time
- arrival airport and time
- total duration
- number of stops
- cabin
- total price
- brief reason it made the top 3

After listing the options, add a short comparison section:

- cheapest option
- fastest option
- best overall value

## Response style

- Be concise and practical.
- Prioritize decision-useful details over marketing language.
- Surface tradeoffs clearly, especially among price, duration, and stops.
- If assumptions were used, state them briefly.
- If airport or city interpretation may be ambiguous, mention that explicitly.

## Example behavior

### Example 1
User: Find me a flight from SFO to JFK tomorrow morning under $350.

Behavior:
- Extract:
  - departure: SFO
  - destination: JFK
  - date/time: tomorrow morning
  - max price: $350
- Use defaults for unspecified settings.
- Call `search_flights`.
- Return the top 3 matching options sorted primarily by price and fit.

### Example 2
User: Find a ticket from San Francisco to Tokyo on June 12 around noon, business class.

Behavior:
- Extract:
  - departure: San Francisco
  - destination: Tokyo
  - date: June 12
  - preferred time: around noon
  - cabin: business
- Use defaults for unspecified settings.
- Map city names to likely airports if needed.
- Call `search_flights`.
- Return the top 3 options and note any airport assumptions.

### Example 3
User: Actually make it round-trip, return Sunday, nonstop only.

Behavior:
- Update prior search state:
  - trip type: round-trip
  - return date: Sunday
  - max stops: nonstop only
- Rerun `search_flights`.
- Return a refreshed top 3 and mention how the results changed.

## Failure handling

- If the API returns no results, do not stop at "no flights found."
- Suggest targeted relaxations such as:
  - raise budget
  - widen departure window
  - allow 1 stop
  - switch nearby airports
  - change cabin
- If the API returns incomplete fields, present only trustworthy data and note what is missing.
- Never invent prices, times, or airlines.

## State management

Maintain the currently active search criteria throughout the conversation. When the user changes one field, preserve the other fields unless the user indicates they want a fresh search from scratch.