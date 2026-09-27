# Submission

Keep this short. Bullets are fine. This is the part we read first.

## Running it

One command, and anything we need to know before running it.

## Assumptions I made

Where the spec was ambiguous and what I chose. Include anything you would
normally have asked us about before writing code.

- assumed UK site location
- assuming the 3 rate cards are the tariffs we are comparing

## Rounding and money

Where you round, at which step, and why.


- **Intermediate Calculations:** All 30-minute period volume and rate multiplications are calculated in pence at exact `Decimal` precision with no rounding.
- **Line Item Rounding:** Individual invoice components (Standing Charge, CCL, and Energy per band) are summed in pence, converted to Pounds (`/ 100`), and rounded to 2 decimal places using `ROUND_HALF_UP`.
   `ROUND_HALF_UP`: .341 -> .34 and .348 -> .35
   Avoid cummulative overcharges this way
   Assumes the undercharges and overcharges will cancel out
- **Annual Total:** The total annual figure is calculated as the sum of the rounded line items to ensure exact alignment on bill.

## Data quality decisions

What you did with short days, long days, missing periods, duplicates and
estimated readings — and what you would do differently with real customer data.

- DST transition dates do not always have 48 settlement periods. In this data set, some days have 46 or 50 periods due to clock changes.
- We do not assume a fixed 48-slot day. Instead, we price using the actual `settlement_period` values in the CSV and resolve out-of-range or missing periods to the nearest defined DUoS band rather than silently defaulting to `green`.
- This is a deliberate trade-off: it preserves a usable price for transition dates without introducing false zeros or heavy-handed data dropping. With real customer data, we would inspect the underlying meter history and confirm whether a missing or duplicated period was a genuine DST artefact or an actual data-quality issue.
- The current implementation intentionally behaves as a warning-and-continue path for anomalous days: it prints validation warnings and still prices the site if the consumption is still usable. This is a designed compromise for Part A.
- A fuller production-grade implementation would add a separate `reject/flag` result path for genuinely unpriceable data (for example: grossly corrupted rows, missing date/period pairs, non-numeric `kwh`, or a site with too many invalid periods to price defensibly). That stricter rejection layer is still a missing Part A implementation step.

## What I cut

Things you deliberately did not do, and roughly how long each would take.

## What I would do next

The first three things, in order.

## Anything that worried me

Something in this task that you think is wrong, risky, or would not survive
contact with real customers.
