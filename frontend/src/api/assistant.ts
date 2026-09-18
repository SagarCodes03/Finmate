import type { ChatMessage } from "../types/chat";
import type { JourneyResponse } from "../types/journey";
import { apiBaseUrl } from "./journeys";

export interface AssistantChatResponse {
  response: string;
  tools_used: string[];
  journey_status: string | null;
  context_used: string[];
  governance_note: string;
}

export async function sendAssistantMessage(payload: {
  customer_id: string;
  message: string;
  conversation_history: ChatMessage[];
  current_journey: JourneyResponse | null;
}): Promise<AssistantChatResponse> {
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}/api/v1/assistant/chat`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
  } catch { throw new Error("FinMate AI Assistant is unavailable."); }
  if (!response.ok) {
    let detail = "FinMate AI Assistant could not answer right now.";
    try {
      const errorBody: unknown = await response.json();
      if (errorBody && typeof errorBody === "object" && typeof (errorBody as { detail?: unknown }).detail === "string") {
        detail = (errorBody as { detail: string }).detail;
      }
    } catch { /* Use the safe fallback when the backend has no JSON error body. */ }
    throw new Error(detail);
  }
  const data: unknown = await response.json();
  if (!data || typeof data !== "object" || typeof (data as AssistantChatResponse).response !== "string") throw new Error("FinMate AI Assistant returned an invalid response.");
  return data as AssistantChatResponse;
}
