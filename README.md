# CalibraytAI storybooks — website files

Built storybooks for https://calibraytai.com/storybook/ (HostPapa VPS). Each page carries `noindex, nofollow`.

| Address | Book |
|---|---|
| /storybook/contractor/ | The Contractor Storybook |
| /storybook/supplier-connection/ | CalibraytAI — Supplier Connection (supplier-neutral master) |
| /storybook/bmr-winchester-<private>/ | Your Price in More Estimates — BMR Winchester (proposal for discussion) |
| /storybook/kbc-<private>/ | Supplier Connection — prepared for KBC, Kemptville (proposal for discussion) |

Install or update: run `install_storybooks.sh` as root in WHM Terminal. Sources: `docs/storybook/supplier-editions/` on `feature/supplier-storybook-editions`.

The BMR and KBC editions are not at guessable addresses. The install script makes a random name for each once, on the server only (`/root/calibrayt-storybook-links.txt`, readable by root), reuses it on every run and prints the two private links at the end. The names are not in GitHub. `/storybook/` itself does not list its folders. Anyone who is given a private link can open it, so give each only to that supplier.
