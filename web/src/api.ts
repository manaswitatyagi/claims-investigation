import type { ClaimView } from "./types";

/** Static mode serves the DTO from a baked file instead of the Python server.
 *
 *  The UI consumes exactly one contract, so a file satisfies it as well as a
 *  process does — every panel, including the graph, is a projection of the same
 *  `claim-view/1` object. Set at build time (`VITE_STATIC=1`) rather than
 *  detected at runtime, so a hosted page never fires a request it knows will
 *  fail and then reasons about the error.
 *
 *  What static mode cannot do is ingest a document: that runs the real
 *  extraction and quote-location pipeline. It is disabled with the reason
 *  shown, not mocked. */
export const STATIC_MODE = import.meta.env.VITE_STATIC === "1";

export async function fetchClaimView(claimId: string): Promise<ClaimView> {
  // BASE_URL carries the Pages subpath, so the snapshot resolves whether the
  // site is served from a domain root or from /<repo>/.
  const url = STATIC_MODE
    ? `${import.meta.env.BASE_URL}claim-view.json`
    : `/api/claim/${claimId}/view`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`view request failed: ${res.status}`);
  return res.json();
}
