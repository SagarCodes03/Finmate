# FinMate frontend

React/Vite presentation layer for the governed FinMate journey. It calls only `POST /api/v1/journeys` for the main journey flow; risk, SHAP, policy, and recovery remain backend-owned.

```powershell
Copy-Item .env.example .env
npm install
npm run dev
```

Vite runs at `http://127.0.0.1:5173` by default, matching the backend's local CORS configuration. Run `npm test` and `npm run build` to verify the frontend.
