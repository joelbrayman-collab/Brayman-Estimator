# Sign-in and email (v1rel13, 26 Oct 2026)

Joel's rules: **one email address and one password for every CalibraytAI site a person may use**, and **nobody's
ability to get in depends only on an email arriving.**

## One identity (Production is the source of truth)

Production (calibryatai.onrender.com) and the Training Centre (training.calibraytai.com) are separate copies of
CalibraytAI with separate databases. Before v1rel13 each kept its own passwords, so a password set on one meant
nothing on the other. Now:

- **Production holds every real person's one password** (`app/services/identity.py`).
- **The Training Centre asks Production** when a real person signs in, changes their password or uses Forgot
  password (server to server, `/identity/api/*`, with a per-site secret). A new password works on both at once.
- **What a person may do stays per site**: a Training Centre account (company, Field only, training
  administrator) is the Training Centre's; a Production membership is Production's. A reviewer such as Kevin has an
  identity on Production but no Production membership: Production politely refuses him and points to the Training
  Centre.
- **Adding a person on the Training Centre** creates their one identity on Production if they have none (an existing
  identity is never changed: they just use the password they already have). The owner gets Production's one-time
  link with Copy and Text it.
- **Practice personas** ("… (training)", addresses ending in `.invalid`) are not people: they keep local passwords on
  the Training Centre and never reach Production.
- **Sessions**: an existing Training Centre session ends at its normal time after a password change made elsewhere;
  every new sign-in uses the new password.

Connecting the Training Centre (WHM Terminal, after v1rel13 is on both sites): `tools/hosting/training_identity.sh`
`prepare` (makes the secret, shows the Render value once) → add `IDENTITY_CLIENTS` and `IDENTITY_TRAINING_SITE_URL`
in Render → `connect` (switches over, lists how each person is matched; undoes itself if Production refuses) →
`reconcile` (people who existed only on the Training Centre keep the password they chose there; where both sites
had a password, Production's wins). `disconnect` is the break-glass back to local passwords (then set any password
with `flask auth reset-password` on the Training Centre).

## How a person gets in

1. The owner (or a System Administrator) adds them in **Company → People & Access → Add person**, or presses
   **Email a link to choose a password** on their page. Suppliers: **Company → Suppliers**, the same way.
2. CalibraytAI emails a one-time set-password link **and shows the owner the same link, once**, with:
   - **Text it**: opens Messages on an iPhone or Mac with a ready message ("Hi Nora, here is your CalibraytAI
     sign-in link…"); choose the person and send. No Twilio.
   - **Copy message** and **Copy link**.
3. The link works once and expires (72 hours for an invitation, 1 hour for a password link). Sending a new link
   replaces the old one.
4. If nothing arrives, the person's Forgot-password page tells them to check junk, then ask the owner, who sends
   a new link and texts it.

## What "sent" means: the words on the person's page (Email history)

| Shown | Meaning |
|---|---|
| **Delivered** | Postmark confirmed the receiving mail server (iCloud, Gmail…) took it, with the server's own words |
| **Bounced: reason** | It was refused; the reason is Postmark's |
| **Marked as spam by the recipient** | They pressed "junk" on it |
| **Delayed: the mail service is still trying** | The receiving server asked Postmark to try again later |
| **Waiting for the mail service to confirm delivery** | Postmark accepted it; no report yet. Press **Check delivery now** |
| **Handed to the server's mail system (delivery cannot be confirmed)** | Sent by SMTP (the old training-site path): nothing reports back |
| **Not sent: reason** | It never left CalibraytAI (allowlist, not set up, refused) |

"Accepted" is never shown as delivered. Delivered means the person's mail server took it; if it is still not in
their inbox or junk, send a new link and text it.

Reports arrive two ways: Postmark's webhooks (instant) and **Check delivery now** (asks Postmark directly; works
even before the webhook is set up).

## Settings

| Setting | Where | Value |
|---|---|---|
| `IDENTITY_CLIENTS` | Production (Render) | `training=<secret>` from `training_identity.sh prepare` |
| `IDENTITY_TRAINING_SITE_URL` | Production (Render) | `https://training.calibraytai.com` |
| `IDENTITY_PROVIDER_URL`, `IDENTITY_CLIENT_ID`, `IDENTITY_CLIENT_SECRET` | Training Centre (`/opt/calibrayt/env`) | set by `training_identity.sh` |

Email, on both sites: Production (Render → calibryatai → Environment) and the Training Centre (`/opt/calibrayt/env` on HostPapa):

| Setting | Value |
|---|---|
| `TRANSACTIONAL_EMAIL_PROVIDER` | `postmark` |
| `POSTMARK_SERVER_TOKEN` | that site's Postmark server's **Server API token** (secret) |
| `TRANSACTIONAL_FROM_EMAIL` | an address on the Postmark-verified domain |
| `POSTMARK_WEBHOOK_USERNAME`, `POSTMARK_WEBHOOK_PASSWORD` | the Basic auth credentials typed into Postmark's webhook form (secret) |
| `PUBLIC_BASE_URL` | `https://calibryatai.onrender.com` / `https://training.calibraytai.com` |
| `TRANSACTIONAL_UAT_ALLOWLIST` | empty once Joel authorizes sending to anyone |

The Training Centre is switched with `tools/hosting/training_email_to_postmark.sh <from address>` (WHM Terminal; asks
for the token at a hidden prompt, backs up the settings, shows the webhook credentials once).

`flask email status` prints how a server sends email (names only; secrets as set / not set).

## Postmark (one account, one server per site)

- **Domain**: Sender Signatures → the domain → **DNS Settings**: add the DKIM TXT record and the Return-Path CNAME
  it shows, then **Verify**. Once DKIM is verified any address on the domain can send.
- **Approval**: until Postmark approves the account, it only sends to the account's own verified domains
  (this is why only @braymanconstruction.ca addresses received email). The Account Owner requests approval in the
  account; reviews usually take about a day on weekdays.
- **Servers**: "CalibraytAI production" and "CalibraytAI Training Centre", each with its own Server API token.
- **Webhook** (each server): the server → **Default Transactional Stream** → **Webhooks** → **Add webhook**:
  URL `https://<site>/webhooks/postmark`, Basic auth username and password = the two settings above, events
  **Delivery**, **Bounce**, **Spam Complaint** → **Send test** → **Save webhook**.
- **DMARC**: a TXT record `_dmarc.<domain>` = `v=DMARC1; p=none; rua=mailto:<an inbox you read>` to start.

## Emergency access (the server's shell; no email)

Prints a one-time set-password link for an existing, active sign-in; nothing is emailed. On the Training Centre,
for a real person, the link comes from Production and sets the one password:

- Production (Mac Terminal):
  `ssh srv-dar95mh42hec73df4rug@ssh.virginia.render.com 'cd /opt/render/project/src && if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=$(command -v python3); fi; $PY -m flask auth issue-link --email you@example.com'`
- Training Centre (WHM Terminal):
  `sudo -u calibrayt bash -c 'cd /opt/calibrayt/app && set -a && . /opt/calibrayt/env && set +a && ./venv/bin/flask auth issue-link --email you@example.com'`

`flask auth reset-password --email …` (hidden prompt) sets a password directly.

## Proving delivery

`flask email test-delivery --to <inbox> [--wait 180]` sends a test with a six-character code in the subject and
waits for Postmark. It prints **ACCEPTED** and **DELIVERY** separately; then check the inbox (and junk) for
"CalibraytAI email test <code>". Run it to an iCloud and a Gmail address on each site before inviting anyone.

## Tests

`tests/test_signin_email_reliability.py` (fake mail service and fake Postmark; no network).
