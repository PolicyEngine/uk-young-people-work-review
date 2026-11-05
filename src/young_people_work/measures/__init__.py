"""Hand-written simulation modifiers, one module per modifier.

Rules, copied from the AB2026 dashboard's ``budget_measures``:
- one modifier per module, with literal defaults and no runtime state, so a
  receipt can bind the module's exact source;
- a modifier built only from ``young_people_work.measure_templates`` needs no
  two-person attestation; any other modifier does while ``sign_off.REQUIRED``
  is on;
- day-of measures are written here, in this repository, not upstream: an
  upstream merge, release and adoption takes days.

No modifier is needed yet: the template's computable measures are parameter
changes. The first likely modifiers are an age-limited health element (until
issue #2 is fixed upstream), a youth-only standard allowance and work
allowance, and a no-earnings proxy for young people who have never worked
(issue #4).
"""
