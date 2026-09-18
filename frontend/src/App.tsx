import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { JourneyStoreProvider } from "./hooks/useJourneyStore";
import { AuditPage } from "./pages/AuditPage";
import { AssistantPage } from "./pages/AssistantPage";
import { HistoryPage } from "./pages/HistoryPage";
import { IntelligencePage } from "./pages/IntelligencePage";
import { JourneyPage, RecoveryPage } from "./pages/JourneyPage";
import { HumanReviewPage } from "./pages/HumanReviewPage";
import { NewJourneyPage } from "./pages/NewJourneyPage";

export default function App() { return <BrowserRouter><JourneyStoreProvider><Layout><Routes><Route path="/" element={<NewJourneyPage />} /><Route path="/journey" element={<JourneyPage />} /><Route path="/assistant" element={<AssistantPage />} /><Route path="/recovery" element={<RecoveryPage />} /><Route path="/human-review" element={<HumanReviewPage />} /><Route path="/intelligence" element={<IntelligencePage />} /><Route path="/audit" element={<AuditPage />} /><Route path="/history" element={<HistoryPage />} /><Route path="*" element={<NewJourneyPage />} /></Routes></Layout></JourneyStoreProvider></BrowserRouter>; }
