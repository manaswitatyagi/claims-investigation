import type { ClaimView } from "./types";

export async function fetchClaimView(claimId: string): Promise<ClaimView> {
  const res = await fetch(`/api/claim/${claimId}/view`);
  if (!res.ok) throw new Error(`view request failed: ${res.status}`);
  return res.json();
}
