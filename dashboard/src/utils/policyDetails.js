// Card text for each measure, keyed by id. A card is used only while the
// measure's description in results.json still matches `description`, so a
// stale card is ignored rather than shown against a changed measure.
export const POLICY_DETAILS = {
  youth_standard_allowance: {
    description:
      "Illustrative age-only stand-in for a separate youth route: the UC standard allowance for single claimants under 25 at 90% of the 2027-28 rate (£317.85 a month).",
    whoIsAffected: "Single UC claimants under 25.",
    howItWorks: "Lowers one monthly amount. Couples under 25 and the support offer are not covered.",
  },
  work_allowance_all_ages: {
    description:
      "Illustrative: UC work allowances 20% higher (£530.33 and £881.82 a month) for all ages, as a stand-in for a youth work allowance.",
    whoIsAffected: "UC claimants with a work allowance (children or the health element) who have earnings, of any age.",
    howItWorks: "Raises the earnings kept before the 55% taper applies.",
  },
  family_benefits_in_training: {
    description:
      "Illustrative: the UC child element and Child Benefit continue for young people in approved education or training until 21 rather than 20.",
    whoIsAffected: "Families with a 20-year-old in approved education or training.",
    howItWorks: "Raises the qualifying young person age limit by one year.",
  },
  shared_accommodation_age_25: {
    description:
      "Illustrative: single renters aged 25 to 34 move from the shared accommodation rate to the one-bedroom rate.",
    whoIsAffected: "Single private renters aged 25 to 34 on UC or Housing Benefit.",
    howItWorks: "Lowers the shared accommodation rate age threshold from 35 to 25.",
  },
};

export function detailsFor(measure) {
  const details = POLICY_DETAILS[measure.id];
  if (!details || details.description !== measure.description) return null;
  return details;
}
