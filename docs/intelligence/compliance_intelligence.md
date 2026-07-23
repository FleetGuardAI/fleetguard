# Vehicle Compliance Intelligence Domain

## Overview
The Vehicle Compliance Intelligence domain evaluates whether a vehicle and its assigned driver satisfy all required regulatory and operational compliance requirements. It ensures that critical documentation like registrations, insurances, fitness certificates, pollution certificates, permits, and driver licenses are valid and active.

This domain operates purely deterministically, evaluating factual observations directly into a compliance risk assessment. It forms part of the 5-Tier Intelligence Architecture and operates independently of other domains.

## 1. Evidence
The Compliance domain consumes the following immutable evidence types:
- `VehicleRegistrationEvidence`: Factual details of the vehicle's registration.
- `InsuranceEvidence`: Factual details of the insurance policy.
- `FitnessCertificateEvidence`: Factual details of the vehicle's fitness certification.
- `PollutionCertificateEvidence`: Factual details of the vehicle's pollution certificate.
- `PermitEvidence`: Factual details of the vehicle's operational permits.
- `DriverLicenseEvidence`: Factual details of the driver's license.

These models strictly contain observations (issue/expiry dates, document numbers, issuing authorities). They *do not* contain computed states like `is_expired`.

## 2. Configuration
The domain behavior is controlled by `ComplianceIntelligenceConfig`:
- `expiry_warning_days` (default 30): The threshold to flag impending expiries.
- `critical_expiry_days` (default 7): Additional severity threshold (unused in basic compliance, but available).
- `required_document_categories`: List of standard expected document types.
- `mandatory_permit_types`: Required permit categories (e.g., `NATIONAL`, `STATE`).
- `required_driver_license_classes`: Allowed license classes (e.g., `COMMERCIAL`, `HEAVY`).

## 3. Checks
Checks are stateless and deterministic, evaluating expiry dates and exact matches against the configuration.
- **RegistrationValidityCheck** (`compliance.registration_validity`)
- **InsuranceValidityCheck** (`compliance.insurance_validity`)
- **FitnessCertificateCheck** (`compliance.fitness_validity`)
- **PollutionCertificateCheck** (`compliance.pollution_validity`)
- **PermitValidityCheck** (`compliance.permit_validity`): Also verifies the presence of all `mandatory_permit_types`.
- **DriverLicenseValidityCheck** (`compliance.driver_license_validity`): Verifies the category matches `required_driver_license_classes`.

## 4. Assessments
- **VehicleComplianceAssessment** (`compliance.vehicle_assessment`): Consumes all Check results. Generates specific findings for any document that is missing, expired, or invalid. Warning findings are generated for documents expiring within the `expiry_warning_days`.

## 5. Domain Risk
- **VehicleComplianceRiskEngine** (`compliance.vehicle_risk`):
  - **CRITICAL**: If any actual expired documents, missing mandatory permits, or invalid classes are found.
  - **MEDIUM**: If only warnings (documents expiring soon) are found.
  - **LOW**: If all documents are perfectly compliant and not expiring soon.

## 6. Decision Engine
- **VehicleComplianceDecisionEngine** (`compliance.vehicle_decision`): Translates the compliance risk into operational policy.
  - LOW risk -> **APPROVE**
  - MEDIUM risk -> **APPROVE_WITH_REVIEW**
  - HIGH risk -> **REVIEW_REQUIRED**
  - CRITICAL risk -> **REJECT**

## Extension Guide
If an organization requires new document types (e.g., specialized HAZMAT permits):
1. Create a new model inheriting `BaseEvidence` (e.g., `HazmatPermitEvidence`).
2. Implement a stateless `HazmatPermitValidityCheck`.
3. Update `VehicleComplianceAssessment` to consume the new check.
4. The Risk and Decision engines require no changes, as they respond automatically to the Assessment findings.
