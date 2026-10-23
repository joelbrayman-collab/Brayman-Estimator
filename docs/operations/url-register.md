# CalibraytAI address register

Authoritative list of the live addresses. Verified 22 October 2026 (HTTPS answered, page as stated).
Update this file whenever an address moves; older addresses stay listed under "Retired" for the record.

## Live

| What | Address | Host | Who can open it |
|---|---|---|---|
| Public website | https://calibraytai.com (also https://www.calibraytai.com) | HostPapa VPS (208.79.219.97), Let's Encrypt certificate | Public |
| Contractor platform (office) | https://calibryatai.onrender.com/login | Render, service `Calibryatai` (`srv-dar95mh42hec73df4rug`) | Signed-in office people |
| Field (crew on iPhone) | https://calibryatai.onrender.com/field | Render (same service) | Signed-in crew |
| Supplier Hub | https://calibryatai.onrender.com/supplier/login | Render (same service) | Signed-in supplier staff |
| Training & Acceptance Centre | https://training.calibraytai.com/training/signin | HostPapa VPS, service `calibrayt-training`, data on the server's disk | Training accounts (email + password for that site) |
| Contractor Workflow Map | Office: Workflow Guide in the menu, `/workflow` (from release v1rel6). Training: https://training.calibraytai.com/training/review/contractor | Render / HostPapa | Signed in; owner review on the training site without registering |
| Supplier Workflow Map | Supplier Hub: Workflow Guide, `/supplier/<id>/workflow` (from v1rel6). Training: https://training.calibraytai.com/training/review/supplier | Render / HostPapa | Signed in |
| Field Workflow | `/field/workflow` (from v1rel6); training: https://training.calibraytai.com/training/review/field-crew | Render / HostPapa | Signed in |
| Calendar printout | Office: Calendar → Print (top right, under + New Appointment), `/schedule/print?from=YYYY-MM-DD&to=YYYY-MM-DD` (optional `scope=mine` or `company`, `project_id=`); up to 92 days, From and To included (from the calendar print change of 23 Oct 2026, not yet released) | Render (same service) | Signed-in office people; the same entries their calendar shows them. Field-only crew are sent to Field |
| Site Plans (crew iPhone Home Screen app and office plans viewer) | https://calibryatai.onrender.com/site-plans/ (Home Screen start `/site-plans/?source=home-screen`; sign-in `/site-plans/sign-in`; a project's plans `/site-plans/projects/<id>`, opened from the Plans button on every office project page). See [site-plans.md](site-plans.md) (from the Site Plans change of 23 Oct 2026, not yet released) | Render (same service) | Signed in. Field-only crew: only the jobs they are booked on (Field's rule). Office: the organization's active projects, and any of its projects from that project's Plans button |
| Contractor Storybook | https://claude.ai/artifact/EbLLAUMkuX2b9vj7M1EMtk | Claude artifact | Whoever Joel shares it with (Share → anyone with the link) |
| Supplier Storybook (BMR Winchester edition) | https://claude.ai/artifact/PV6APezvX4iAUV5jXP4GEj | Claude artifact | As shared |
| Supplier Connection Storybook (supplier-neutral) | https://claude.ai/artifact/NhdXg7hccjDMq8E8n1278b | Claude artifact | As shared |

The contractor platform, Field and Supplier Hub were not moved: production stays on Render.

## Retired (do not give out)

| Address | Was | Status 22 Oct 2026 |
|---|---|---|
| https://calibai.joel-brayman.chatgpt.site/ | Public website (ChatGPT-hosted, Version 31) | Still answers; replaced by calibraytai.com |
| https://calibraytai-training-preview.onrender.com | Training Centre preview (free plan, data wiped on restart) | Still answers; to be suspended in Render |
| https://claude.ai/artifact/Rd5LyVRRncyyTDT2suG26i | Earlier Contractor Storybook edition (18 Oct) | Superseded by EbLLAUMkuX2b9vj7M1EMtk |
