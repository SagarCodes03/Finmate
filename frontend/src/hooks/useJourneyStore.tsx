import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { confirmSimulatedVerification, JourneyApiError, reassessJourney, startJourney } from "../api/journeys";
import type { JourneyRequest, JourneyResponse, SimulatedVerificationField } from "../types/journey";
import { newJourneyId } from "../utils/format";

export type JourneyStatus = "IDLE" | "SUBMITTING" | "SUCCESS" | "API_UNAVAILABLE" | "INVALID_RESPONSE" | "ERROR";

interface JourneyStore {
  result: JourneyResponse | null;
  currentCustomerId: string | null;
  status: JourneyStatus;
  errorMessage: string | null;
  history: JourneyResponse[];
  previousAssessment: JourneyResponse | null;
  customerSummary: { name: string; businessType: string } | null;
  submit: (request: JourneyRequest) => Promise<JourneyResponse | null>;
  openJourney: (journey: JourneyResponse) => void;
  resetError: () => void;
  confirmVerification: (field: SimulatedVerificationField) => Promise<boolean>;
  reassess: (requestedAmount?: number) => Promise<JourneyResponse | null>;
  canReassess: boolean;
  setCustomerSummary: (summary: { name: string; businessType: string } | null) => void;
}

const JourneyStoreContext = createContext<JourneyStore | null>(null);

export function JourneyStoreProvider({ children }: { children: ReactNode }) {
  const [result, setResult] = useState<JourneyResponse | null>(null);
  const [currentCustomerId, setCurrentCustomerId] = useState<string | null>(null);
  const [status, setStatus] = useState<JourneyStatus>("IDLE");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [history, setHistory] = useState<JourneyResponse[]>([]);
  const [previousAssessment, setPreviousAssessment] = useState<JourneyResponse | null>(null);
  const [customerSummary, setCustomerSummary] = useState<{ name: string; businessType: string } | null>(null);
  const [reassessmentCount, setReassessmentCount] = useState(0);

  const value = useMemo<JourneyStore>(() => ({
    result,
    currentCustomerId,
    status,
    errorMessage,
    history,
    previousAssessment,
    customerSummary,
    canReassess: reassessmentCount < 1 && status !== "SUBMITTING",
    openJourney: (journey) => {
      setResult(journey);
      setReassessmentCount(0);
      setErrorMessage(null);
      setStatus("SUCCESS");
    },
    resetError: () => {
      setErrorMessage(null);
      if (status !== "SUBMITTING") setStatus(result ? "SUCCESS" : "IDLE");
    },
    submit: async (request) => {
      setStatus("SUBMITTING");
      setErrorMessage(null);
      try {
        const response = await startJourney(request);
        setResult(response);
        setPreviousAssessment(null);
        setReassessmentCount(0);
      setCurrentCustomerId(request.customer_id);
        if (!request.customer_id.startsWith("custom-")) setCustomerSummary(null);
        setHistory((current) => [response, ...current.filter((item) => item.journey_id !== response.journey_id)]);
        setStatus("SUCCESS");
        return response;
      } catch (error) {
        if (error instanceof JourneyApiError) {
          setStatus(error.kind === "unavailable" ? "API_UNAVAILABLE" : error.kind === "invalid_response" ? "INVALID_RESPONSE" : "ERROR");
          setErrorMessage(error.message);
        } else {
          setStatus("ERROR");
          setErrorMessage("FinMate could not start this journey.");
        }
        return null;
      }
    },
    setCustomerSummary,
    confirmVerification: async (field) => {
      if (!currentCustomerId) return false;
      try { await confirmSimulatedVerification(currentCustomerId, field); return true; }
      catch (error) { setErrorMessage(error instanceof Error ? error.message : "FinMate could not update the simulated verification."); return false; }
    },
    reassess: async (requestedAmount) => {
      if (!result || !currentCustomerId || reassessmentCount >= 1 || status === "SUBMITTING") return null;
      setStatus("SUBMITTING"); setErrorMessage(null);
      try {
        const response = await reassessJourney({ journey_id: newJourneyId(), customer_id: currentCustomerId, customer_goal: result.customer_goal, requested_amount: requestedAmount ?? result.requested_amount }, result.journey_id);
        setPreviousAssessment(result); setResult(response.reassessment);
        setReassessmentCount((current) => current + 1);
        setHistory((current) => [response.reassessment, ...current.filter((item) => item.journey_id !== response.reassessment.journey_id)]);
        setStatus("SUCCESS"); return response.reassessment;
      } catch (error) {
        setStatus("ERROR"); setErrorMessage(error instanceof Error ? error.message : "FinMate could not re-run the governed journey assessment."); return null;
      }
    }
  }), [currentCustomerId, customerSummary, errorMessage, history, previousAssessment, reassessmentCount, result, status]);

  return <JourneyStoreContext.Provider value={value}>{children}</JourneyStoreContext.Provider>;
}

export function useJourneyStore() {
  const store = useContext(JourneyStoreContext);
  if (!store) throw new Error("useJourneyStore must be used inside JourneyStoreProvider");
  return store;
}
