# Monopoly lens
Score: 2 | Vote: PASS

## What is strong
- Honest measurement. Paper-only forward test, a pre-registered verdict date (30/11), explicit pass/fail thresholds (>=53% pass, <51% fail), and the filter cutoff is admitted to be contaminated. That discipline is rare and is the only real "know-how" here.
- Risk rules (stake reduction at $1.800/$1.200/$600) and a tax calculator limit damage while learning.
- The dashboard (RLS, public bankroll link, projection, backup) is competent, but it is a tool, not an edge.

## What would kill it (the top 3, most dangerous first)
1. No edge, and the data points the wrong way. Breakeven is 51,02%; observed is 49,49% on 1.853 entries (SE ~1,2 pt). That is about 1,3 SE BELOW breakeven and about 2,9 SE below the 53% target. Strategy "N equal candles -> next repeats" is a public, trivially copied rule on a near-random M1 series. Not 10x better than anything; it is not better than a coin minus the 4% payout haircut. Expected loss per entry at 49,49% is about -$1,2; the -$2.220,80 matches.
2. Overfitting the filter. The >=4,9 ATR cutoff was picked after seeing data. 54,32% on 408 signals (SE ~2,5 pt) from a searched threshold is a selection artifact until proven otherwise. The clean sample is 16 entries at 50,0%: statistically zero information (SE ~12,5 pt). To confirm a true 54% vs 51,02% breakeven you need roughly 1.000+ clean entries.
3. Counterparty and durability. The house sets payout and price feed (Ebinex, scraped via Playwright). Any real inefficiency, if it existed, would be arbitraged or closed by the broker; bankroll variants (Soros, stops, time windows) rerun the same signals and cannot create edge from negative expectancy.

## The questions I would ask the founder
- What do you know about this market that the other traders on the same broker do not? Why would the rule still work in six months?
- Why should the signal not be just noise, given the clean sample is 16 entries?
- Who is the customer if this becomes a product, and why would a trader without edge pay for a bankroll dashboard?
- Is the broker's feed the source of the price your signal reads, and does the broker ever see your flow?

## If FUND IF: the conditions
Not applicable (PASS). Reopen only if: >=1.000 clean post-freeze entries at >=53% (lower CI bound above 51,02%), cutoff unchanged, and results hold on a different instrument or period.
