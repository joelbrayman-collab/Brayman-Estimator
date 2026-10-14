# Deck takeoff — J1 purchasing reconciliation

| Field | Value |
|-------|--------|
| Date | 2026-10-13 |
| Evidence | `tests/test_deck_takeoff_reconciliation.py`, `tests/test_linda_j1_mapping.py` |
| Basis | Synthetic copy of J1 and the dry-run J1 mapping (`tools/linda_j1_construction_model.py`). The real project was not read or changed. |

Every structural cut is placed exactly once (2×8: 57 cuts, 2×10: 16 plies, 2×12: 10 stringers, 6×6: 9 cut posts; 6 lower posts ordered uncut). On every stick the cuts plus one kerf between neighbours fit the stock; the offcut is recorded; waste equals kerf plus offcut; purchased length equals cuts plus waste. Results are identical when the members are supplied in reverse order.

| Material | J1 | Engine | Why |
|---|---|---|---|
| 2×8 × 12 ft | 20 sticks | 20 when offcuts stay with their use (J1 rule); 18 when offcuts are reused across uses | The 2 sticks come only from placing header pieces and blocks on joist offcuts. Whether that is allowed is Brayman's cutting decision (`cutting.offcut_reuse`). |
| 2×10 | 4 × 10 ft + 7 × 12 ft = 124 ft | 124 ft at zero kerf; 6 × 10 ft + 6 × 12 ft = 132 ft at 1/8 in kerf | J1 cut two 72 in front plies from each 144 in stick. With a saw kerf, 72 + 72 + 1/8 in exceeds 144 in. The smaller J1 figure is only valid if the stock is longer than nominal. |
| Decking on the J1 board basis (5.5 in, no gap, no kerf) | 446 ft (11 × 20 + 17 × 10 + 7 × 8) | 432 ft (21 × 20 + 1 × 12) with offcuts reused | All 48 board cuts placed once and fit their sticks. This is a test basis only; PVC/composite boards wait for their manufacturer's width, gap, and stock lengths. |

A smaller quantity is not taken as correct by itself: each figure above is checked stick by stick.
