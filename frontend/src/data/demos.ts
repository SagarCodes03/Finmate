export interface DemoCustomer {
  id: string;
  name: string;
  goal: string;
  amount: number;
  outcomeHint: string;
}

export const demoCustomers: DemoCustomer[] = [
  { id: "eligible-demo", name: "Ananya", goal: "Upgrade business equipment", amount: 50_000, outcomeHint: "Eligible path" },
  { id: "missing-info-demo", name: "Vikram", goal: "Expand delivery capacity", amount: 75_000, outcomeHint: "Information needed" },
  { id: "rahul-demo", name: "Rahul", goal: "Expand grocery store", amount: 500_000, outcomeHint: "Human review" },
  { id: "recovery-demo", name: "Meera", goal: "Purchase inventory", amount: 200_000, outcomeHint: "Goal recovery" }
];
