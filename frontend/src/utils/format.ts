export const formatCurrency = (amount: number) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0
  }).format(amount);

export const formatProbability = (value: number) =>
  new Intl.NumberFormat("en-IN", { style: "percent", maximumFractionDigits: 1 }).format(value);

export const readableFeature = (feature: string) =>
  feature
    .replace(/^(numeric|categorical|revenue)__/, "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());

export const newJourneyId = () =>
  `journey-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
