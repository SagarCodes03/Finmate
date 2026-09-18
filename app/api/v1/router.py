from fastapi import APIRouter

from app.api.v1.endpoints import accounts, assistant, customers, health, journey, policy, recovery, risk, simulated_context, transactions, users, verification

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(policy.router, prefix="/policy", tags=["policy"])
api_router.include_router(recovery.router, prefix="/recovery", tags=["recovery"])
api_router.include_router(risk.router, prefix="/risk", tags=["risk"])
api_router.include_router(simulated_context.router, prefix="/simulated-context", tags=["simulated-context"])
api_router.include_router(customers.router, prefix="/custom-customers", tags=["custom-customers"])
api_router.include_router(journey.router, prefix="/journeys", tags=["journeys"])
api_router.include_router(verification.router, prefix="/journeys", tags=["journeys"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["assistant"])
