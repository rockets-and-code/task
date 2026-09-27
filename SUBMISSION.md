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

## What I cut

Things you deliberately did not do, and roughly how long each would take.

## What I would do next

The first three things, in order.

## Anything that worried me

Something in this task that you think is wrong, risky, or would not survive
contact with real customers.
