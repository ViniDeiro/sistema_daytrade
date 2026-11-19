# Product lens
Score: 3/10 | Vote: FUND IF

## What is strong
- The bot's one sentence is clear: "N equal candles, the next repeats; alert me ~7s before close." Paper-only, no orders sent. That restraint is good taste.
- The founder holds himself to a kill rule (>=53% by 30/11, <51% fails) and froze the strength filter. Honest instrumentation is rare.
- The panel shows care in details nobody sees: owner-only RLS (migration 0003 closes the open anon policies from 0001/0002), a public link behind a secret token with a security-definer function that hides individual operations, tax calculator, JSON backup.

## What would kill it (the top 3, most dangerous first)
1. The product has no proven core. 49,49% on 1.853 new entries against 51,02% breakeven means the thing the panel manages has negative expectancy. Fifteen screens polish a result that is not there yet.
2. Two products, one seam. The bot logs paper trades to forward_log.json and serves them on its own index.html; the panel's Operações are results typed by hand each day. Nothing connects them, so the evidence (bot) and the bankroll (panel) can silently disagree. The user does double entry to reconcile a signal with a real fill.
3. Sprawl instead of focus. Many bank variants (Soros, stop win/loss, time window, "contra", cripto, memx, fortes) all run over the same signals. Variants are a way to keep hunting for a winner after the core test says no. The panel adds projection, taxes and a public link for a bankroll that is not yet profitable.

## The questions I would ask the founder
- In one sentence, what is the one thing this does brilliantly? Today it is two things.
- Describe the first five minutes of your day. What do you open, and where do you type a number twice?
- If the filter fails on 30/11, which screens survive? Which ones would you delete today?
- Why does a public bankroll link exist before there is a profit to show?
- Is the panel for you, or for other traders? The design only works for one of them.

## If FUND IF: the conditions
- Choose one surface. Make the bot the source of truth: write its paper trades into Supabase and have Operações read from them. Manual entry only for real fills, as a clearly separate field.
- Freeze the variants. Keep one fixed-stake baseline and cut the rest (Soros, windows, contra, cripto, memx) until the edge is shown.
- Gate the panel work on the verdict: no new screens, no productization, before >=53% on clean forward data.
- Hide Projeção, Impostos and the public link until the bankroll is net positive.
- Pass if 30/11 lands under 51%.
