from app.models.assembly import Assembly, AssemblyItem
from app.models.client import Client
from app.models.canonical_material import CanonicalMaterial
from app.models.material_requirement import MaterialRequirement
from app.models.supplier_catalogue import (
    CanonicalMaterialSupplierMap,
    ContractorSupplierAccount,
    Supplier,
    SupplierLocation,
    SupplierPackage,
    SupplierPackageLine,
    SupplierProduct,
    SupplierProductAvailabilityEvidence,
    SupplierProductPriceEvidence,
    SupplierRequirementMap,
)
from app.models.cost_item import CostItem
from app.models.jurisdiction import JurisdictionAlias, JurisdictionDefinition
from app.models.legal_content import (
    LegalContentActivationEvent,
    LegalContentCandidateChange,
    LegalContentCandidateImpact,
    LegalContentJurisdictionPackage,
    LegalContentObject,
    LegalContentReviewEvent,
    LegalContentSource,
    LegalContentSourceSnapshot,
)
from app.models.project_contract import (
    GeneratedProjectContract,
    ProjectContractSnapshot,
    ProjectContractSnapshotObject,
)
from app.models.signing import (
    SigningConsentVersion,
    SigningEvent,
    SigningExecutedArtifact,
    SigningFrozenArtifact,
    SigningParticipant,
    SigningRequest,
    SigningTokenAccessAttempt,
)
from app.models.permit_intelligence import (
    PermitAnalysis,
    PermitFinding,
    PermitRule,
    ProjectPermitFact,
)
from app.models.project import (
    PermitProfile,
    Project,
    ProjectCommercialContext,
    ProjectIdentityEvent,
    ProjectLocation,
    ProjectNumberSequence,
    ProjectOperatingStateEvent,
)
from app.models.punch_list import ProjectPunchListItem, ProjectPunchListItemEvent
from app.models.final_walkthrough import (
    ProjectFinalWalkthroughAccessAttempt,
    ProjectFinalWalkthroughInvitation,
    ProjectFinalWalkthroughItem,
)
from app.models.estimate import (
    Estimate,
    EstimateLineItem,
    EstimateSection,
    EstimateVersion,
)
from app.models.estimate_costing import (
    EstimateCostingSnapshot,
    EstimateCostingSnapshotLine,
)
from app.models.contractor_cost_approval import ContractorCostApproval
from app.models.estimate_quickbooks import (
    EstimateQuickBooksCostClassLine,
    EstimateQuickBooksEntryEvent,
    EstimateQuickBooksEntryOccupancy,
    EstimateQuickBooksPackage,
    EstimateQuickBooksSalesLine,
)
from app.models.estimate_scope_delivery import EstimateScopeDelivery
from app.models.subcontractor import Subcontractor, SubcontractQuoteEvidence
from app.models.organization import (
    Organization,
    OrganizationInstanceOwnerEvent,
    OrganizationSystemAdministratorEvent,
    OrganizationSystemAdministratorMembership,
)
from app.models.person import OrganizationPerson, OrganizationPersonWageEvent
from app.models.people_access_event import PeopleAccessEvent
from app.models.user import User, UserMembership, UserMembershipAccessDomainGrant
from app.models.password_reset import PasswordResetAccessAttempt, PasswordResetToken
from app.models.transactional_message import TransactionalMessage
from app.models.email_delivery import TransactionalDeliveryEvent  # sign-in reliability (26 Oct 2026)
from app.models.brand_profile import OrganizationBrandProfile, ProposalBrandSnapshot
from app.models.build import (
    FieldCaptureDerivedCandidate,
    FieldCaptureEvent,
    FieldCaptureOriginal,
)
from app.models.direct_cost_actual import ProjectDirectCostActual
from app.models.takeoff_estimate_insertion import (
    TakeoffEstimateInsertion,
    TakeoffEstimateInsertionCitation,
)
from app.models.calculation_estimate_mapping import (
    CalculationMappingAcceptance,
    CalculationQuantityReview,
    CalculationResultIntake,
)
from app.models.proposal import Proposal, ProposalLineItem, ProposalSection, ProposalTemplate
from app.models.proposal_acceptance import ProposalAcceptance, ProposalClientLink, ProposalDecline
from app.models.accounting import AccountingEvent, AccountingExportRecord, CustomerInvoice
from app.models.supplier_portal import (
    ConcreteRequest,
    NotificationContact,
    TextMessage,
    SupplierBrandProfile,
    SupplierDeliveryChange,
    SupplierNotificationNumber,
    SupplierPurchaseOrder,
    SupplierRequestEvent,
    SupplierRequestShare,
    SupplierUserMembership,
)
from app.models.sms_notification import (  # SMS schedule-change notices (22 Oct 2026)
    SmsConsentEvent,
    SmsDeliveryEvent,
    SmsScheduleNotice,
    SmsTextMessageDetail,
)
from app.models.pricing_engine import (
    EstimatePricingSnapshot,
    OrganizationPricingPolicy,
    PricingAuditEvent,
)
from app.models.labour_engine import (
    DirectLabourCostRateStandard,
    EstimateLabourSnapshot,
    LabourAuditEvent,
    LabourCalibrationCandidate,
    LabourTask,
    LabourTaskMapping,
    ProductionRateStandard,
)
from app.models.project_work_package import ProjectWorkPackage
from app.models.estimate_approval import EstimateApproval
from app.models.plan_generation_candidate import PlanGenerationCandidate
from app.models.project_construction_model import ProjectConstructionModelRevision
from app.models.construction_drawing import ConstructionDrawingAttachment, ConstructionDrawingSet
from app.models.work_structure import (
    ProjectWorkActivity,
    ProjectWorkElement,
    ProjectWorkScopeDelta,
    ProjectWorkScopeHistory,
    ProjectWorkStructureSeed,
    WorkActivityTemplate,
    WorkElementTemplate,
    WorkType,
)
from app.models.time_entry import LabourTimeEntry, LabourTimeHistory
from app.models.organization_crew import OrganizationCrew, OrganizationCrewMember
from app.models.onboarding import OrganizationOnboardingStep
from app.models.payroll_time import (  # noqa: F401  approved time to QuickBooks Time, banked hours (22 Oct 2026)
    BankedHoursLedgerEntry,
    BankedHoursPolicy,
    QuickBooksTimeEmployeeLink,
    QuickBooksTimeEvent,
    QuickBooksTimeJobcodeLink,
    QuickBooksTimeTransfer,
)
from app.models.training import TrainingFeedback, TrainingLessonProgress, TrainingTrainee, TrainingUatResult
from app.models.project_calculation import ProjectCalculation
from app.models.guided_estimating import (
    CalculatorResultCarry,
    GuidedEstimate,
    GuidedEstimateEvent,
    GuidedEstimateStage,
)
from app.models.wizard import WizardRun, WizardRunEvent
from app.models.field_operations import (  # the Magnificent Seven everyday operations (25 Oct 2026)
    AccountingProjectLink,
    DailyJobSummary,
    DeliveryConfirmation,
    ExtraWorkReport,
    FieldMaterialRequest,
    FieldOperationEvent,
    FieldReceipt,
    OperationsReminder,
    OperationsSettings,
    QuickBooksOnlineConnection,
    QuickBooksOnlineEvent,
    QuickBooksOnlineLink,
    QuickBooksOnlineTransfer,
    ReminderPreference,
)
from app.models.appointment import (
    CalendarFeedKey,
    CompanyAppointment,
    CompanyAppointmentAttendee,
    CompanyAppointmentHistory,
)
from app.models.supplier_quote import (
    SupplierCustomer,
    SupplierPriceImport,
    SupplierQuote,
    SupplierQuoteEvent,
    SupplierQuoteFile,
    SupplierQuoteLink,
    SupplierQuoteSettings,
    SupplierBuildingAssembly,
    SupplierSellingPrice,
)
from app.models.schedule import (
    ProjectWorkDependency,
    WorkScheduleAssignment,
    WorkScheduleHistory,
    WorkScheduleItem,
)
from app.models.historical_estimates import (
    HistoricalCostLineItem,
    HistoricalDataQualityFlag,
    HistoricalEstimate,
    HistoricalEstimateReviewDecision,
    HistoricalLabourItem,
    HistoricalSourceObservation,
    HistoricalSourceWorkbook,
    HistoricalSubcontractItem,
    HistoricalUploadAttempt,
)
from app.project_controls.models import ChangeOrder, ChangeOrderItem
from app.plan_intelligence.models import (
    DrawingPackage,
    DrawingRevision,
    PlanAuditEvent,
    PlanDocument,
    PlanPage,
    ProcessingAttempt,
    ProcessingResult,
    TakeoffCandidate,
    TakeoffExtractionRun,
    TakeoffPackage,
    TakeoffPackageItem,
)

__all__ = [
    "ProjectCalculation",
    "GuidedEstimate",
    "GuidedEstimateStage",
    "WizardRun",
    "WizardRunEvent",
    "GuidedEstimateEvent",
    "CalculatorResultCarry",
    "ConcreteRequest",
    "NotificationContact",
    "TextMessage",
    "SmsConsentEvent",
    "SmsDeliveryEvent",
    "SmsScheduleNotice",
    "SmsTextMessageDetail",
    "SupplierBrandProfile",
    "SupplierDeliveryChange",
    "SupplierNotificationNumber",
    "SupplierPurchaseOrder",
    "SupplierRequestEvent",
    "SupplierRequestShare",
    "SupplierUserMembership",
    "ProposalAcceptance",
    "ProposalDecline",
    "AccountingEvent",
    "AccountingExportRecord",
    "CustomerInvoice",
    "ProposalClientLink",
    "Assembly",
    "AssemblyItem",
    "ChangeOrder",
    "CanonicalMaterial",
    "CanonicalMaterialSupplierMap",
    "ContractorSupplierAccount",
    "MaterialRequirement",
    "Supplier",
    "SupplierLocation",
    "SupplierPackage",
    "SupplierPackageLine",
    "SupplierProduct",
    "SupplierProductAvailabilityEvidence",
    "SupplierProductPriceEvidence",
    "SupplierRequirementMap",
    "ChangeOrderItem",
    "Client",
    "CostItem",
    "DrawingPackage",
    "DrawingRevision",
    "Estimate",
    "EstimateCostingSnapshot",
    "EstimateCostingSnapshotLine",
    "EstimateQuickBooksCostClassLine",
    "EstimateQuickBooksEntryEvent",
    "EstimateQuickBooksEntryOccupancy",
    "EstimateQuickBooksPackage",
    "EstimateQuickBooksSalesLine",
    "EstimateScopeDelivery",
    "Subcontractor",
    "SubcontractQuoteEvidence",
    "FieldCaptureDerivedCandidate",
    "FieldCaptureEvent",
    "FieldCaptureOriginal",
    "ProjectDirectCostActual",
    "EstimateLineItem",
    "EstimatePricingSnapshot",
    "EstimateSection",
    "EstimateVersion",
    "HistoricalCostLineItem",
    "HistoricalDataQualityFlag",
    "HistoricalEstimate",
    "HistoricalEstimateReviewDecision",
    "HistoricalLabourItem",
    "HistoricalSourceObservation",
    "HistoricalSourceWorkbook",
    "HistoricalSubcontractItem",
    "HistoricalUploadAttempt",
    "JurisdictionAlias",
    "JurisdictionDefinition",
    "LegalContentActivationEvent",
    "LegalContentCandidateChange",
    "LegalContentCandidateImpact",
    "LegalContentJurisdictionPackage",
    "LegalContentObject",
    "LegalContentReviewEvent",
    "LegalContentSource",
    "LegalContentSourceSnapshot",
    "GeneratedProjectContract",
    "ProjectContractSnapshot",
    "ProjectContractSnapshotObject",
    "SigningConsentVersion",
    "SigningEvent",
    "SigningFrozenArtifact",
    "SigningParticipant",
    "SigningRequest",
    "SigningTokenAccessAttempt",
    "DirectLabourCostRateStandard",
    "EstimateLabourSnapshot",
    "LabourAuditEvent",
    "LabourCalibrationCandidate",
    "LabourTask",
    "LabourTaskMapping",
    "ProductionRateStandard",
    "ProjectWorkPackage",
    "EstimateApproval",
    "ProjectWorkActivity",
    "ProjectWorkElement",
    "ProjectWorkScopeDelta",
    "ProjectWorkScopeHistory",
    "ProjectWorkStructureSeed",
    "WorkActivityTemplate",
    "WorkElementTemplate",
    "WorkType",
    "LabourTimeEntry",
    "LabourTimeHistory",
    "Organization",
    "OrganizationInstanceOwnerEvent",
    "OrganizationSystemAdministratorEvent",
    "OrganizationSystemAdministratorMembership",
    "User",
    "UserMembership",
    "UserMembershipAccessDomainGrant",
    "PasswordResetAccessAttempt",
    "PasswordResetToken",
    "TransactionalMessage",
    "OrganizationBrandProfile",
    "OrganizationPricingPolicy",
    "ProposalBrandSnapshot",
    "PricingAuditEvent",
    "PlanAuditEvent",
    "PlanDocument",
    "PlanGenerationCandidate",
    "ProjectConstructionModelRevision",
    "PlanPage",
    "ProcessingAttempt",
    "ProcessingResult",
    "TakeoffCandidate",
    "TakeoffExtractionRun",
    "TakeoffPackage",
    "TakeoffPackageItem",
    "TakeoffEstimateInsertion",
    "TakeoffEstimateInsertionCitation",
    "PermitAnalysis",
    "PermitFinding",
    "PermitProfile",
    "PermitRule",
    "ProjectPermitFact",
    "OrganizationCrew",
    "OrganizationOnboardingStep",
    "OrganizationCrewMember",
    "OrganizationPerson",
    "OrganizationPersonWageEvent",
    "PeopleAccessEvent",
    "Project",
    "ProjectCommercialContext",
    "ProjectLocation",
    "ProjectOperatingStateEvent",
    "ProjectIdentityEvent",
    "ProjectNumberSequence",
    "ProjectFinalWalkthroughAccessAttempt",
    "ProjectFinalWalkthroughInvitation",
    "ProjectFinalWalkthroughItem",
    "ProjectPunchListItem",
    "ProjectPunchListItemEvent",
    "ProjectWorkDependency",
    "CalendarFeedKey",
    "CompanyAppointment",
    "CompanyAppointmentAttendee",
    "CompanyAppointmentHistory",
    "SupplierCustomer",
    "SupplierPriceImport",
    "SupplierQuote",
    "SupplierQuoteEvent",
    "SupplierQuoteFile",
    "SupplierQuoteLink",
    "SupplierQuoteSettings",
    "SupplierBuildingAssembly",
    "SupplierSellingPrice",
    "WorkScheduleAssignment",
    "WorkScheduleHistory",
    "WorkScheduleItem",
    "Proposal",
    "ProposalLineItem",
    "ProposalSection",
    "ProposalTemplate",
]
