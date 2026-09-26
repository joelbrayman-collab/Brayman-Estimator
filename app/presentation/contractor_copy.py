"""FG-025 contractor-facing display mapping (Slice 1–6) plus FG-024 CONTRACT Hub copy.

Presentation only. Deterministic. No DB access, I/O, service ownership,
commercial calculations, or mutation. Internal domain keys stay authoritative.
"""

from __future__ import annotations

from datetime import datetime

MONITOR_STATE_LABELS = {
    "MISSING_ACTUALS": "No actual costs entered yet",
    "MISSING_CUSTOMER_COMMITMENT": "No accepted proposal yet",
    "AMBIGUOUS_COMMITMENT": (
        "More than one accepted proposal — this screen will not pick one"
    ),
    "MISSING_ORIGINAL_BASELINE": (
        "An accepted proposal exists, but the original estimate cannot be used"
    ),
}

COST_CLASS_LABELS = {
    "other_direct": "Other direct cost",
    "labour": "Labour",
    "material": "Material",
    "subcontract": "Subcontract",
}

CO_COST_DELTA_INTERNAL = "CO cost delta not stored"
CO_COST_DELTA_LABEL = (
    "Change Order estimated cost is not stored on the Change Order"
)
CO_COST_DELTA_NOT_CAPTURED = "Not captured"
CO_COST_DELTA_INCLUDED = (
    "Extra-work approved internal direct cost is included"
)
NOT_CAPTURED_LABEL = "Not captured"

CURRENT_ACTUALS_HEADING = "Current actual costs"
CURRENT_ACTUALS_EMPTY = "No current actual-cost entries"
PREVIOUS_ENTRIES_HEADING = "Previous entries"
CORRECTED_ITEM_LABEL = "Corrected"
CORRECTED_BY_HEADING = "Corrected by"
PREVIOUS_ENTRIES_EMPTY = "No previous cost corrections."
RECORD_CORRECTION_BUTTON = "Record correction"
SOURCE_HEADLINE = "Source of these numbers"
PRICING_ASSUMPTIONS_HEADING = "Pricing assumptions"
NO_PRICING_ASSUMPTIONS = "No pricing assumptions recorded."
LEGACY_PRICING_ASSUMPTIONS_HEADING = (
    "Legacy project — pricing assumptions not recorded"
)
PERMIT_FOUNDATION_EYEBROW = "Preliminary / foundation only"
PERMIT_ADVISORY_EYEBROW = "Advisory only"
PERMIT_RECHECK_HEADING = "Recheck required"
PERMIT_RECHECK_WHY = (
    "Location, plan/site facts, or rules have changed since the last report."
)
PERMIT_NOT_MUNICIPAL_APPROVAL = (
    "This is not zoning approved, permit-ready, permit approved, or building-code "
    "approved. A passing check never means the municipality has issued a permit."
)
PERMIT_LOCATION_NOT_APPROVAL = (
    "This records the job address and permit context. It does not mean zoning "
    "approved, permit-ready, permit approved, building-code approved, or reviewed "
    "by the municipality or permit office."
)
PERMIT_GENERATE_HEADING = "Create permit report"
PERMIT_GENERATE_HELP = (
    "Creates a new saved report from the current reviewed facts. Earlier reports "
    "are not changed."
)
PERMIT_GENERATE_BUTTON = "Create permit report"
PERMIT_REQUIREMENT_LABEL = "Requirement"
PERMIT_PDF_BANNER = "Advisory only — this is not municipal permit approval"

COST_LIBRARY_NAV_TITLE = "Cost library"
COSTS_AND_PRICING_NAV_TITLE = "Costs & pricing"
WHAT_WE_PAY_NAV_TITLE = "What we pay"
REUSABLE_WORK_NAV_TITLE = "Reusable work"
HOW_WE_PRICE_NAV_TITLE = "How we price"
COMPANY_LIBRARY_NAV_TITLE = "Company library"
PAST_JOBS_NAV_TITLE = "Past jobs"
PAST_JOBS_NOTE = (
    "These are old jobs kept for reference. They are not current estimates."
)
PROPOSALS_NAV_TITLE = "Proposals"
TEMPLATES_NAV_TITLE = "Templates"
ATTENTION_NAV_TITLE = "Attention"
BRAND_NAV_TITLE = "Brand"
WORK_CATALOG_NAV_TITLE = "Work catalog"
HISTORICAL_NAV_TITLE = "Previous estimates"
HISTORICAL_PAGE_TITLE = "Previous estimates"
HISTORICAL_HEADING = "Upload previous estimates"
HISTORICAL_READY_BADGE = "Uploaded — review before using in pricing"
HISTORICAL_UPLOAD_HELP = (
    "Select many workbooks, drag and drop files, or choose a folder where this "
    "browser supports it. Each file is checked on its own. Supported: .xlsx and "
    ".xlsm Excel workbooks. Macros and formulas are not run."
)
HISTORICAL_RECORDS_HEADING = "Previous estimate records"
HISTORICAL_SOURCE_HEADING = "Where these numbers came from"
HISTORICAL_FILE_LABEL = "Source file"
HUB_PRICING_RECORDED_HEADING = "Pricing recorded"
HUB_LABOUR_RECORDED_HEADING = "Labour rates recorded"
HUB_RECORDED_LABEL = "Recorded"
HUB_NOT_RECORDED_LABEL = "Not recorded"
HUB_PRICE_LIST_NOTE = (
    "This list shows whether pricing and labour rates have been recorded for each "
    "estimate. This page does not recalculate selling price, margin, or labour cost."
)

HISTORICAL_FAMILY_LABELS = {
    "FAMILY_A": "Workbook A",
    "FAMILY_B": "Workbook B",
    "FAMILY_C": "Workbook C",
    "FAMILY_D": "Workbook D",
    "FAMILY_E": "Workbook E",
}

HISTORICAL_UPLOAD_OUTCOME_LABELS = {
    "INGESTED": "Loaded",
    "DUPLICATE": "Already uploaded",
    "QUARANTINED": "Needs review",
    "UNSUPPORTED": "Not supported",
    "FAILED": "Could not load",
}

EMPTY_COPY = {
    "MISSING_ACTUALS": {
        "what": "No actual costs have been entered yet.",
        "why": "Margin so far cannot be shown as $0.00.",
        "next": "Use Record actual direct cost below.",
    },
    "MISSING_CUSTOMER_COMMITMENT": {
        "what": "No accepted proposal yet.",
        "why": "Original estimated figures are not treated as a committed baseline.",
        "next": "Accept a proposal when the customer has committed.",
    },
    "AMBIGUOUS_COMMITMENT": {
        "what": (
            "More than one accepted proposal — this screen will not pick one."
        ),
        "why": "Original estimated baseline is not shown as committed.",
        "next": "This hub does not choose among them.",
    },
    "MISSING_ORIGINAL_BASELINE": {
        "what": (
            "An accepted proposal exists, but the original estimate cannot be used."
        ),
        "why": "Original estimated baseline is not shown as committed.",
        "next": "The locked source estimate is missing or unusable.",
    },
}


def monitor_state_label(state: str | None) -> str:
    if not state:
        return ""
    return MONITOR_STATE_LABELS.get(state, state)


def cost_class_label(cost_class: str | None) -> str:
    if not cost_class:
        return ""
    return COST_CLASS_LABELS.get(cost_class, cost_class)


def co_cost_delta_label(internal_copy: str | None) -> str:
    if internal_copy == CO_COST_DELTA_INTERNAL:
        return CO_COST_DELTA_LABEL
    if internal_copy == CO_COST_DELTA_NOT_CAPTURED:
        return NOT_CAPTURED_LABEL
    if internal_copy == CO_COST_DELTA_INCLUDED:
        return CO_COST_DELTA_INCLUDED
    return internal_copy or ""


def monitor_empty_copy(state: str | None) -> dict:
    if not state:
        return {}
    return EMPTY_COPY.get(state, {})


def monitor_source_headline() -> str:
    return SOURCE_HEADLINE


def monitor_source_detail(provenance: dict | None, authorized_co_count: int = 0) -> str:
    provenance = provenance or {}
    parts = []
    if provenance.get("accepted_proposal_id"):
        parts.append("accepted proposal")
    if provenance.get("source_estimate_version_id"):
        parts.append("estimate")
    if provenance.get("pricing_snapshot_id"):
        parts.append("pricing lock")
    if parts:
        source = "Based on " + ", ".join(parts) + "."
    else:
        source = "No proposal, estimate, or pricing lock is available yet."
    co_line = f"Authorized change orders: {int(authorized_co_count)}."
    last = provenance.get("last_actual_created_at")
    if isinstance(last, datetime):
        last_line = f"Last actual cost recorded: {last.strftime('%Y-%m-%d %H:%M')}."
    else:
        last_line = "No actual cost recorded yet."
    return f"{source} {co_line} {last_line}"


def entry_reference(record_id) -> str:
    if record_id is None or record_id == "":
        return ""
    return f"Entry reference {record_id}"


def sentence_label(value: str | None) -> str:
    if not value:
        return ""
    return str(value).replace("_", " ").replace("-", " ")


LABOUR_RATES_HEADING = "Labour rates"
PRICING_HEADING = "Pricing"
WORK_TYPES_HEADING = "Work types"
WORK_PLAN_HEADING = "Project work"
BUILD_WORK_PLAN_BUTTON = "Build project work"
ADD_WORK_ITEM_BUTTON = "Add work item"
ADD_ACTIVITY_BUTTON = "Add activity"
SCOPE_ORIGINAL_WORK = "Original work"
SCOPE_CHANGE_ORDER_WORK = "Change order work"
SCOPE_EXTRA_WORK_LABEL = "Extra work"
SCOPE_ORIGINAL_LABOUR = "Original labour"
SCOPE_APPROVED_CHANGES = "Approved changes"
SCOPE_CURRENT_AUTHORIZED = "Current authorized labour"
SCOPE_EXTRA_WORK_BANNER = (
    "This work has not yet been added to the authorized project. "
    "If the customer asked you to add, remove, move, or change something "
    "outside the work you were sent to do, record it as extra work."
)
SCOPE_EXTRA_WORK_RULE = (
    "If the customer asks you to add, remove, move, or change something "
    "outside the work you were sent to do: use Extra work."
)
FIELD_EXTRA_WORK_BUTTON = "Extra work"
FIELD_EXTRA_WORK_HEADING = "Extra work"
TIME_HEADING = "Time"
FIELD_TIME_BUTTON = "Time"
FIELD_MY_TIME_HEADING = "My time"
FIELD_SUBMIT_TIME = "Send time"
TIME_REVIEW_HEADING = "Time review"
TIME_APPROVE_BUTTON = "Approve"
TIME_RETURN_BUTTON = "Return"
TIME_APPROVE_SELECTED = "Approve selected"
TIME_HUB_HEADING = "Time"
LABOUR_HUB_HEADING = "Labour"
LABOUR_AUTHORIZED_HEADING = "Authorized work"
LABOUR_ALLOWED = "Allowed"
LABOUR_USED = "Used"
LABOUR_REMAINING = "Remaining"
LABOUR_WAITING = "Waiting for approval"
LABOUR_OVER_BY = "Over by"
LABOUR_ALLOWANCE_UNAVAILABLE = "Allowance not available"
LABOUR_EXTRA_NEEDS_REVIEW = "Needs review"
LABOUR_HOURS_USED = "hours used"
LABOUR_HOURS_WAITING = "hours waiting for approval"
LABOUR_NEEDS_ATTENTION_HEADING = "Needs attention"
COMPANY_ATTENTION_HEADING = "Company Attention"
COMPANY_ATTENTION_EYEBROW = "Company"
COMPANY_ATTENTION_QUESTION = "Where does my business need attention?"
PROJECT_CLOSED_NEW_WORK = (
    "This Project is closed. Reopen it before adding new work."
)
PROJECT_LIST_CURRENT = "Current"
PROJECT_LIST_CLOSED = "Closed"
PROJECT_CLOSE_ACTION = "Close Project"
PROJECT_REOPEN_ACTION = "Reopen Project"
PROJECT_ALREADY_CLOSED = "This Project is already closed."
PROJECT_ALREADY_CURRENT = "This Project is already current."
PROJECT_CLOSED_FLASH = "This Project is closed."
PROJECT_REOPENED_FLASH = "This Project is current."
PROJECT_CLOSE_CONFIRM_LEDE = (
    "Closing removes this Project from current operating work. "
    "Historical Project information remains available. "
    "New work cannot be added unless the Project is reopened."
)
PROJECT_REOPEN_CONFIRM_LEDE = (
    "Reopening returns this Project to current operating work. "
    "Existing Project history remains unchanged. "
    "New operating work may again be added under existing product rules."
)
PROJECT_CLOSE_CONFIRM_TITLE = "Close this Project?"
PROJECT_REOPEN_CONFIRM_TITLE = "Reopen this Project?"
PROJECT_LIFECYCLE_CANCEL = "Cancel"
PROJECT_CLOSE_OPEN_PUNCH_REQUIRED = (
    "This Project has open Punch List items. Confirm you intend to close it "
    "anyway. Closing does not complete or remove those Punch List items."
)
PROJECT_CLOSE_OPEN_PUNCH_CONFIRM = (
    "Close this Project with open Punch List items. They will stay open."
)
PROJECT_CLOSE_OPEN_PUNCH_WARNING = (
    "There are open Punch List items on this Project. Closing will not "
    "complete or delete them. They stay on the Project record. You can "
    "still close the Project deliberately."
)
PROJECT_LIST_CURRENT_EMPTY = "No current projects."
PROJECT_LIST_CLOSED_EMPTY = "No closed projects."
PUNCH_LIST_HEADING = "Punch List"
PUNCH_LIST_LEDE = "Physical work that still needs to be completed."
PUNCH_LIST_ADD = "Add Punch List Item"
PUNCH_LIST_CANCEL = "Cancel"
PUNCH_LIST_SAVE = "Save"
PUNCH_LIST_COMPLETE = "Mark Complete"
PUNCH_LIST_REOPEN = "Reopen"
PUNCH_LIST_DESCRIPTION = "Description"
PUNCH_LIST_WORK_SOURCE = "Work Source"
PUNCH_LIST_ORIGINAL_SCOPE = "Original Scope"
PUNCH_LIST_CHANGE_ORDER = "Change Order"
PUNCH_LIST_OTHER = "Other closeout work"
PUNCH_LIST_ORIGINAL_SCOPE_OPTIONAL = "Original Scope item"
PUNCH_LIST_CHANGE_ORDER_SELECTOR = "Existing Change Order"
PUNCH_LIST_STATUS_OPEN_LABEL = "Open"
PUNCH_LIST_STATUS_COMPLETE_LABEL = "Complete"
PUNCH_LIST_SUMMARY_COMPLETE = "Punch List complete"
PUNCH_LIST_SUMMARY_EMPTY = "Nothing is on the Punch List"
PUNCH_LIST_CREATED = "Punch List item added."
PUNCH_LIST_UPDATED = "Punch List item updated."
PUNCH_LIST_ITEM_COMPLETED = "Punch List item marked complete."
PUNCH_LIST_ITEM_REOPENED = "Punch List item reopened."
PUNCH_LIST_COMPLETE_EDIT = "Reopen this item before changing it."
PUNCH_LIST_DESCRIPTION_REQUIRED = (
    "Describe the physical work that still needs to be completed."
)
PUNCH_LIST_CHANGE_ORDER_REQUIRED = "Choose an existing Change Order."
PUNCH_LIST_INVALID_SOURCE = (
    "Choose Original Scope, Change Order, or Other closeout work."
)
PUNCH_LIST_INVALID_ASSOCIATION = "Choose a valid work association on this Project."
PUNCH_LIST_ITEM_NOT_FOUND = "That Punch List item was not found."
PUNCH_LIST_OPEN_ITEMS_BLOCK_SIGN_OFF = (
    "Open Punch List items must be completed first."
)
PUNCH_LIST_NONE_OPTION = "None"
PUNCH_LIST_CLOSED_VIEW = (
    "This Project is closed. Punch List history remains available."
)
WALKTHROUGH_HUB_HEADING = "Client Final Walkthrough"
WALKTHROUGH_LEDE = (
    "Ask the client if anything still needs attention. Client input is not the Punch List."
)
WALKTHROUGH_INVITE = "Invite Client to Final Walkthrough"
WALKTHROUGH_SEND_ANOTHER = "Send another invitation"
WALKTHROUGH_COPY_LINK_HINT = (
    "Copy this Final Walkthrough link and send it to the client. "
    "Email delivery is not configured for this step."
)
WALKTHROUGH_INVITED_FLASH = "Final Walkthrough invitation is ready."
WALKTHROUGH_STATE_NOT_SENT = "Final Walkthrough not sent"
WALKTHROUGH_STATE_SENT = "Final Walkthrough sent"
WALKTHROUGH_STATE_REVOKED = (
    "The Final Walkthrough invitation is no longer usable. "
    "Send a new invitation if the client should respond again."
)
WALKTHROUGH_STATE_RESPONDED = "Client responded"
WALKTHROUGH_STATE_AWAITING = "Client input awaiting review"
WALKTHROUGH_STATE_NOTHING = "Client had nothing to add"
WALKTHROUGH_ADD_TO_PUNCH_LIST = "Add to Punch List"
WALKTHROUGH_ALREADY_ADDRESSED = "Already Addressed"
WALKTHROUGH_DISCUSS = "Discuss / Not Part of Current Work"
WALKTHROUGH_WORK_SOURCE = "Work Source"
WALKTHROUGH_CLIENT_HEADING = "Final Walkthrough"
WALKTHROUGH_CLIENT_LEDE = (
    "Your project is nearing completion. Please let us know if there is "
    "anything you believe still needs attention."
)
WALKTHROUGH_WHAT_NEEDS_ATTENTION = "What needs attention?"
WALKTHROUGH_ADD_ANOTHER = "Add another item"
WALKTHROUGH_NOTHING_TO_ADD = "Everything looks complete — I have nothing to add."
WALKTHROUGH_SUBMIT = "Submit"
WALKTHROUGH_RECEIVED = "Thank you. We received your response."
WALKTHROUGH_CLOSED_VIEW = (
    "This Project is closed. Final Walkthrough history remains available."
)
WALKTHROUGH_DESCRIPTION_REQUIRED = "Describe what still needs attention."
WALKTHROUGH_RESPONSE_REQUIRED = (
    "Tell us what still needs attention, or choose that everything looks complete."
)
WALKTHROUGH_CONTRADICTORY_RESPONSE = (
    "Choose either items that need attention, or that everything looks complete — not both."
)
WALKTHROUGH_ITEM_NOT_FOUND = "That client input was not found."
WALKTHROUGH_INVITATION_NOT_FOUND = "That Final Walkthrough invitation was not found."
WALKTHROUGH_ALREADY_REVIEWED = "That client input has already been reviewed."
WALKTHROUGH_WORK_SOURCE_REQUIRED = (
    "Choose Original Scope, Change Order, or Other closeout work before adding this to the Punch List."
)
WALKTHROUGH_TOKEN_INVALID = "This link is invalid, expired, or already used."
WALKTHROUGH_TOKEN_EXPIRED = "This link is invalid, expired, or already used."
WALKTHROUGH_TOKEN_CONSUMED = "This link is invalid, expired, or already used."
WALKTHROUGH_TOKEN_RATE_LIMITED = "Too many tries. Please wait and try again later."
WALKTHROUGH_ACCEPTED_FLASH = "Client input added to the Punch List."
WALKTHROUGH_ADDRESSED_FLASH = "Client input marked already addressed."
WALKTHROUGH_DISCUSS_FLASH = "Client input marked discuss / not part of current work."
WALKTHROUGH_ORIGIN_CLIENT = "Client Walkthrough"
LABOUR_GETTING_CLOSE = "Labour getting close"
LABOUR_ALLOWANCE_USED = "Labour allowance used"
LABOUR_OVER_ALLOWANCE = "Labour over allowance"
LABOUR_EXTRA_WORK_NEEDS_REVIEW = "Extra work needs review"
SCHEDULE_FINISH_PASSED = "Scheduled finish passed"
SCHEDULE_NO_APPROVED_TIME = "Scheduled work has no approved Time"
LABOUR_NOTHING_NEEDS_ATTENTION = "Nothing needs attention right now."
ATTENTION_LINK_CHANGE_ORDERS = "Change orders"
COMPANY_CALENDAR_HEADING = "Company Calendar"
COMPANY_CALENDAR_LEDE = (
    "The month, the selected day, work still waiting for dates, "
    "and the project dates in this period."
)
COMPANY_CALENDAR_WAITING = "Waiting for dates"
COMPANY_CALENDAR_PERIOD = "This period"
COMPANY_CALENDAR_DAY = "Selected day"
COMPANY_CALENDAR_DAY_WORK = "Work on this day"
SCHEDULE_HEADING = "Schedule"
SCHEDULE_HUB_HEADING = "Schedule"
SCHEDULE_LEDE = "See what is happening now, what is next, and which authorized work still needs dates."
SCHEDULE_ADD = "Set dates"
SCHEDULE_EDIT = "Edit schedule dates"
SCHEDULE_RETIRE = "Retire these dates"
SCHEDULE_UNSCHEDULED = "Not scheduled yet"
SCHEDULE_UNSCHEDULED_HELP = "Authorized work with no dates yet. This is a schedule reminder, not a performance alert."
SCHEDULE_PROJECT_RANGE = "Project dates"
SCHEDULE_MOVE_PROJECT = "Move project"
SCHEDULE_EMPTY = "Nothing is scheduled in these dates"
SCHEDULE_FORM_HELP = "Choose the work and the start and end dates. Drag and drop is not required."
SCHEDULE_CONFIRM_ELEMENT = "Also change the work item dates so this activity stays inside them"
SCHEDULE_ASSIGNED = "Assigned"
SCHEDULE_UNASSIGNED = "Unassigned"
SCHEDULE_ASSIGN = "Assign"
SCHEDULE_REMOVE_ASSIGNMENT = "Remove"
SCHEDULE_CREW = "Crew"
SCHEDULE_CREWS_HEADING = "Crews"
SCHEDULE_CREWS_LEDE = "Named crews you can put on scheduled work. An organization can work with people only and never use a crew."
SCHEDULE_ADD_CREW = "Add crew"
SCHEDULE_RETIRE_CREW = "Retire crew"
SCHEDULE_ADD_CREW_MEMBER = "Add dates on this crew"
SCHEDULE_CLOSE_MEMBERSHIP = "Set last day"
SCHEDULE_CONFLICT = "Schedule conflict"
SCHEDULE_ALREADY_ELSEWHERE = "is already scheduled elsewhere"
SCHEDULE_ASSIGN_HELP = "Put a person or a crew on these dates. Unassigned is valid."
SCHEDULE_WORK_ORDER = "Work order"
SCHEDULE_WORK_ORDER_HELP = "Say which work comes after other work. This does not move dates by itself."
SCHEDULE_COMES_AFTER = "Comes after"
SCHEDULE_MUST_FOLLOW = "Must follow"
SCHEDULE_ADD_DEPENDENCY = "Add work order"
SCHEDULE_REMOVE_DEPENDENCY = "Remove"
SCHEDULE_SEQUENCE_WARNING = "Schedule warning"
SCHEDULE_BEFORE_PRIOR_FINISHED = "is scheduled before prior work is finished"
SCHEDULE_PRIOR_NOT_SCHEDULED = "is scheduled, but the prior work does not have dates yet"
SCHEDULE_KEEP = "Leave dates as they are"
SCHEDULE_MOVE = "Change dates"
SCHEDULE_REVIEW = "Review this project"
SCHEDULE_WARNING_HELP = "This is information only. You can continue without changing anything."
FIELD_NAV_TODAY = "Today"
FIELD_NAV_WEEK = "This week"
FIELD_NAV_MONTH = "This month"
FIELD_COMPANY_TODAY = "Company today"
FIELD_MY_WORK = "My work"
FIELD_ASSIGNED_TO_ME = "Assigned to me"
FIELD_CREW_WORK = "Crew work"
FIELD_NOT_ASSIGNED = "Not assigned"
FIELD_YOU_ALREADY_ELSEWHERE = "You are already scheduled elsewhere"
FIELD_NO_WORK_TODAY = "Nothing is scheduled for you today."
FIELD_NO_COMPANY_TODAY = "Nothing is scheduled today."
FIELD_NO_WORK_WEEK = "Nothing is scheduled for you this week."
FIELD_NO_WORK_MONTH = "Nothing is scheduled for you this month."
FIELD_NO_WORK_DAY = "No scheduled work for this day."
FIELD_DIRECTIONS = "Directions"
FIELD_MONTH_PREV = "Previous month"
FIELD_MONTH_NEXT = "Next month"
FIELD_ENTER_TIME = "Enter time"
FIELD_SCHEDULED_TODAY = "Scheduled today"
FIELD_SCHEDULE_SUGGEST_HELP = "You can use this scheduled work, or choose other work."
FIELD_WORKING_ELSEWHERE = "Working somewhere else?"
FIELD_CHOOSE_DIFFERENT_WORK = "Choose different work"
FIELD_TWO_JOBS_HELP = "Choose the work you actually did."
FIELD_SCHEDULE_WARNING_HELP = "This is information only. You can keep working."
FIELD_COMPANY_TODAY_HELP = "What the company has scheduled today. This does not change dates."
COSTING_REVIEW_HEADING = "Costing review"
APPROVE_ALL_COSTING_BUTTON = "Approve all costing"
COSTING_NOT_APPROVED = "Costing is not approved yet."
PRICING_NEEDS_APPROVED_COSTING = "Apply pricing after costing is approved."
PRICING_STALE_REQUIRES_REAPPLY = "STALE / REQUIRES RE-APPLY"
WORKING_COSTING_CHANGED = (
    "Working costs changed. Approve all costing again before applying pricing."
)
LOGIN_LEDE = "Sign in with your email and password."
FORGOT_PASSWORD_LINK = "Forgot Password?"
FORGOT_PASSWORD_HEADING = "Forgot Password"
FORGOT_PASSWORD_INSTRUCTION = (
    "Enter your email address and we will send password reset instructions."
)
FORGOT_PASSWORD_SUBMIT = "Send Reset Instructions"
FORGOT_PASSWORD_SENT_HEADING = "Check your email"
FORGOT_PASSWORD_SENT_BODY = (
    "If an account exists for that email address, password reset instructions "
    "have been sent."
)
RESET_PASSWORD_HEADING = "Set New Password"
RESET_PASSWORD_SUBMIT = "Reset Password"
RESET_PASSWORD_NEW_LABEL = "New Password"
RESET_PASSWORD_CONFIRM_LABEL = "Confirm New Password"
RESET_PASSWORD_SUCCESS_HEADING = "Password Updated"
RESET_PASSWORD_SUCCESS_BODY = "Your password has been reset."
RESET_PASSWORD_INVALID_HEADING = "Reset link unavailable"
RESET_PASSWORD_INVALID_BODY = (
    "This password reset link is invalid or has expired. "
    "Request a new password reset link."
)
REQUEST_ANOTHER_RESET = "Request Another Reset"
BACK_TO_SIGN_IN = "Back to Sign In"
RETURN_TO_SIGN_IN = "Return to Sign In"
EMAIL_CAPTURED_FOR_TESTING = "Email captured for testing"
EMAIL_ACCEPTED_FOR_DELIVERY = "Email accepted for delivery"
EMAIL_NOT_SENT = "Email not sent"
EMAIL_CONFIGURATION_MISSING = "Email configuration missing"
SIGNING_INVITATION_ISSUED = "Invitation issued"
SIGNING_LINK_COPY_HINT = "Copy the signing link if you need it."
SIGNING_REVIEW_AND_SIGN = "Review & Sign"
SIGNING_CURRENT_LINK = "Use this current signing link to review and sign."
SIGNING_COMPLETE_CUSTOMER_BODY = (
    "Signing is complete. Contact the office if you need a copy of the "
    "completed document."
)
SIGN_OUT_LABEL = "Sign out"
DASHBOARD_HEADING = "Home"
DASHBOARD_LEDE = "Open a project, start an estimate, or issue a proposal."
HOME_START_PROJECT = "+ Start New Project"
PROJECTS_LEDE = "Your current and completed work."
PROJECTS_OPEN = "Open"
HOME_PULSE_PROJECTS = "Current projects"
HOME_PULSE_ESTIMATES = "Estimates outstanding"
HOME_PULSE_PROPOSALS = "Proposals outstanding"
HOME_PULSE_CHANGE_ORDERS = "Open change orders"
HOME_PULSE_ATTENTION = "Need attention"
HOME_DAY_HEADING = "Day"
HOME_NO_SCHEDULED_WORK = "No scheduled work occupying this day."
HOME_NO_UNSCHEDULED = "No authorized work is waiting for dates."
HOME_CALENDAR_EMPTY = "Nothing is scheduled this month."
HOME_OVERFLOW_MORE = "more"
BRAND_PROFILE_HEADING = "Brand profile"
BRAND_PROFILE_LEDE = (
    "Company identity and logo for documents you send to customers. "
    "Saving creates a new current version. Issued and Accepted proposals "
    "keep the branding they were issued with."
)
FIELD_SAVE_ORIGINAL = "Save original"
FIELD_NOTES_LABEL = "Notes"
FIELD_CHANGE_PROJECT = "Change project"
FIELD_CONFIRM_BEFORE_CAPTURE = "Confirm the project before capturing."
FIELD_NO_PROJECTS = "No projects are available."
FIELD_RETRY_HEADING = "Not sent yet"
FIELD_RETRY_LINK = "Try sending again"
FIELD_RETRY_ONE = "1 capture did not send."
FIELD_RETRY_MANY_SUFFIX = " captures did not send."
FIELD_SAVED = "Saved"
FIELD_SAVING = "Saving…"
FIELD_NEEDS_RETRY = "Could not send"
FIELD_EVENT_SAVE_FAILED = "This observation could not be saved."
FIELD_ORIGINAL_SAVE_FAILED = (
    "The original photo or file could not be saved."
)
FIELD_CAPTURE_START_FAILED = (
    "This phone could not start a capture. Try again."
)
FIELD_ADD_BEFORE_SAVE = (
    "Add a photo, recording, or note before saving."
)
FIELD_LOGOUT_CONFIRM = (
    "Unsent captures will be removed from this phone. Sign out?"
)
FIELD_OTHER_PROJECT_PENDING = (
    "A capture is still waiting on another project. "
    "Open that project to send it, or discard it?"
)
FIELD_DISCARD_OTHER_PENDING = (
    "Discard the waiting capture for the other project?"
)
SOURCE_NOTES_LABEL = "Source notes"
PRICING_LOCK_HEADING = "Pricing lock"
CATALOGUE_COLUMN_LABEL = "Catalogue"

PRICING_METHOD_LABELS = {
    "TRUE_GROSS_MARGIN": "Gross Margin Pricing",
    "COST_PLUS_MARKUP": "Cost plus markup",
    "COST_PLUS_MARKUP_STACK": "Cost plus markup (legacy stack)",
}

NO_PRICING_LOCK = (
    "No pricing lock. This version uses the live "
    f"{PRICING_METHOD_LABELS['COST_PLUS_MARKUP_STACK']} "
    "calculation. Totals are not backfilled to Gross Margin Pricing."
)

OFFICE_STATUS_LABELS = {
    "DRAFT": "Draft",
    "ORG_APPROVED": "Organization approved",
    "ORG-APPROVED": "Organization approved",
    "ORG_APPROVED_ACTIVE": "Organization approved (active)",
    "SUPERSEDED": "Superseded",
    "RECEIVED": "Received",
    "SELECTED": "Selected",
    "SUBCONTRACT_QUOTE_AMOUNT_DIFFERS": "Quoted amount differs from working cost",
    "WITHDRAWN": "Withdrawn",
    "ACTIVE": "Active",
    "INACTIVE": "Inactive",
    "ARCHIVED": "Archived",
    "APPROVED": "Approved",
    "DISCONTINUED": "Discontinued",
    "GENERIC": "Generic",
    "SPECIFIED": "Specified",
    "ALLOWED": "Allowed",
    "RESTRICTED": "Restricted",
    "PROHIBITED": "Prohibited",
    "NOT_LABOUR": "Not labour",
    "SUGGESTED": "Suggested",
    "ACCEPTED": "Accepted",
    "REJECTED": "Rejected",
    "REVOKED": "Revoked",
    "PROPOSED": "Proposed",
    "IN_REVIEW": "In review",
    "CURRENT": "Current",
    "MANUAL": "Manual",
    "BASELINE": "Baseline",
    "PROVISIONAL": "Provisional",
    "ORG-ACTUAL": "Organization actual",
    "ORG-HISTORICAL": "Organization historical",
    "PRODUCTION_RATE": "Production rate",
    "DIRECT_LABOUR_COST_RATE": "Direct labour cost rate",
    "MAPPED_FROM_HISTORICAL": "Mapped from historical",
    "BASELINE_CLONE": "Baseline clone",
    "UNSPECIFIED": "Not specified",
    "NOT_APPLIED": "Not applied",
    "DIRECT_PROJECT_COST": "Direct project cost",
    "INCLUDED_IN_MARGIN_ECONOMICS": "Included in margin economics",
    "SEPARATELY_CUSTOMER_PRICED": "Separately customer-priced",
    "INTERNAL_RESERVE": "Internal reserve",
    "CUSTOMER_PRICED": "Customer-priced",
    "INCLUDED_IN_MARGIN_BASIS": "Included in margin basis",
    "ADDED_AFTER_BASE_PRICING": "Added after base pricing",
    "ESTIMATE_OVERRIDE": "Estimate override",
    "COMMERCIAL_CONTEXT": "Pricing assumptions",
    "ORGANIZATION_DEFAULT": "Organization default",
    "CALIBAI_BASELINE": "Platform baseline",
    "PROVISIONAL_LEGACY_STACK": "Provisional legacy stack",
    "HUMAN": "Human",
    "AI": "AI",
    "RULE": "Rule",
    "CONFIRMED": "Confirmed",
    "UNRESOLVED": "Not decided yet",
    "NONE": "None",
    "ORG_DEFAULT": "Organization default",
}


SCOPE_MATERIAL_LABELS = {
    "CONTRACTOR_PURCHASED": "We purchase the material",
    "SUBCONTRACTOR_SUPPLIED": "Subcontractor supplies it",
    "OWNER_SUPPLIED": "Owner supplies it",
    "NO_MATERIAL": "No material",
    "UNRESOLVED": "Not decided yet",
}

SCOPE_LABOUR_LABELS = {
    "INTERNAL": "Our crew",
    "SUBCONTRACT": "Subcontractor",
    "OWNER_THIRD_PARTY": "Owner's third party",
    "NO_LABOUR": "No labour",
    "UNRESOLVED": "Not decided yet",
}


def scope_material_label(value: str | None) -> str:
    if not value:
        return ""
    return SCOPE_MATERIAL_LABELS.get(value) or office_status_label(value)


def scope_labour_label(value: str | None) -> str:
    if not value:
        return ""
    return SCOPE_LABOUR_LABELS.get(value) or office_status_label(value)


def pricing_method_label(method: str | None) -> str:
    if not method:
        return ""
    mapped = PRICING_METHOD_LABELS.get(method)
    if mapped:
        return mapped
    return office_status_label(method)


def historical_family_label(family: str | None) -> str:
    if not family:
        return ""
    return HISTORICAL_FAMILY_LABELS.get(family, family.replace("FAMILY_", "Workbook "))


def historical_upload_outcome_label(outcome: str | None) -> str:
    if not outcome:
        return ""
    return HISTORICAL_UPLOAD_OUTCOME_LABELS.get(outcome, office_status_label(outcome))


def permit_office_language(text: str | None) -> str:
    """Replace internal AHJ wording in contractor-facing permit copy."""
    if not text:
        return ""
    result = text
    for old, new in (
        ("authority having jurisdiction (AHJ)", "municipality or permit office"),
        ("The authority having jurisdiction", "The municipality or permit office"),
        ("the authority having jurisdiction", "the municipality or permit office"),
        ("the AHJ", "the municipality or permit office"),
        ("AHJ", "the municipality or permit office"),
    ):
        result = result.replace(old, new)
    return result


CUSTOMER_DOCUMENT_TITLE = "CONSTRUCTION ESTIMATE"
CUSTOMER_PRICING_HEADING = "Pricing"
CUSTOMER_NO_PRICING_SECTIONS = "No priced items on this construction estimate."
CUSTOMER_CLIENT_LABEL = "Customer"
CUSTOMER_PROJECT_LABEL = "Project"

CONTRACT_STATUS_HEADING = "Production contract"
CONTRACT_PRODUCTION_UNAVAILABLE = "Production contract unavailable"
CONTRACT_PRODUCTION_AVAILABLE = "Production contract package available"
CONTRACT_NO_ACTIVE_PACKAGE = (
    "No active counsel-approved contract package is available for this jurisdiction."
)
CONTRACT_LOCATION_INCOMPLETE = (
    "Project location is not complete, so a production contract cannot be generated."
)
CONTRACT_PACKAGE_NOT_USABLE = (
    "The selected package cannot be used for production contract generation."
)
CONTRACT_STATUS_UNDETERMINED = (
    "Production contract status could not be determined. Contract generation is blocked."
)
CONTRACT_GENERATION_BLOCKED = (
    "Contract generation is blocked until approved legal content is activated."
)
CONTRACT_ACTIVE_PACKAGE_SELECTED = (
    "An active counsel-approved package is selected for this jurisdiction."
)
CONTRACT_PENDING_UPDATE_WARN = (
    "An approved active contract package is available and remains the current "
    "authority, but an update is pending legal review."
)
CONTRACT_ACTIVE_REMAINS_AUTHORITY = (
    "The current approved package remains in force. A pending update is not "
    "used as contract authority."
)
CONTRACT_GENERATION_NOT_FROM_HUB = (
    "Production generation is not started from this screen."
)
CONTRACT_SAFEGUARD = (
    "This is a legal-content safeguard. The estimate and proposal are not broken."
)
CONTRACT_NO_PRODUCTION_GENERATED = "No production contract has been generated."
CONTRACT_NO_FAMILY_05_FALLBACK = (
    "A commercial presentation draft is not used as a substitute contract."
)
CONTRACT_NO_BYPASS = "This screen does not override the legal-content gate."
CONTRACT_OFFICE_DETAIL_LABEL = "Office detail"

CONTRACT_BLOCK_LEDES = {
    "JURISDICTION_NOT_SUPPORTED": CONTRACT_NO_ACTIVE_PACKAGE,
    "NO_ACTIVE_PACKAGE": CONTRACT_NO_ACTIVE_PACKAGE,
    "PACKAGE_NOT_ACTIVE": CONTRACT_NO_ACTIVE_PACKAGE,
    "PACKAGE_SUPERSEDED_NO_ACTIVE_REPLACEMENT": CONTRACT_NO_ACTIVE_PACKAGE,
    "JURISDICTION_UNRESOLVED": CONTRACT_LOCATION_INCOMPLETE,
    "PACKAGE_NOT_EFFECTIVE": CONTRACT_PACKAGE_NOT_USABLE,
    "EFFECTIVE_DATE_UNRESOLVED": CONTRACT_PACKAGE_NOT_USABLE,
    "COVERAGE_LIMITED": CONTRACT_PACKAGE_NOT_USABLE,
}


def contract_selection_copy(selection) -> dict:
    """Map a Slice A LegalContentSelection to office CONTRACT copy.

    Presentation only. Does not resolve jurisdiction or select packages.
    """
    if selection is None or getattr(selection, "selection_error", False):
        return {
            "blocked": True,
            "warned": False,
            "heading": CONTRACT_PRODUCTION_UNAVAILABLE,
            "lede": CONTRACT_STATUS_UNDETERMINED,
            "next": CONTRACT_GENERATION_BLOCKED,
            "block_code": None,
            "warn_code": None,
            "jurisdiction_code": None,
        }
    if getattr(selection, "available", False):
        status = getattr(selection, "status", None)
        warn_code = getattr(selection, "warn_code", None)
        if status == "WARN" or warn_code:
            return {
                "blocked": False,
                "warned": True,
                "heading": CONTRACT_PRODUCTION_AVAILABLE,
                "lede": CONTRACT_PENDING_UPDATE_WARN,
                "next": CONTRACT_ACTIVE_REMAINS_AUTHORITY,
                "block_code": None,
                "warn_code": warn_code or "PENDING_CANDIDATE",
                "jurisdiction_code": getattr(selection, "jurisdiction_code", None),
            }
        return {
            "blocked": False,
            "warned": False,
            "heading": CONTRACT_PRODUCTION_AVAILABLE,
            "lede": CONTRACT_ACTIVE_PACKAGE_SELECTED,
            "next": CONTRACT_GENERATION_NOT_FROM_HUB,
            "block_code": None,
            "warn_code": None,
            "jurisdiction_code": getattr(selection, "jurisdiction_code", None),
        }
    code = getattr(selection, "block_code", None)
    return {
        "blocked": True,
        "warned": False,
        "heading": CONTRACT_PRODUCTION_UNAVAILABLE,
        "lede": CONTRACT_BLOCK_LEDES.get(code, CONTRACT_NO_ACTIVE_PACKAGE),
        "next": CONTRACT_GENERATION_BLOCKED,
        "block_code": code,
        "warn_code": None,
        "jurisdiction_code": getattr(selection, "jurisdiction_code", None),
    }


def office_status_label(value: str | None) -> str:
    if not value:
        return ""
    mapped = OFFICE_STATUS_LABELS.get(value)
    if mapped:
        return mapped
    mapped_method = PRICING_METHOD_LABELS.get(value)
    if mapped_method:
        return mapped_method
    text = sentence_label(value)
    if text.isupper():
        if " " not in text:
            return text.capitalize()
        return text.title()
    return text
