# Monte Carlo Thinking

***When you can't solve the problem, simulate it***

> **Section:** Reasoning Under Uncertainty

In 1946, Stanislaw Ulam was recovering from encephalitis and playing solitaire to pass the time. A mathematician by training, he found himself wondering: what are the actual odds of winning this hand? He could try to calculate it formally — working through probability trees, conditional dependencies, all the ways the cards could fall — but the math quickly became impossible. There were too many branches, too many combinations.

Then it occurred to him: why not just play the game a hundred times and count how often he won?

This seems almost stupidly simple. But Ulam realized he'd stumbled onto something powerful. Some problems are too complex to solve analytically but trivial to simulate. You don't need the perfect equation. You just need to run the scenario many times and watch what happens.

He shared the insight with John von Neumann, who immediately saw its potential. They were working on neutron diffusion problems for the Manhattan Project — questions involving particles bouncing through materials in ways no equation could predict cleanly. But they could simulate individual particles, follow random paths, run thousands of trials. The average outcome would reveal what the math couldn't.

They named the method after the Monte Carlo casino, where Ulam's uncle used to borrow money to gamble. The name stuck.

**The Core Idea**

Monte Carlo thinking replaces calculation with simulation when problems involve:
- Many variables interacting
- Randomness or uncertainty
- Complex feedback loops
- Outcomes that depend on chance

Instead of deriving the answer, you create a model of the situation, inject randomness where it belongs, and run it thousands or millions of times. The distribution of outcomes shows you what to expect: the average case, the range of possibilities, the tail risks.

A financial analyst trying to forecast project returns doesn't need to solve for every possible scenario. She runs ten thousand simulations with variables randomly sampled from realistic ranges — market conditions, construction delays, regulatory changes. The results show not just the expected return but its variance, the probability of loss, the shape of the distribution.

A logistics company doesn't calculate the optimal delivery route through changing traffic. It simulates thousands of routes with randomized traffic patterns and chooses the one that performs best across conditions.

The power is in volume. One simulation might mislead. Ten thousand simulations reveal the truth.

**Where It Misleads**

Monte Carlo thinking is only as good as your model. If you simulate based on wrong assumptions — if your ranges are too narrow, your correlations mistaken, your model missing key variables — you get precision without accuracy. The computer will confidently tell you nonsense.

It also obscures understanding. When you solve a problem analytically, you see *why* the answer is what it is. When you simulate it, you see *what* happens but not always why. The method trades insight for practicality.

And people often mistake simulation for prediction. Monte Carlo reveals what could happen across many runs, not what will happen in the one run that matters. The average outcome might never actually occur.

**The Takeaway**

When a problem has too many moving parts to solve cleanly, don't keep adding equations. Model the system, add realistic randomness, and run it until patterns emerge. Sometimes the only way to know what happens is to let it happen ten thousand times and watch. See also: Fat Tails, Ergodicity.

---
*Part of Mental Models: A Book of Better Thinking at alexandria.press*