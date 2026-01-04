# Expected Value Calculation
***Multiply probability by outcome, sum across possibilities***

> **Section:** Tools

**What it is:** Expected value means calculating what a decision is worth on average across all possible outcomes. You multiply each outcome's value by its probability, then add them up. It's the mathematical answer to "What should I expect from this choice?"

**When to use it:** When you face a decision with quantifiable outcomes and estimable probabilities. Hiring decisions. Investment choices. Product launches. Insurance purchases. Anything where you can put numbers on both "What could happen?" and "How good or bad would that be?"

**How to do it:** 

1. List every outcome you can foresee
2. Estimate the probability of each (they should sum to 100%)
3. Assign a value to each outcome (dollars, years, whatever unit matters)
4. Multiply each probability by its value
5. Add up all those products

Formula: EV = (P₁ × V₁) + (P₂ × V₂) + (P₃ × V₃) + ...

**Example:** You're considering joining a startup. They offer $80,000 salary plus equity that could be worth $0, $200,000, or $2,000,000 depending on how the company performs.

You estimate:
- 60% chance: Company fails, equity = $0
- 30% chance: Company exits small, equity = $200,000
- 10% chance: Company exits big, equity = $2,000,000

Expected value of equity: (0.6 × $0) + (0.3 × $200,000) + (0.1 × $2,000,000) = $260,000

Compare that to a corporate job offering $120,000. The startup's total compensation is $80,000 + $260,000 = $340,000 expected value versus $120,000 guaranteed. But note: expected value doesn't capture your risk tolerance or the variance in outcomes.

**Watch out for:** Expected value assumes you can play the same game many times. If you're making a one-time, irreversible decision — like betting your life savings — the average outcome matters less than the worst case. A 1% chance of losing everything might be unacceptable even if expected value is positive.

It also treats all units as linear. Losing $100,000 when you have $1,000,000 hurts less than losing $100,000 when you have $200,000. Expected value doesn't capture that.

And your probability estimates are guesses. If you're systematically overconfident, you'll systematically miscalculate. Run the calculation with pessimistic probabilities too.

---
*Part of Decision-Making: Tools, Traps and Stories at alexandria.press*