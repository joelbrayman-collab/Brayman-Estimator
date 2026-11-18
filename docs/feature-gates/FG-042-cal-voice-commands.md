# Feature Gate FG-042: Cal Voice Commands (go anywhere with a few words)

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-042` |
| Module | Cal Assistant (extends Phase 1 "Find It"; no new records, no second set of screens) |
| Date | 2026-11-18 |
| Status | **AUTHORIZED by Joel (18 Nov 2026). IN PROGRESS on branch `feature/cal-voice-commands`. NOT RELEASED.** |
| Source of truth | This file and the branch/PR in GitHub. Nothing here lives only in a chat. |

## Goal

Ben taps one big microphone button on his phone, says a short phrase, and lands on the right screen.
Examples: "Serge plans", "Get me Serge estimate", "Show me Steele costs", "Open new change order".
It must work with wet or gloved hands on a bad day: big targets, no typing, fewest taps.

## Scope (reuse first; nothing existing is rebuilt)

1. Command shape: action word + thing + job. Action words (show, get me, open, find) are interchangeable.
2. One list of "things", each mapped to a screen that already exists: plans, estimate, costs, proposal,
   contract, change orders, new change order, schedule, deliveries, purchase orders, calendar, calculators.
   New screens are added to the list; the list is `app/services/cal_find.py`.
3. Missing job: "Which job?" with big buttons. Job named, nothing else: big buttons Plans / Estimate / Schedule / ...
4. One clear match: opens straight away. A fuzzy (sound/spelling) match asks "Did you mean ...?" first.
5. Voice only opens screens and blank forms. It never saves, sends, signs, orders or moves a schedule.
   "Open new change order" opens the existing blank form (`project_controls.create_change_order_route`).
6. Costs and margins are Owner / System Administrator only (`financial_access.can_view_project_economics`);
   anyone else is told it is for the office.
7. Matching by spelling and by sound (Soundex + similarity) against existing project, client and street names.
   Plain code. No external AI, no cost per command.
8. Home: large microphone button; the Cal panel keeps typing as a backup. Speech recognition is the browser's
   own (same pattern as the Help microphone).

## Out of scope

External AI; free-form questions; migrations; model changes; changes to approved documents or CaliSIGN gates;
deploy to Practice or Production (needs Joel's explicit instruction and the release gate on the exact commit).
Plans must exist in Calibrayt to be found: uploading plans at project setup is existing behaviour; a back-fill of
older jobs' plans is a **separate, data-only task** needing Joel's authorization.

## Acceptance

- Ben's real short phrases, spoken on his phone, against Production (list below, to be completed by Ben).
- Each lands on the right screen or says clearly that nothing matched.
- Costs are blocked for non-owner / non-administrator logins.
- Existing Cal Find It tests still pass; new tests cover every rule above.

## Ben's phrase list (starting point; Ben replaces with his own words)

| You say | You should get |
|---|---|
| "Serge plans" | Current plans, newest first |
| "Get me Serge estimate" | That job's estimate |
| "Show me Steele costs" | Costs and profit (owner/office only) |
| "Open new change order" | "Which job?" then the blank change-order form |
| "Doxey" | The job, with big buttons: Plans / Estimate / Schedule ... |
| "Kingfisher plans" | Current plans |
| "Geleynse deliveries" | That job's deliveries |
| "Lockwood Proulx" | Just that house, not every Lockwood job |
| a misspelling or a mishearing ("Detremble") | "Did you mean Serge Dutremble?" |
| something that does not exist | A clear "nothing found" |
