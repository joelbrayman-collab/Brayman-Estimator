# People & Access: invitation emails, the sender's confirmation and Email history

| Attribute | Value |
|-----------|-------|
| Status | v1rel8 (23 Oct 2026); not deployed until the release is approved |
| Owner brief | Joel, 23 Oct 2026: tell the person who pressed the button that the invitation went, and show each person's recent emails |
| Database | No migration. Uses `transactional_messages` (no link, token or body is stored there) |
| Code | `app/routes/people_access.py` (`_send_link`, `_confirm_to_sender`, `email_history`), `app/services/transactional_email.py` (`INVITATION_SENT_CONFIRMATION`), `app/templates/settings/people/detail.html` (Email history) |
| Tests | `tests/test_people_access_pages.py` |

## What happens when the owner (or a System Administrator) sends a link

Company → People & Access → a person → **Email a link to choose a password** (or adding a person):

1. The invitation (`ACCOUNT_INVITATION`, 72 hours) or set-password email (`PASSWORD_RESET`) is sent through the
   shared transactional email service, with its allowlist, exactly as before.
2. **If the mail service accepted it** (Postmark or SMTP accepted; on a development office, the captured file),
   a second, separate email goes to the person who pressed the button (`INVITATION_SENT_CONFIRMATION`):

   > Your CalibraytAI invitation to Nora New (nora@example.com) was sent at Oct 23, 2026 at 9:14 AM. It works once
   > and expires Oct 26, 2026 at 9:14 AM.

   It never contains the link or any part of its token (the link is a credential), and the real invitation is
   never copied (no cc or bcc). The template is built only from the name, the address, the kind and the two
   times. It obeys `TRANSACTIONAL_UAT_ALLOWLIST` like every other send: a sender who is not on the list gets no
   confirmation (recorded as `SKIPPED_ALLOWLIST`). If the confirmation fails, the invitation's outcome and the
   page the owner sees do not change.
3. **If the invitation was not delivered** (allowlist, not configured, refused, or captured on a hosted office or
   the training site), there is no confirmation: the owner is shown the one-time link on the page instead, as
   before.

The training site runs the same code. Its captured mail is never a delivery, so confirmations are sent there only
when its SMTP server accepted the invitation.

## Email history on the person's page

The person's People & Access page lists the last 5 emails to that person's address from `transactional_messages`:
when, what kind (Invitation, Set-password link, Proposal, ...), and **Sent** or **Not sent** with the plain reason
(for example "this office only emails the test addresses on its allowlist" or "email delivery is not set up on this
server"). No links are shown or stored.
