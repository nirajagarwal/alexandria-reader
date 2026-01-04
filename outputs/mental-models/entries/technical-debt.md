# Technical Debt

***The hidden compound interest on shortcuts***

> **Section:** Systems and Complexity

In 1992, Ward Cunningham was trying to explain to his managers why they needed to refactor code. The software worked — users could do what they needed to do — but beneath the surface, the codebase had accumulated decisions that made future changes harder. Each quick fix, each "we'll clean this up later," had left the system more brittle.

His managers didn't understand why working code needed expensive programmer time. So Cunningham reached for a financial metaphor: "Shipping first-time code is like going into debt. A little debt speeds development so long as it is paid back promptly with refactoring. The danger occurs when the debt is not repaid. Every minute spent on code that is not quite right for the programming task of the moment counts as interest on that debt."

The metaphor worked because it captured something everyone understood: shortcuts have compound costs.

Technical debt is the accumulated consequence of expedient decisions in complex systems. Every time you choose the quick solution over the right one, you take out a loan against your future self. The code runs. The product ships. But the underlying structure becomes harder to maintain, harder to extend, harder to understand.

The interest comes due in multiple forms. Simple changes take longer because you have to work around previous shortcuts. New features require more planning because the system wasn't designed for them. Bugs become harder to fix because the code has grown tangled. Eventually, the interest payments consume so much time that forward progress slows to a crawl.

This isn't limited to software. Every system that evolves through decisions accumulates debt.

A company hires rapidly without clarifying roles — technical debt in organizational structure. A city patches roads year after year instead of rebuilding them — technical debt in infrastructure. A student crams for exams without building foundational understanding — technical debt in learning. A writer publishes without revision, planning to "fix it in editing" — technical debt in craft.

The debt isn't always bad. Sometimes the right move is to ship the imperfect version, to hire before you have perfect role clarity, to patch the road one more year. Strategic debt can be worth taking. The mistake is in not recognizing that you've taken it, or in never paying it back.

What makes technical debt dangerous is its invisibility. Financial debt shows up on balance sheets. Technical debt hides in the guts of systems. Outsiders can't see it. Even insiders often don't notice it accumulating until the interest payments become crushing. The team that built the shortcuts has moved on. The new team inherits a system they don't fully understand, one that fights them at every change.

The cure is deliberate refactoring: stopping forward progress to pay down the debt. This is expensive and feels unproductive. No new features ship. No visible progress occurs. But systems that never refactor eventually collapse under the weight of their own history. The interest compounds until the only option is a complete rewrite — declaring bankruptcy on the entire system.

The model reveals why "move fast and break things" has a hidden second half: "and then spend years fixing what you broke." It shows why legacy systems persist long past their useful life — replacing them means paying back decades of accumulated debt all at once. It explains why mature organizations slow down even when they have more resources — they're spending more time servicing old decisions than making new ones.

Where technical debt misleads is in suggesting all problems come from past shortcuts. Sometimes systems are just complex. Sometimes the world changes in ways you couldn't have predicted. Not all maintenance work is debt repayment. Some is just the cost of keeping any complex system running.

The takeaway: Every shortcut is a loan against your future capacity. The question isn't whether to take the loan — sometimes you should. The question is whether you'll pay it back before the interest overwhelms you.

---
*Part of Mental Models: A Book of Better Thinking at alexandria.press*