# FinMate Product Requirements Document

## Product

**FinMate — Your AI teammate for financial journeys**  
Team: **Adaptive Edge**

FinMate is a goal-driven AI teammate for prototype lending journeys. It helps a customer progress toward an underlying financial goal rather than treating a loan request as the sole outcome.

## Problem

Traditional lending journeys can end when a requested amount or product is not suitable. Customers receive little explanation, no guided remediation, and no legitimate alternative path toward the original goal.

## Vision and differentiator

FinMate understands a customer's goal, gathers the relevant simulated context, obtains a governed ML risk signal, applies deterministic policy, and guides the next best permitted action.

Its core differentiator is **Goal Recovery**: if the original request is not viable, FinMate diagnoses the governed reason and proposes legitimate alternatives that may still move the customer toward the same goal.

FinMate does not allow an LLM to approve or reject a loan.

## Target users

- Small-business owners seeking financing for a clear business objective.
- Customer-support or operations reviewers handling exceptional journeys.
- Demo operators showing an end-to-end governed lending flow.

## Core user journey

1. Customer states a financial goal and requested amount.
2. AI agent clarifies the goal and collects permitted information.
3. Backend assembles simulated customer, business, CRM, and bank context.
4. XGBoost returns a risk/eligibility signal; SHAP produces model-linked reasons.
5. Policy engine deterministically returns an approved, declined, pending, or review outcome.
6. FinMate explains the next step in plain language.
7. When the original request is unsuitable, Goal Recovery generates governed alternatives.
8. High-impact, ambiguous, or exceptional cases are escalated to human review.

## Core features

- Goal capture and clarification through an LLM provider abstraction.
- Simulated context gathering through replaceable adapters.
- Governed XGBoost risk scoring.
- SHAP explanations generated from the scored model and feature values.
- Versioned deterministic policy rules and auditable decision records.
- Goal Recovery recommendations constrained by policy.
- Customer-facing explanations, missing-requirement checklist, and handoff state.
- Human-review queue for escalated cases.

## Rahul demo journey

Rahul is a grocery-store owner who requests **₹5 lakh** to expand his business.

1. FinMate records the goal: grocery-store expansion, requested financing: ₹5 lakh.
2. It gathers only simulated customer and business data required by the demo.
3. The risk model and policy layer determine that the requested path is not suitable, or requires review.
4. FinMate communicates the governed result and reasons without asserting that the LLM made the decision.
5. Goal Recovery offers only configured, permissible options, for example:
   - right-sized financing of ₹2.5 lakh;
   - phased financing; or
   - eligibility-improvement actions followed by a later reapplication.
6. Rahul selects a recovery path, requests human assistance, or exits the journey.

## Functional requirements

- The API shall create and persist a financial-goal journey with a unique journey ID.
- The API shall separate raw context, normalized features, model output, SHAP explanation, policy result, recovery options, and agent messages.
- The model endpoint shall return a risk signal and model version, not a final approval decision.
- The policy endpoint shall consume explicit inputs and produce a deterministic outcome, policy version, and machine-readable rule reasons.
- Recovery options shall be generated only after policy evaluation and shall retain the original goal and decision evidence.
- The agent shall call backend tools for state-changing or governed information; it shall not invent scores, policy outcomes, or integrations.
- The workflow layer shall support pending-information and human-review states.
- All demo data and integration responses shall be visibly labeled simulated.

## Non-functional requirements

- Use Python, FastAPI, SQLite/SQLAlchemy, React/Vite, n8n, XGBoost, and SHAP.
- Keep LLM, CRM, bank, and workflow adapters provider-agnostic and replaceable.
- Make all governed outcomes reproducible from stored input, model version, policy version, and recovery-rule version.
- Maintain structured logs with journey and decision correlation IDs; avoid personal/private financial data.
- Keep the prototype understandable, local-runnable, and demo-resilient.
- Return clear errors and safe fallbacks when a simulated dependency is unavailable.

## Success and demo metrics

- Rahul's journey completes from goal capture through a governed outcome and a recovery option.
- Every displayed decision has a policy version, model version where scored, and traceable reasons.
- At least one unsuitable ₹5 lakh path yields a legitimate recovery path rather than a dead end.
- Demonstrate at least one human-review escalation.
- Do not present unmeasured performance, approval rates, or business outcomes as facts.

## Acceptance criteria

- A demo user can create, resume, and inspect a journey through the frontend.
- The backend can score a prepared feature payload and persist its model metadata and SHAP explanation.
- A policy evaluation is deterministic for identical inputs and records its triggered rules.
- The LLM can explain and orchestrate, but cannot issue a final approval or rejection.
- Goal Recovery produces only options allowed by configured policy and links them to the stated goal.
- UI and API label all data and integrations as simulated unless an integration is actually implemented.
- High-impact or ambiguous cases have an explicit human-review status and handoff payload.

## Explicit prototype limitations

- This is not a production lending system or a real credit decision.
- Data may be simulated customer, business, CRM, and bank data.
- No real Paytm, bank, CRM, or lender integration may be claimed unless actually implemented.
- The prototype does not use personal/private financial data.
- Model performance is unknown until an actual, reproducible evaluation is conducted; no metrics may be invented.
- Recovery options are demo policy paths, not loan offers or real customer outcomes.
