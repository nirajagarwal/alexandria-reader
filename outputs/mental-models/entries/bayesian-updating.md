# Bayesian Updating

***Revising beliefs as evidence arrives***

> **Section:** Probability & Prediction

In 1985, a woman in Boston tested positive for breast cancer in a routine mammogram. The test was 90% accurate — meaning it correctly identified cancer 90% of the time when present, and correctly returned negative results 90% of the time when absent. Her doctor delivered the news gravely. With a 90% accurate test showing positive, she almost certainly had cancer.

She asked to see a statistician.

The statistician asked a different question: What percentage of women her age actually have breast cancer? The answer: about 1%. Now the picture changed. Imagine 1,000 women like her getting screened. Ten would have cancer, and nine of those would test positive. But 990 wouldn't have cancer — and 10% of those, roughly 99 women, would still test positive due to the test's 10% false positive rate.

So out of 108 positive tests (9 true positives plus 99 false positives), only 9 actually indicated cancer. Her chance of having cancer wasn't 90%. It was 8%.

The same test. The same result. Two completely different conclusions. The difference was whether you started with the base rate — the actual prevalence of cancer in the population — or ignored it.

This is Bayesian updating. You start with a prior probability (1% base rate of cancer), then update it with new evidence (the positive test) to reach a posterior probability (8% actual risk). Every piece of evidence shifts your belief, but the shift depends on what you knew before the evidence arrived.

Thomas Bayes, an 18th-century minister, never published the theorem during his lifetime. The math itself is straightforward: multiply your prior belief by how much the new evidence should change it, then normalize. But the implications revolutionized statistics, machine learning, and how we think about uncertainty.

Most people ignore priors entirely. They see evidence and jump straight to conclusions. Someone acts nervous during a conversation — they must be lying. A startup founder went to Stanford — they'll probably succeed. A stock drops 10% — something must be wrong. Each judgment treats the new information as if it exists in a vacuum.

But evidence doesn't replace prior knowledge. It updates it. If 99% of nervous people are just nervous, the nervousness barely shifts your belief about lying. If 90% of Stanford founders fail anyway, the credential moves your estimate only slightly. If stocks frequently drop 10% for no reason, this drop is just noise.

The power of Bayesian updating isn't just getting the math right. It's maintaining the humility to know that you started somewhere. You had a prior belief, maybe implicit, maybe unexamined. New evidence should change that belief, but the strength of the change depends on both the quality of the evidence and the strength of what came before.

Strong priors require strong evidence to shift. If you've driven the same route to work a thousand times, one day of traffic doesn't make you conclude the route is permanently broken. Weak priors shift easily. If you've never tried a restaurant, one good meal substantially raises your estimate of quality.

Where it misleads: Priors can become prisons. If you're too confident in your starting belief, no amount of evidence will change your mind — you'll just explain it away. The Bayesian gambler who "knows" they're on a hot streak ignores each loss. The investor who "knows" a company is great explains away each bad quarter. Updating only works if you remain genuinely uncertain and let evidence genuinely update.

There's also the prior you don't know you have. We all carry implicit beliefs about how the world works — beliefs formed by our particular experiences, our culture, our slice of history. These hidden priors shape every update. Two people see the same evidence and reach different conclusions not because they're irrational, but because they started from different places. Making priors explicit, examining them, is as important as the updating itself.

See also: *Base Rate Fallacy* (ignoring priors entirely), *Confirmation Bias* (updating only on evidence you like).

The woman in Boston didn't have cancer. The statistician's calculation saved her from unnecessary treatment and months of terror. The lesson wasn't about mammograms. It was about how belief actually works: not as certainty that evidence confirms or denies, but as probability that evidence gradually, carefully reshapes.

---
*Part of Mental Models: A Book of Better Thinking at alexandria.press*