"""Hand-written simulation modifiers, one module per modifier.

Rules, copied from the AB2026 dashboard's ``budget_measures``:
- one measure family per module (for example the lower and upper bound of
  one age test), with literal defaults and no runtime state, so a receipt
  can bind the module's exact source;
- a modifier built only from ``young_people_work.measure_templates`` needs no
  two-person attestation; any other modifier does while ``sign_off.REQUIRED``
  is on;
- day-of measures are written here, in this repository, not upstream: an
  upstream merge, release and adoption takes days.

``health_element_min_age`` is the age test on the UC health element (issue
#2). The next likely modifiers are a youth-only standard allowance and work
allowance, and a no-earnings proxy for young people who have never worked
(issue #4).
"""
