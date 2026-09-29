# Linda Bushel — governed geometry reconciliation

Date: 2026-09-29

This record traces the open layout conflicts. It does not choose a pier count, a joist grid, or a stringer count. It does not change a drawing, a take-off quantity, a supplier request, or a price.

## What both layouts already share

The design brief and both generators use the same finished datum:

- Pool centre is the origin. Positive Y is toward the stairs. Pool radius is 10.5 ft.
- Upper deck is 18 ft wide, from X = −9 ft to X = +9 ft. Front edge is Y = 15.5 ft. Clear depth at the centreline is 5 ft.
- Approved framing is Option A: one straight main beam and short wing beams. Main beam Y = 13 ft, from X = −6 ft to X = +6 ft. Wing ends are at X = ±9 ft, Y = 8.5 ft. Each wing length is 5.41 ft.
- Stair width is 10 ft, from X = −5 ft to X = +5 ft. Finished rise is 38 in. Five risers at 7.60 in. Four treads at 11 in nosing-to-nosing. Horizontal run is 44 in.
- Lower deck is 10 ft wide by 3 ft deep, finished 12 in above grade.
- Joists are 2×8. Beams are double 2×10. Stringers are 2×12.

That shared datum is not a member layout. The counts below are still open.

## Piers — unresolved

P1 places 12 piers. The front beam has three, at X = −9, 0, and +9 ft, so the front-beam bays are 9 ft. The landing has four corner piers, so the landing beams span 10 ft. `p1_calculation.py` says those spans are not checked against a span table.

CT-1 places 15 piers. The front beam has four, at X = −9, −3, +3, and +9 ft, so those bays are 6 ft. The landing has six piers, including a centre on the back rim and a centre on the front rim. The script compares spans with numeric limits named `ALLOW_2X8_16`, `ALLOW_2X6_16`, `ALLOW_DBL_2X10_AT_8`, `ALLOW_DBL_2X10_AT_10`, and `ALLOW_DBL_2X6_AT_6`. No sentence in the design brief, the drawing standard, or this case cites those numbers to the Ontario Building Code, a municipality table, or another prescriptive source.

The design brief approves sonotube piers and Option A. It also says final spans and pier locations are still to be reconciled before issue. It does not state a pier count.

Neither 12 nor 15 is the governed construction layout.

Authority still required: the prescriptive beam and joist span table the Municipality of North Grenville accepts for these members, these spacings, and this species and grade, or a structural reviewer. Field bearing remains a separate confirmation.

## Joist lines — unresolved

The brief says 2×8 joists at 16 in on centre. The upper deck is 216 in wide. 216 / 16 = 13.5, so a uniform 16 in module cannot place a joist on both side edges and keep every bay at 16 in.

P1 draws 16 lines. Measured bays, in inches, from X = −9 ft: 4, then thirteen bays of 16, then 4. The largest bay is 16 in.

CT-1 draws 15 lines. Measured bays, in inches, from the same edge: thirteen bays of 16, then one 8 in closer. The largest bay is 16 in.

Both stay within 16 in. The brief does not say whether the closing remainder is split into two 4 in edge bays or left as one 8 in bay, or which edge receives the closer.

Neither 16 nor 15 is the governed joist layout.

## Stringers — unresolved

The brief says 2×12 stringers at not more than 16 in on centre. The stair is 120 in wide. 120 / 16 = 7.5, so the same closing problem applies.

P1 draws 10 stringers. Measured bays, in inches: 4, then seven bays of 16, then 4. The largest bay is 16 in.

CT-1 and CT-2 R2 draw 9 stringers. Measured bays, in inches: seven bays of 16, then one 8 in closer. The largest bay is 16 in.

Both meet the maximum. The brief does not require the smaller count, and it does not require the 4 in edge bays.

Neither 10 nor 9 is the governed stringer count. Purchase quantities stay on the unsent P1 take-off until one layout is accepted.

## Stringer throat — unresolved

CT-2 R2 calculates the remaining throat as 4.997 in and labels it 5.00 in, with the words STRUCTURAL VERIFICATION REQUIRED.

The calculation uses a 11.25 in stringer, an 11 in going, and a 7.60 in rise:

throat = 11.25 − (11 × 7.60) / hypotenuse(11, 7.60) = 4.997 in.

No stringer-throat limit was found in the design brief, the take-off, the drawing standard, or the rest of the repository docs searched for this slice. Rise and run inside the private-stair limits named on the sheet do not certify the remaining section.

Authority still required: a structural reviewer, or the prescriptive cut-stringer standard the municipality accepts for this 2×12, this rise, and this run.

## What was not done

No drawing was regenerated. No take-off line was edited. No supplier request was sent. No price was created.
