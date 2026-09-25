# Senior Engineer Technical Task — Tariff Quoting Engine

Build a tariff comparison engine for one site's half-hourly consumption, then
design how it scales to a full portfolio.

Budget up to **2.5 hours** of focused work. We would rather see two tariffs priced
correctly and a considered design for scaling than three tariffs and a thin scaling plan.

### Suggested time split for the tasks
| Part | Time    | Deliverable |
| --- |---------| --- |
| A | ~90 min | Working pricing engine, run from the command line |
| B | ~45 min | Written design plus any interface changes to Part A |
| C | ~15 min | `SUBMISSION.md` covering trade-offs and assumptions |

## Ground rules

- **Setup should take under five minutes.** `make install` then `make run`.
- **Use an AI assistant if you normally would.** We assume you will. The
  follow-up call asks why you made each choice, so own the decisions in your
  code.
- **Use any library you like.** Standard library, pandas, whatever suits.
- **Postgres is optional.** `docker compose up -d` gives you one if your design
  wants it. Part A does not require it and you will not lose marks for skipping
  it.
- **Skip** authentication, a UI, deployment config and exhaustive test coverage.
  A handful of tests on the parts that matter is the right amount.
- **If a requirement is ambiguous**, pick something sensible, carry on, and
  record the assumption in `SUBMISSION.md`. We left some ambiguity in on purpose.

## The data you're given

Everything lives under `data/`. It is synthetic — generated for this exercise
rather than taken from a real customer — but it has the shape and the flaws of
the real thing.

### `site_consumption.csv`

One site, a year of half-hourly readings.

| Column | Type | Notes |
| --- | --- | --- |
| `mpan` | string | Meter Point Administration Number; the same site throughout |
| `settlement_date` | ISO date | Europe/London local date |
| `settlement_period` | integer | 1-indexed; period 1 starts at 00:00 local. Most days run to 48 |
| `kwh` | decimal | Consumption during that half hour |
| `reading_type` | `A` or `E` | Actual or estimated |

### `rate_cards/*.json`

Three tariffs, one file each.

| Field | Notes |
| --- | --- |
| `standing_charge_p_per_day` | Pence per day, charged every day of the contract |
| `band_scheme` | One of `flat`, `day_night`, `duos`. Tells you which keys `unit_rates_p_per_kwh` holds and which calendar, if any, resolves a period to a band |
| `unit_rates_p_per_kwh` | Band name to rate, in pence to three decimal places |

### `duos_calendar.json`

Maps settlement period to a distribution band by season and day type, for the
`duos` scheme. Bank holidays are listed in it and are treated as weekends.

All monetary values arrive as strings so you can parse them however you judge
best. **Nothing in the data is guaranteed clean.**

---

## Part A — Pricing engine (75 minutes)

Price the site's annual consumption against each rate card and rank them by
total cost.

**Output.** Print or write a ranking, cheapest first, with a cost breakdown per
tariff. Something like:

```
Rank  Tariff                  Annual (ex VAT)    Standing      Energy       CCL
1     Example Tariff A            £99,999.99   £1,000.00  £95,000.00  £3,999.99
2     Example Tariff B           £101,111.11     £800.00  £96,500.00  £3,999.99
```

Those figures are illustrative of the *format* only — they are not the answer
for this fixture. Break the cost into standing charge, energy (by band where the
tariff has bands), and Climate Change Levy. Layout is yours; the components are
not.

**Requirements.**

1. **Money is exact.** Use `Decimal`, and state your rounding policy — per
   period, per band, per invoice — in `SUBMISSION.md`.
2. **Apply CCL** at `0.775` p/kWh on all consumption. Ignore VAT, or handle it
   and say so.
3. **Handle validation**, including the days where the period count
   is not 48 and the periods that are missing entirely. Your choice of policy
   matters less than stating it.
4. **Separate tariff rules from consumption data.** We should be able to add a
   fourth rate card without editing engine code.
5. **Reject or flag anything you cannot price**, rather than silently producing
   a number.

**Boundaries.** Settlement periods are 1-indexed, period 1 starting at 00:00
local time. All dates are Europe/London. The consumption year runs 1 April 2025
to 31 March 2026. For reference, there are 50 settlement periods. For most days,
only 48 are used. When clocks go forwards or backwards a day may have only 46 
periods defined, or all 50 (more information here: 
https://www.elexon.co.uk/bsc/glossary/settlement-period/) 

---

## Part B — Scale to 5,000 sites (30 minutes)

One API call now asks for every site in a portfolio to be priced against every
rate card we hold: roughly **5,000 sites by 40 rate cards**, run monthly and on
demand. Design it. **Do not build the workers.**

Write at most one page, in `DESIGN.md`, covering five things.

1. **The endpoint contract.** Request and response shapes for submitting a run
   and checking on it. Include what a caller sees while it is still running, and
   how they retrieve results at the end.
2. **Where the work goes.** Name the actual AWS services you would use and why.
   We run FastAPI on ECS with Postgres on RDS today; stay near that unless you
   have a reason not to.
3. **The cost of the computation.** Work out roughly how much arithmetic this
   is, then say what you would do about it. If your answer changes the shape of
   Part A's engine, say which interface you would change.
4. **Partial failure.** Three sites out of 5,000 fail because their consumption
   data is unusable. Describe what the caller sees, what gets stored, and what
   happens on a retry.
5. **Idempotency.** The same run is submitted twice, or a worker retries
   mid-batch. Say how you prevent duplicate or corrupted output.

**What to hand in.** `DESIGN.md`, plus any refactor of Part A that the design
implies — an extracted interface, a changed function signature, a new module
boundary. Skeleton code is fine and no implementation is expected. A design that
requires no change to Part A is a valid answer if you argue it.

We are looking for the reasoning, not the word count.

---

## Part C — `SUBMISSION.md` (15 minutes)

Fill in the template in `SUBMISSION.md`. Keep it short; bullets are fine. This
is the part we read first.

---

## How we assess

We read `SUBMISSION.md`, then the code, then run it. In that order.

**What earns marks**

- Correct money handling and a stated rounding policy
- Sound judgement about messy data
- A Part B design whose numbers you actually worked out
- Honesty about what you cut

**What does not**

- Test coverage percentages
- Abstraction layers with one implementation
- A third tariff instead of a finished Part B

## Submitting
- Include your git history; we like seeing the order you worked in.
- Record any prompts you make to an AI Assistant
