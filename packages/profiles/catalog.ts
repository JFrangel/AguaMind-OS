import { educationTutor } from "./profiles/education-tutor";
import { legalResearch } from "./profiles/legal-research";
import { medicalAssistant } from "./profiles/medical-assistant";
import { retailAnalyst } from "./profiles/retail-analyst";

import type { Profile } from "./types";

/**
 * The catalog. To add a new problem domain:
 *   1. Create `packages/profiles/profiles/<slug>.ts` exporting a Profile.
 *   2. Add it here.
 *   3. The 3 frontends pick it up automatically via /apps and /apps/[slug].
 *
 * Order in this array drives the order in the /apps directory page.
 */
export const PROFILES: readonly Profile[] = Object.freeze([
  medicalAssistant,
  legalResearch,
  retailAnalyst,
  educationTutor,
]);

const BY_SLUG: ReadonlyMap<string, Profile> = new Map(PROFILES.map((p) => [p.slug, p]));

export function getProfile(slug: string): Profile | undefined {
  return BY_SLUG.get(slug);
}

export function listProfiles(): readonly Profile[] {
  return PROFILES;
}
