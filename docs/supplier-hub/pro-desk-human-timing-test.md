# PRO Desk — human timing test (five-minute quotation)

Joel, 20 Oct 2026: the five-minute target is measured with a person operating the PRO Desk, never inferred from
automated browser run time. Synthetic store data until BMR authorizes its own.

## What is measured, and where

The **Timing** page (`/supplier/<id>/pro-desk/timing`) reads the times the person actually pressed each button:

| Stage | From | To |
|---|---|---|
| Customer and building answers | Quick Quote page opened (written into the form by the server) | "Price this building" accepted |
| Exceptions: missing prices, product matches, lines left out | building accepted | last match / choice / leave-out before issue |
| Price review and issue | end of exceptions (or building accepted) | "Issue the quotation" |
| Open the printable quotation | issue | first opening of the quotation PDF |
| **Walk-in quotation** | Quick Quote opened | printable quotation opened (sum of the stages) |

Kept apart, never counted in a quotation: **one-time store setup** — price file import, product matches made before
the walk-in, and the store's standard buildings (each with who approved it and when).

## Protocol (one session, about 30 minutes)

1. **Setup, timed separately with a stopwatch** and written down: import the store price file; approve one standard
   building; match products on a first practice quotation. Record each duration.
2. **Three walk-ins**, each by the counter person (Darcy or a store employee), from a printed customer sketch:
   - A. the reference 30 × 40 ft, 12 ft walls, one 10 × 10 overhead door, one man door, no floor;
   - B. the same size with a concrete slab and a second overhead door;
   - C. a 24 × 36 ft building with two man doors and two windows.
   An observer starts a stopwatch when the person opens Quick Quote and stops it when the printable quotation is on
   screen. Nobody coaches during the run; questions are noted.
3. After each run, compare the stopwatch with the Timing page total (they should agree within a few seconds) and
   note every exception (a missing price, a product the person had to match, a line left out) and its cause.
4. Record: person, date, store data used (synthetic or authorized BMR), stopwatch time, Timing-page stages,
   exceptions, and anything confusing.

## Pass mark

Walk-in A in **five minutes or less** with no technical-review item hidden; B and C reported as measured. A run that
needs a price or a product match is reported with its exception time, not discarded.

## Results

| Date | Person | Data | Run | Stopwatch | Timing page | Exceptions | Notes |
|---|---|---|---|---|---|---|---|
| — | — | — | — | not yet run | — | — | needs a person at the counter |
