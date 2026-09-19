#!/usr/bin/env python3
"""Generate universal multi-domain synthetic documents, entities, cases, and golden eval sets.

Deterministic seeded generation ensures 100% reproducibility across environments.
Supports universal multi-format documents: TXT, MD, JSON, CSV, PDF, and DOCX.
"""
from __future__ import annotations

import csv
import json
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

SEED = 42
random.seed(SEED)

DATA_DIR = ROOT / "data"
SAMPLE_DOCS_DIR = DATA_DIR / "sample_docs"
SYNTHETIC_DIR = DATA_DIR / "synthetic"
GOLDEN_DIR = DATA_DIR / "golden"


def create_directories() -> None:
    for d in [SAMPLE_DOCS_DIR, SYNTHETIC_DIR, GOLDEN_DIR, DATA_DIR / "storage"]:
        d.mkdir(parents=True, exist_ok=True)


def generate_vendor_contract_txt() -> Path:
    p = SAMPLE_DOCS_DIR / "vendor_contract.txt"
    content = """# MASTER SERVICES AGREEMENT: CLOUDSCALE TECHNOLOGIES & ACME CORP
Contract ID: MSA-2024-8891
Effective Date: January 1, 2024
Term: 36 Months

SECTION 1: SCOPE OF SERVICES
CloudScale Technologies ('Vendor') agrees to provide enterprise multi-region cloud infrastructure, data warehousing, and 24/7 technical support to Acme Corp ('Customer').

SECTION 2: SERVICE LEVEL AGREEMENT (SLA) & UPTIME GUARANTEE
2.1 Vendor guarantees a monthly service availability of 99.95% for all core production APIs and databases.
2.2 If availability drops between 99.0% and 99.95%, Customer is entitled to a 10% service credit on monthly billing.
2.3 If availability drops below 99.0%, Customer is entitled to a 25% service credit.
2.4 Critical incident response time: Vendor shall acknowledge and begin remediation on Severity-1 tickets within 15 minutes of notification.

SECTION 3: PAYMENT TERMS & BILLING DISPUTES
3.1 Invoices are issued monthly in arrears with Net-30 payment terms.
3.2 Any invoice dispute must be submitted in writing within 45 days of invoice date. Undisputed amounts must be paid according to schedule.
3.3 Late payments are subject to a 1.5% interest charge per month or the legal maximum.

SECTION 4: TERMINATION & BREACH OF CONTRACT
4.1 Either party may terminate this agreement for cause upon 30 days written notice if a material breach remains uncured.
4.2 Termination for convenience requires 90 days prior written notice and payment of prorated unamortized equipment fees.
4.3 In the event of breach of confidentiality or data protection obligations, termination is immediate without penalty.

SECTION 5: DATA PROTECTION & CONFIDENTIALITY
5.1 Both parties agree to maintain strict confidentiality of proprietary data, customer records, and system architectures.
5.2 Data stored on Vendor infrastructure remains the sole property of Customer and must be exported within 30 days upon termination.
"""
    p.write_text(content.strip(), encoding="utf-8")
    return p


def generate_api_spec_md() -> Path:
    p = SAMPLE_DOCS_DIR / "api_spec.md"
    content = """# OmniPlatform REST API Specification v2.4

## Overview
The OmniPlatform REST API provides programmatic access to document ingestion, case resolution, user authorization, and webhook telemetry.

## Base URL
`https://api.omniplatform.internal/v2`

## Authentication
All requests require a Bearer token in the `Authorization` header:
`Authorization: Bearer <JWT_TOKEN>`

Rate limit: 1200 requests per minute per tenant. Exceeding limits returns HTTP 429 Too Many Requests.

## Endpoints

### 1. Documents Resource
`POST /documents/upload`
- Multipart form upload for `.pdf`, `.docx`, `.txt`, `.md`, `.csv`, `.json`.
- Query Parameters: `extract_tables=true`, `chunk_size=500`.
- Response: `201 Created` with document metadata and computed vector hashes.

`GET /documents/{doc_id}`
- Returns parsed chunks, extraction status, and indexing timestamp.

### 2. Cases Resource
`POST /cases/resolve`
- Payload:
```json
{
  "entity_id": "ENT-1042",
  "query": "What is our reimbursement policy for travel cancellations?",
  "documents": ["company_policy.pdf", "vendor_contract.txt"],
  "require_hitl": true
}
```
- Response: Returns resolution draft with explicit citations and confidence scores.

### 3. Webhooks & Events
- `POST /webhooks/subscribe`: Register callbacks for `case.resolved`, `case.escalated`, `document.indexed`.
- Delivery timeout: 5000ms with exponential backoff up to 3 retries.
"""
    p.write_text(content.strip(), encoding="utf-8")
    return p


def generate_company_policy_txt_and_pdf() -> Path:
    txt_path = SAMPLE_DOCS_DIR / "company_policy.txt"
    content = """GLOBAL CORPORATE GOVERNANCE & OPERATIONAL POLICIES
Document Ref: POL-GLOB-2024-V3
Classification: Internal Corporate Policy

SECTION 1: REIMBURSEMENT & EXPENSE REPORTING
1.1 Business Travel: Air travel must be booked in economy class for domestic flights under 5 hours. Business class requires VP approval for intercontinental flights over 8 hours.
1.2 Meal Allowance: Per diem allowance is capped at $75/day for Tier-1 cities and $50/day for all other locations. Itemized receipts are mandatory for expenses exceeding $25.
1.3 Submission Window: All expense reports must be submitted within 30 calendar days of expense occurrence. Claims past 60 days are permanently forfeited.
1.4 Approvals: Department managers may approve expense claims up to $1,000. Expenses between $1,000 and $10,000 require Director approval. Claims exceeding $10,000 require CFO sign-off.

SECTION 2: REMOTE WORK & EQUIPMENT POLICY
2.1 Hybrid Schedule: Core operational employees may work remotely up to two days per week with manager consent.
2.2 Home Office Stipend: New full-time employees are eligible for a one-time $500 home office equipment stipend within their first 90 days of employment.
2.3 Hardware Ownership: All laptops and mobile devices provided by the company remain company property and must be returned upon employment separation.

SECTION 3: CODE OF CONDUCT, COMPLAINTS & ESCALATION
3.1 Harassment & Discrimination: The company enforces a zero-tolerance policy against workplace harassment, bullying, or unlawful discrimination.
3.2 Whistleblower Protection: Employees reporting ethical or compliance violations in good faith are protected from retaliation.
3.3 Mandatory Escalation: Any grievance alleging discrimination, harassment, legal violation, or fraud must be escalated immediately to the Legal & Compliance review board within 24 hours.

SECTION 4: INTELLECTUAL PROPERTY & DATA PRIVACY
4.1 All innovations, inventions, and documentation created during working hours are company intellectual property.
4.2 Customer PII must never be stored on unencrypted local drives or transmitted over unsecured channels.
"""
    txt_path.write_text(content.strip(), encoding="utf-8")

    # Also generate a lightweight valid PDF using minimal PDF specification bytes
    pdf_path = SAMPLE_DOCS_DIR / "company_policy.pdf"
    try:
        # Minimal valid PDF file generator in pure Python without requiring external tools
        lines = content.strip().split("\n")
        stream_data = "BT /F1 10 Tf 50 750 Td 14 TL "
        for line in lines[:40]:
            cleaned_line = line.replace("(", "[").replace(")", "]").replace("\\", "/")
            stream_data += f"({cleaned_line[:80]}) ' "
        stream_data += "ET"

        pdf_str = (
            "%PDF-1.4\n"
            "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
            "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
            "3 0 obj << /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >> endobj\n"
            "4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
            f"5 0 obj << /Length {len(stream_data)} >> stream\n{stream_data}\nendstream\nendobj\n"
            "xref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000117 00000 n \n0000000234 00000 n \n0000000312 00000 n \n"
            "trailer << /Size 6 /Root 1 0 R >>\nstartxref\n450\n%%EOF\n"
        )
        pdf_path.write_bytes(pdf_str.encode("latin-1"))
    except Exception:
        # Fallback to copy text if pdf writing fails
        pdf_path.write_text(content.strip(), encoding="utf-8")
    return pdf_path


def generate_structured_data() -> None:
    # 1. Product Catalog JSON
    json_path = SAMPLE_DOCS_DIR / "product_catalog.json"
    catalog = {
        "catalog_version": "2024.1",
        "last_updated": "2024-03-15",
        "products": [
            {
                "sku": "PROD-A101",
                "name": "Cloud Data Lake Enterprise",
                "tier": "Enterprise",
                "price_monthly_usd": 1500.0,
                "included_storage_tb": 50,
                "support_level": "24/7 Dedicated Account Manager",
                "warranty_days": 365,
                "refund_policy": "Full refund within 30 days of initial deployment."
            },
            {
                "sku": "PROD-B202",
                "name": "OmniStream Realtime Analytics",
                "tier": "Professional",
                "price_monthly_usd": 450.0,
                "included_storage_tb": 5,
                "support_level": "Standard Business Hours",
                "warranty_days": 90,
                "refund_policy": "Pro-rated refund if SLA uptime falls below 99.5%."
            },
            {
                "sku": "PROD-C303",
                "name": "Edge Gateway Appliance",
                "tier": "Hardware",
                "price_monthly_usd": 250.0,
                "included_storage_tb": 2,
                "support_level": "Hardware Replacement NBD",
                "warranty_days": 730,
                "refund_policy": "Hardware return accepted within 14 days subject to 15% restocking fee."
            }
        ]
    }
    json_path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")

    # 2. Roster CSV
    csv_path = SAMPLE_DOCS_DIR / "employee_roster.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["employee_id", "full_name", "department", "role", "location", "status", "signing_authority_usd"])
        writer.writerow(["EMP-1001", "Aarti Iyer", "Engineering", "Principal Architect", "Bengaluru", "Active", "5000"])
        writer.writerow(["EMP-1002", "Marcus Vance", "Procurement", "VP Global Sourcing", "New York", "Active", "50000"])
        writer.writerow(["EMP-1003", "Elena Rostova", "Customer Success", "Senior Manager", "Berlin", "Active", "2500"])
        writer.writerow(["EMP-1004", "Karthik Reddy", "Finance", "Director of Financial Controls", "Hyderabad", "Active", "25000"])
        writer.writerow(["EMP-1005", "Sarah Jenkins", "Legal & Compliance", "Chief Compliance Officer", "London", "Active", "100000"])


def generate_entities_and_cases() -> None:
    entities = {
        "ENT-1001": {
            "entity_id": "ENT-1001",
            "name": "Aarti Iyer",
            "type": "employee",
            "department": "Engineering",
            "role": "Principal Architect",
            "location": "Bengaluru",
            "tenure_months": 28,
            "security_clearance": "Confidential",
            "history": [
                {"case_id": "CASE-901", "type": "expense", "amount": 420.0, "status": "approved", "date": "2024-01-15"}
            ]
        },
        "ENT-1002": {
            "entity_id": "ENT-1002",
            "name": "CloudScale Technologies",
            "type": "vendor",
            "contract_id": "MSA-2024-8891",
            "account_status": "Active",
            "annual_contract_value_usd": 180000.0,
            "sla_tier": "Critical Enterprise",
            "contact_email": "ops@cloudscale.example.com",
            "history": [
                {"case_id": "CASE-804", "type": "sla_credit", "amount": 1800.0, "status": "resolved", "date": "2023-11-20"}
            ]
        },
        "ENT-1003": {
            "entity_id": "ENT-1003",
            "name": "Apex Global Retail",
            "type": "customer",
            "account_tier": "Enterprise Gold",
            "assigned_csm": "Elena Rostova",
            "products_subscribed": ["PROD-A101", "PROD-B202"],
            "mrr_usd": 1950.0,
            "history": [
                {"case_id": "CASE-771", "type": "onboarding", "status": "completed", "date": "2023-09-01"}
            ]
        }
    }

    cases = [
        {
            "case_id": "CASE-2001",
            "entity_id": "ENT-1001",
            "category": "expense_policy",
            "query": "I had to travel to London for 9 hours on business. Can I claim business class flights and what is my daily meal per diem?",
            "expected_outcome": "resolution_draft",
            "relevant_docs": ["company_policy.pdf", "company_policy.txt"],
            "requires_escalation": False,
            "grounding_check": "Economy under 5 hrs; Business class permitted over 8 hrs with VP approval; Per diem is $75 for Tier-1 cities."
        },
        {
            "case_id": "CASE-2002",
            "entity_id": "ENT-1002",
            "category": "vendor_sla",
            "query": "Our production database suffered a multi-region outage causing monthly uptime to hit 98.6%. What service credit are we owed under MSA-2024-8891?",
            "expected_outcome": "resolution_draft",
            "relevant_docs": ["vendor_contract.txt"],
            "requires_escalation": False,
            "grounding_check": "Under Section 2.3, uptime below 99.0% entitles Customer to a 25% service credit."
        },
        {
            "case_id": "CASE-2003",
            "entity_id": "ENT-1001",
            "category": "compliance_grievance",
            "query": "I am experiencing workplace harassment and retaliation from my supervisor after reporting accounting irregularities. I need immediate investigation.",
            "expected_outcome": "escalation",
            "relevant_docs": ["company_policy.txt"],
            "requires_escalation": True,
            "grounding_check": "Triggered mandatory escalation to Legal & Compliance review board within 24 hours under Section 3.3."
        },
        {
            "case_id": "CASE-2004",
            "entity_id": "ENT-1003",
            "category": "product_refund",
            "query": "We purchased Cloud Data Lake Enterprise 20 days ago. Can we request a full refund according to the product warranty terms?",
            "expected_outcome": "resolution_draft",
            "relevant_docs": ["product_catalog.json"],
            "requires_escalation": False,
            "grounding_check": "Full refund permitted within 30 days of deployment for PROD-A101."
        }
    ]

    (SYNTHETIC_DIR / "entities.json").write_text(json.dumps(entities, indent=2), encoding="utf-8")
    (SYNTHETIC_DIR / "cases.json").write_text(json.dumps(cases, indent=2), encoding="utf-8")


def generate_golden_set() -> None:
    golden_cases = [
        {
            "test_id": "GOLDEN-001",
            "entity_id": "ENT-1001",
            "query": "What is the expense submission window, and can an expense from 75 days ago be reimbursed?",
            "expected_facts": [
                "Expense reports must be submitted within 30 calendar days",
                "Claims past 60 days are permanently forfeited"
            ],
            "expected_citation_doc": "company_policy.pdf",
            "expected_section": "SECTION 1: REIMBURSEMENT & EXPENSE REPORTING",
            "must_contain": ["30 calendar days", "forfeited"],
            "should_escalate": False
        },
        {
            "test_id": "GOLDEN-002",
            "entity_id": "ENT-1002",
            "query": "What is the vendor's required response time for Severity-1 critical incidents?",
            "expected_facts": [
                "Severity-1 tickets require response within 15 minutes of notification"
            ],
            "expected_citation_doc": "vendor_contract.txt",
            "expected_section": "SECTION 2: SERVICE LEVEL AGREEMENT (SLA) & UPTIME GUARANTEE",
            "must_contain": ["15 minutes", "Severity-1"],
            "should_escalate": False
        },
        {
            "test_id": "GOLDEN-003",
            "entity_id": "ENT-1001",
            "query": "My manager threatened to terminate me after I reported illegal safety violations. This is unlawful retaliation.",
            "expected_facts": [
                "Allegations of harassment, illegal acts, or retaliation trigger mandatory escalation"
            ],
            "expected_citation_doc": "company_policy.txt",
            "expected_section": "SECTION 3: CODE OF CONDUCT, COMPLAINTS & ESCALATION",
            "must_contain": ["escalated", "Legal & Compliance"],
            "should_escalate": True
        },
        {
            "test_id": "GOLDEN-004",
            "entity_id": "ENT-1003",
            "query": "What is the refund and restocking fee policy for the Edge Gateway Appliance?",
            "expected_facts": [
                "Accepted within 14 days subject to 15% restocking fee"
            ],
            "expected_citation_doc": "product_catalog.json",
            "expected_section": "products",
            "must_contain": ["14 days", "15% restocking fee"],
            "should_escalate": False
        }
    ]

    with open(GOLDEN_DIR / "golden_set.jsonl", "w", encoding="utf-8") as f:
        for item in golden_cases:
            f.write(json.dumps(item) + "\n")


def main() -> None:
    print("Creating synthetic directories...")
    create_directories()

    print("Generating sample multi-format documents...")
    generate_vendor_contract_txt()
    generate_api_spec_md()
    generate_company_policy_txt_and_pdf()
    generate_structured_data()

    print("Generating synthetic entities and cases...")
    generate_entities_and_cases()

    print("Generating golden evaluation set...")
    generate_golden_set()

    print("Synthetic knowledge generation completed successfully!")


if __name__ == "__main__":
    main()
