# Account maintenance

Each iteration, alongside scoring the farm habit, the bot maintains the account:
accept a pending party quest when required, allocate one strength point when
points remain, and buy the Enchanted Armoire when gold is strictly above 10000.

## Sub-features

- `maintain-accept-quest` accepts when `party_quest.requires_acceptance` is true.
- `maintain-quest-already-active` ignores recoverable BadRequest messages
  (`quest has already started`, `already accepted the quest invitation`).
- `maintain-allocate-strength` calls allocate when `available_points > 0`.
- `maintain-allocate-skip` skips when points are zero or level/stats missing.
- `maintain-allocate-stat-error` treats NotAuthorized mentioning `stat points`
  as a soft skip.
- `maintain-armoire-buy` buys when `gold > 10000.0`.
- `maintain-armoire-skip` skips at gold equal to the threshold.
- `maintain-single-status` reuses one `UserStatus` snapshot per maintain pass.

## How to get to it (user POV)

- Run the bot with a character that has pending party invites, free stat points,
  or gold above 10000 (live path blocked here).
- Observe log lines `Accepted party quest: …` and `Bought Enchanted Armoire`.

## Driving it with verify-habitica-levelup

Preconditions:

- Doctor-healthy scratch from `scripts/launch.sh`.
- Owner rule: do not launch this app. Live proof is
  **not run (owner rule: do not launch this app)**.
- Gateway methods are mocked; no Habitica traffic.

- **Drive suite.** Run
  `.cursor/skills/verify-habitica-levelup/scripts/drive.sh "$SCRATCH" account-maintenance`.
- **Quest accept.** `test_accept_pending_party_quest` awaits
  `accept_pending_party_quest` when required; skip test covers false.
- **Recoverable quest errors.** already-started and already-accepted BadRequest
  paths return without raise; other BadRequest and auth errors re-raise.
- **Allocate.** success, no points, missing stats, stat-points auth soft-skip,
  and other auth re-raise tests in `tests/test_bot.py`.
- **Armoire.** `test_buy_armoire_if_wealthy` buys above threshold;
  `test_buy_armoire_if_wealthy_skips_at_threshold` does not call buy at 10000.0.
- **Engine pure checks.** `tests/test_engines.py` for `should_buy_armoire` and
  `should_accept_party_quest`.
- **Shared snapshot.** `test_maintain_account_reuses_single_status_snapshot`
  asserts one `get_user_status` for the maintain bundle.
- **Proof.** Evidence transcript exit 0 and `PROOF.md`. `STATIC_NOTE.md` records
  **not run (owner rule: do not launch this app)**.

## Gotchas

- Armoire uses strict greater-than (`gold > 10000.0`), not greater-or-equal.
- Stat allocation always targets strength (`Attributes.STR`) via the gateway.
- Party quest accept is also attempted once during `initialize`, not only in
  the loop.
- Do not invent gold thresholds or quest message strings; copy from
  `LevelUpService` and its tests.
