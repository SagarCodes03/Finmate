export const formatCurrency = (amount: number) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0
  }).format(amount);

export const formatProbability = (value: number) =>
  new Intl.NumberFormat("en-IN", { style: "percent", maximumFractionDigits: 1 }).format(value);

const riskLabels: Record<string, string> = {
  "numeric__loan_amnt": "Loan amount compared with business revenue",
  "numeric__fico_n": "Credit score",
  "revenue__revenue": "Business revenue",
  "numeric__dti_n": "Debt-to-income ratio"
};

export const readableFeature = (feature: string) => {
  if (riskLabels[feature]) return riskLabels[feature];
  const cleaned = feature.replace(/^(numeric|categorical|revenue)__/, "").replace(/_/g, " ").trim();
  return cleaned ? cleaned.replace(/\b\w/g, (letter) => letter.toUpperCase()) : "Financial context factor";
};

export const newJourneyId = () =>
  `journey-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
