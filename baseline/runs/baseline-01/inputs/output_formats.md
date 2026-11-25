# Shared specialist output formats

Use UTF-8. Write plain JSON objects without code fences. All times are local
24-hour HH:MM strings, quantities are whole packs, and currency is integer US
cents. Additional narrative belongs in the specified Markdown files.

## Logistics

- `logistics.json` has an `agenda` array of objects with `activity`, `start`,
  `end`, and `volunteers`. Use these activity IDs exactly, in order:
  `welcome_checkin`, `icebreaker`, `career_panel`, `structured_networking`,
  `refreshment_break`, `closing_activity`. Use volunteer IDs V1 through V6,
  one or more per block. Cover 16:00 through 19:00 continuously.
- `logistics.md` explains each block, the volunteer duties by block, supplies
  and quantities (including purchased SKU where applicable), accessibility
  arrangements, and contingencies with trigger, action, and owner.

## Budget

- `budget.json` has an `items` array of unique SKU objects with `sku`,
  `quantity`, `unit_cents`, and `total_cents`. The top level has
  `subtotal_cents`, `reserve_cents`, and `total_cents` (subtotal + reserve).
  List each purchase once. Free venue and equipment go in the notes.
- `budget.md` explains coverage, alignment to the logistics supplies,
  provided equipment, and reserve assumptions.

## Marketing

- `marketing.md` has three sections: Instagram caption, Flyer wording, and
  Promotional email (subject and body). Each can stand on its own. Include
  the correct event name, date, hours, audience, promised activities and an
  accessibility contact placeholder. Use [Venue] and [RSVP link] where needed.

## Final package

- `event_package.md` is a readable, self-contained package that includes
  the latest logistics, itemized budget with totals, and all promotional copy.
  Link to the source versions, automated validation, and final review.
