# Calibrayt office guide

Brayman Construction. 7 October 2026.

This is the operating and recovery pack for the first controlled Brayman project. It is the guide Ben uses. It is not a contract, and it is not the finished User Guide.

The first real project goes on the Mac office. Joel starts that office. Ben does not start a second one, and Ben does not use the website for a real job.

## 1. What Calibrayt does

Calibrayt is the Brayman office for a job.

You keep the customer, the project, the location, the estimate, the customer price, the field notes, and the actual costs in one place. You can ask a supplier for a price. You can give the customer a construction estimate.

You cannot produce an executable construction contract from Calibrayt until counsel has approved the Ontario package. Until then the Contract section stays blocked. That block is doing its job.

## 2. Which office

Use only the office Joel has opened on the Brayman Mac.

1. Joel starts it from the Brayman-Estimator folder with `flask run --port 5001`. On this Mac, port 5000 is already used by the system, so the office does not use 5000.
2. On that Mac, open `http://127.0.0.1:5001`.
3. If Joel gives you a different address, use that address. Do not guess another one.

The program in the development folder and the program on the website are not the same thing. A newer folder does not change the office you are signed into.

Office identity checked 7 October 2026:

- Mac office file: `instance/brayman_estimator.db`
- That file is intact. Its office revision is `q7d8e9f0a1b2`. Size 3,645,440 bytes. Last changed 2026-10-07 11:06:09.
- The backup taken immediately before that structure update is revision `h8c9d0e1f2a3`. It is recorded in the backup log.
- This is the office for the first real project.
- Website: `https://calibryatai.onrender.com`. Last recorded live program `ff9d6791c4bb16ef50d42a9ca71af2a1d6bc051b`, deploy `dep-dav9uk97lnhs73bj35pg`. Auto-deploy is off.
- The website is a separate copy. Password sign-in there is not settled. A temporary bypass was last left on. Do not enter a real job there.
- Development folder `0db938d6bdbd9d5d8a54b60900f26b088c8ee3b2` is not what the website is running.

Some older practice jobs are already in the Mac office. Do not delete them. Do not use one as the real customer job. Ask Joel which project is the real one.

## 3. Sign in

1. Open the Mac office address.
2. The screen says Office sign in.
3. Use the email and password Joel gave you.
4. Choose Sign in.

There is no Create Account button. Do not make a second user.

Forgot Password may say to check your email. Do not wait on that email. Ask Joel to set the password.

If the office asks you to sign in again later, sign in and open the same project. Then check that the last field note is actually on the project. See section 13.

Each main screen has Help. It explains that screen. Help does not change the job.

## 4. Start a project

1. If the customer is not already under Clients, open Clients and choose New Client.
2. On Home, choose + Start New Project.
3. Project name and client are required. Save.
4. Open the project.
5. Under Documents, choose Review location.
6. Enter the street, the municipality, and the province. Postal code is optional. Save.
7. A permit report is not municipal approval. Read it. Do not treat it as a permit.

Incomplete location is allowed while you are setting the job up. A production contract cannot be generated from an incomplete location. With a complete Ontario location, the contract still stays blocked until an approved legal package exists. See section 9.

## 5. Plan

Planning on the project is the Documents section.

1. Upload the plan PDF you already have.
2. Review the job address.
3. Read the permit report. It is not approval to build.

Calibrayt does not produce the crew drawing set. If you do not have a drawing, say so. Do not ask the office to invent one.

An approved take-off package can be mapped into an estimate. Open that package and choose Map to estimate. Review the line. Choose Insert into estimate. Nothing is added until you do that. The project page points to that same action. It does not add the line itself. Do not type a quantity the package does not show.

If there is no approved package, go to Price and enter the lines you actually know.

An our-crew ICF wall can use the existing wall-form path. A line is added only after you confirm it. Other trades do not have that path.

## 6. Price

1. On the project, under Estimates and proposals, choose New estimate.
2. Open the current version.
3. Add a section, then add the lines you know. Leave unknown lines off the estimate.
4. Read Costing review.
5. Open Scope Delivery Review. Confirm who provides the material and who does the work. Approve all costing requires that confirmation. An unconfirmed line blocks approval. Confirming the review does not approve the cost.
6. If a line is still blocked, fix that line or take it off. Do not approve over a block.
7. The Human actor box may show Joel Brayman. If you are the person approving, replace that with your own name.
8. Choose Approve all costing.
9. Choose Apply org pricing policy. That button stays off until costing is approved.
10. If the screen says working costs changed, approve costing again before you apply pricing again.

Approve all costing approves the cost. It does not approve the customer price by itself, and it does not approve a supplier's price.

Internal Detailed Cost Breakdown is the office cost sheet. It stays in the office.

## 7. Supplier

The path is:

1. The project has a material requirement.
2. Open Supplier Package on the project.
3. Select the supplier.
4. Choose Supplier Estimate Request.
5. Send that sheet to the supplier.
6. When it comes back, give it to Joel.

Unit price, line price, and the supplier code stay blank on the way out. A blank is not zero. Where the purchase quantity is not known, the quantity stays TBD. Do not invent a quantity, a code, or a price.

The supplier account on this Mac office is labelled DEMO / SYNTHETIC. That label stays on the request. It does not fill in a price.

The supplier does not approve Brayman's cost. Brayman decides the cost after the supplier has answered.

The Linda Bushel sheet for BMR Winchester is a real-world proving exercise. It is not a reason to change this office. Darcy's reply comes back as a document. The office does not read that reply in by itself.

Generate Supplier Package and Issue Supplier Package are a different record. They are not the supplier estimate request.

## 8. Customer estimate

1. On the estimate version, choose Create Proposal.
2. If the office says to create a proposal template first, stop and tell Joel. Do not invent one.
3. Review the proposal.
4. Choose Download PDF.
5. Read it before it leaves the office.

The customer document title is CONSTRUCTION ESTIMATE. It is the price you are showing the customer. It is not the construction contract. Do not put internal cost or margin on it.

When the customer has committed, open that proposal. Set Update status to Accepted. That is the acceptance record. It is not the construction contract.

Warranty words typed into a proposal are not an approved Ontario warranty.

## 9. Contract

This is the rule.

Calibrayt does not generate an executable contract when an approved jurisdictional legal package is unavailable.

On the project, Contract may say Production contract unavailable. The usual line is: no active counsel-approved contract package is available for this jurisdiction. It also says contract generation is blocked, no production contract has been generated, a commercial presentation draft is not used as a substitute contract, and this screen does not override the legal-content gate.

A complete street address can still show this block. The office currently knows City of Ottawa. An address outside that municipality may say the location is not complete, or that no approved package is available. The block is intentional. Do not bypass it.

When you see that:

1. Stop.
2. Do not look for a way around it.
3. Do not download a draft and call it the Brayman contract.
4. Do not tell the customer that Calibrayt produced the contract.
5. The estimate and the proposal are still usable. The block does not break them.
6. The paper contract, if there is one, stays with counsel and with Joel.

Family 05 is a presentation master. It is not an approved Ontario contract. Do not use it as one.

## 10. Build and field

On the project, Project work is where the job is run after the estimate exists.

Field, on the phone or the office browser:

1. Open Field.
2. Open the project and confirm it. The button is Confirm and Capture, or Confirm for Today.
3. On Capture, save the note, the photo, or the voice you actually have.
4. Back on the project, open Field Observations and confirm the note is listed.

You can also choose Add text observation on the project.

Change orders are office records. On the project, New Change Order. Or, on the estimate version, Create Change Order. Record what changed. Do not send the customer a Calibrayt signing link. Email delivery for signing is not the operating path.

A field note is evidence. It is not an actual cost. Enter the cost under Money only when you know the amount.

Closing the project, a punch-list closeout, and a client walkthrough are later. Do not close the job to "finish setup."

## 11. Monitor

On the project, Money is Estimated versus actual.

It compares the committed estimate with actual direct costs entered in the office. It is not a profit figure.

Money shows the committed baseline after the estimate version is locked. On the estimate version, choose Lock. Accepting the proposal does not lock the version by itself. Until the version is locked, do not type a number to force the comparison.

1. Read the What, Why, and Next lines already on that section.
2. If it says the comparison cannot be made yet, do not type a number to force one.
3. When you know a labour, material, subcontract, or other direct cost, enter that actual.
4. Leave field notes as evidence. They do not fill the actual cost by themselves.

## 12. Backup and recovery

Ben does not back up the office and Ben does not restore it.

Joel follows the printed backup sheet: `v1-backup-restore-checklist.md`. The backup made on 7 October 2026, before the office structure update, is in the backup log. He does it again at the end of any day a real project changed, and again before any change to the office file's structure.

There is no automatic backup service. The procedure is a controlled copy. Joel makes it. The copy is checked. A second copy is kept outside the live file. The backup log records the file name.

If the office will not open, or the project you just saved is gone:

1. Stop typing.
2. Do not start the office again if the office file is missing. Starting it can create an empty office.
3. Do not delete the file, rename it yourself, or run a repair.
4. Call Joel. Joel restores from the last checked copy.

## 13. Known limits

- The contract block is intentional. Do not bypass it. It stays until counsel approves the Ontario package. A complete address outside City of Ottawa can still show the block. Family 05 is not that package.
- The Mac supplier account is labelled DEMO / SYNTHETIC.
- If a field session ends before the note appears under Field Observations, the note may not have been saved. Sign in, look, and enter it again if it is missing. Do not delete other notes to fix it.
- Calibrayt does not produce professional construction drawings.
- The office will not calculate a deck, a roof, siding, drywall, or flooring for you. Enter the lines you know. An our-crew ICF wall is the path that already confirms a quantity onto an estimate line.
- A supplier answer comes back on paper or in a file. You give it to Joel. The supplier does not approve the cost.
- QuickBooks-ready entry is a sheet a person uses. Calibrayt does not send the estimate to QuickBooks.
- Forgot Password email is not the way a password gets reset. Ask Joel.
- Do not email a customer a Calibrayt signing link.
- Practice jobs stay in the office. Do not delete them.
- LEARN does not recommend work on this project.

## 14. When something goes wrong

Call Joel Brayman. Tell him the date, the project name, what you clicked, and the words on the screen. Say whether you had already approved costing, downloaded a supplier sheet, or sent anything to a customer.

Do not delete the project. Do not rewrite an accepted proposal. Do not type a contract. Do not copy or rename the office database. Do not keep working in an office that looks empty.

Joel writes the note in `docs/operations/v1-issue-log.md`. That is the record. Ben does not have to edit that file.
