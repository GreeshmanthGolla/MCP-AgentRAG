# OWASP LLM Top 10 Security Architecture & Defenses

## 1. Threat Mitigation Matrix

The **Universal Document Copilot** is designed with defense-in-depth principles addressing the OWASP Top 10 for Large Language Model Applications.

| OWASP Vulnerability | Risk Scenario | Universal Copilot Defense | Enforcing Module |
| :--- | :--- | :--- | :--- |
| **LLM01: Prompt Injection** | Adversarial user query attempts instruction overrides (`"Ignore all previous rules"`). | Pre-execution `InjectionDetector` scans for known jailbreaks and system override patterns. Malicious queries are immediately routed to `blocked_exit`. | `src/universal_copilot/guardrails/injection_detector.py` |
| **LLM02: Sensitive Information Disclosure** | Accidental leakage of customer/employee SSNs, emails, phone numbers, or credentials. | Inbound queries are scrubbed by `PIIRedactor`, replacing sensitive tokens (`[EMAIL_1]`, `[SSN_1]`). LLMs only process sanitized data. | `src/universal_copilot/guardrails/pii_redactor.py` |
| **LLM04: Model Denial of Service** | Oversized payloads or recursive document chunks exhaust token budgets and memory. | Context assembler enforces strict sliding-window token ceilings and prunes duplicate sentences. | `src/universal_copilot/context/assembler.py` |
| **LLM06: Excessive Agency** | Agent autonomously executes high-risk actions (disbursing funds, terminating contracts). | Strict Human-in-the-Loop (`HITLApprovalNode`) governance. The copilot drafts and cites; terminal dispatch requires explicit human operator sign-off. | `src/universal_copilot/graph/nodes/hitl_approval_node.py` |
| **LLM07: System Prompt Leakage** | Attackers prompt the model to reveal internal prompts or proprietary rules. | Specific signature checks detect prompt extraction requests; indirect RAG snippets are isolated in `<untrusted_content>`. | `src/universal_copilot/context/quarantine.py` |
| **LLM08: Vector / RAG Poisoning** | Adversarial documents planted in knowledge corpus containing malicious instructions. | Every retrieved chunk is isolated within `<untrusted_content>` tags and validated by the Reflective Critic before synthesis. | `src/universal_copilot/graph/nodes/critic_node.py` |

---

## 2. Human-in-the-Loop (HITL) Governance Principle

In accordance with strict corporate governance:
1. **Forbidden Auto-Dispatches**: The agent cannot auto-execute financial disbursements, close grievance tickets, or send binding legal communications.
2. **Interactive Review Envelope**: The terminal node formats the draft alongside exact bracketed source document citations, allowing human operators to either approve, edit, or escalate.
