import { error } from "@sveltejs/kit";

import { getProfile } from "@agentos/profiles";

import type { PageLoad } from "./$types";

export const load: PageLoad = ({ params }) => {
  const profile = getProfile(params.slug);
  if (!profile) {
    throw error(404, `No existe el profile "${params.slug}"`);
  }
  return { profile };
};
