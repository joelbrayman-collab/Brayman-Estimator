# Definition of Done Evidence — 18 Oct 2026

Definition of Done item 5: "Full tests pass (actually run), or an explicit Joel-approved exception is recorded." No exception is requested.

| Commit | Branch | Environment | Passed | Failed | Errors | Skipped | Warnings | Time | Exit |
|---|---|---|---|---|---|---|---|---|---|
| `5094a2e` | `cleanup/technical-2026-10-18` | cloud, clean checkout, Python 3.9.6, fresh venv from the lock | 2766 | 0 | 0 | 11 | 8870 | 4225.8 s | 0 |
| `66f7772` | `security/closure-2026-10-18` | cloud, clean checkout, Python 3.9.6, fresh venv from the pinned `requirements.txt` | 2796 | 0 | 0 | 11 | 8916 | 3855.7 s | 0 |

Both runs include the end-to-end contractor walk (Chrome), the Cal tests, every calculator test, the browser tests at desktop and 390 px, and the signing, contract, authentication and isolation tests. Release browser checks: 43 / 43 on both. Darcy nine-step demonstration: completed on both (59 screens, no error responses).

## The 11 skips

All in `tests/test_historical_ingestion.py`: the 20 source workbooks are real customer estimates kept only on the office Mac (`~/Desktop/CalibAi Historical Estimates`, 21 files, all downloaded on 18 Oct). They are not copied to the cloud. On the Mac they run, and the release gate stops on **any** skipped test, so the release run must show 0 skipped.

## Still to run

The native Mac regression inside the release gate, for each release.
