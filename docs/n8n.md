# FinMate n8n Prototype Workflow

`workflows/finmate_journey.json` is an importable n8n workflow export for the FinMate hackathon demo. It is orchestration only: it does not score risk, calculate SHAP, approve/reject financing, apply policy rules, or generate recovery rules.

## Prototype boundary

All CRM, financial, and credit context endpoints in this workflow are **SIMULATED_PROTOTYPE** adapters. They are not Paytm, bank, CRM, or credit-bureau integrations. XGBoost emits a prototype risk signal; SHAP explains that model signal; FastAPI's deterministic Policy and Goal Recovery services govern the next path. No result is a real loan approval, product offer, or guaranteed outcome.

## Required environment variable

Set this in the n8n environment before activating the workflow:

```text
FINMATE_API_URL=https://your-publicly-reachable-finmate-host
```

Do not include a trailing slash. The workflow uses `$env.FINMATE_API_URL`; no credentials, keys, or secrets are embedded in the JSON.

## Running FastAPI and reaching it from n8n Cloud

Start the API from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

`localhost` in n8n Cloud means the n8n Cloud container, not your PC. For a local demo, expose port 8000 through an approved secure HTTPS tunnel or deploy the API to a reachable demo host, then set `FINMATE_API_URL` to that HTTPS address. Restrict access to the demo and remove the exposure when finished. This repository does not create or connect any tunnel or n8n account.

## Import and run

1. In n8n Cloud, create/import a workflow and select `workflows/finmate_journey.json`.
2. Configure `FINMATE_API_URL` in the n8n environment used by the workflow.
3. Confirm `GET {FINMATE_API_URL}/api/v1/health` works from n8n's network.
4. Activate or manually execute the webhook node.
5. POST a journey request to the n8n webhook URL.

Rahul demo input:

```json
{
  "journey_id": "rahul-demo-001",
  "customer_id": "rahul-001",
  "customer_goal": "Expand grocery store",
  "requested_amount": 500000
}
```

## Node flow

1. **FinMate Journey Input** receives the webhook request.
2. **Validate Request** validates required journey fields only.
3. **Get Simulated CRM Context**, **Financial Context**, and **Credit Context** retrieve clearly labeled prototype fixtures from FastAPI.
4. **Build Model Context** maps those fixtures to the seven existing ML features.
5. **Run Risk Inference** calls the existing FastAPI wrapper around `app.ml.inference.predict_risk`.
6. **Get SHAP Explanation** retains the SHAP factors returned by that existing inference call; it does not calculate SHAP.
7. **Evaluate Policy** calls the existing deterministic policy endpoint.
8. **Decision Router** branches only on the policy's returned decision:
   - `NOT_SUITABLE` → **Goal Recovery**, then a structured final result.
   - `COMPLEX_REVIEW` → human-review result.
   - `MISSING_INFORMATION` → information-request result.
   - `ELIGIBLE` → governed-next-step result.

The workflow preserves the original goal and amount in every final result. It never makes an independent lending decision.

## FastAPI endpoints used

- `GET /api/v1/simulated-context/{customer_id}/crm`
- `GET /api/v1/simulated-context/{customer_id}/financial`
- `GET /api/v1/simulated-context/{customer_id}/credit`
- `POST /api/v1/risk/infer`
- `POST /api/v1/policy/evaluate`
- `POST /api/v1/recovery/evaluate` — called only on the `NOT_SUITABLE` branch

`POST /api/v1/risk/infer` returns the existing model probability/class plus its SHAP risk and protective factors. It remains a prototype risk signal, not an approval/rejection service.
