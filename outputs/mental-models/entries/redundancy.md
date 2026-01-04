# Redundancy

***Why systems survive their own failures***

> **Section:** Systems Thinking

In 1970, Apollo 13's oxygen tank exploded 200,000 miles from Earth. The spacecraft lost half its oxygen supply, most of its water, and nearly all its electrical power. The mission commander, Jim Lovell, watched his gauges plummet and transmitted the most famous understatement in space history: "Houston, we have a problem."

The crew should have died. They were in a crippled machine, coasting through vacuum, with no realistic chance of rescue. But they didn't die. They made it home because NASA engineers had built redundancy into every critical system. The spacecraft had backup oxygen tanks, backup power cells, backup navigation systems. Even backup ways to scrub carbon dioxide from the air using materials that weren't designed for the purpose.

Redundancy is duplication that looks wasteful until the moment it saves you.

At its core, redundancy means having more capacity than you need under normal conditions. Two kidneys when one would suffice. Multiple servers when a single machine could handle the load. Three independent sensors measuring the same thing. Extra inventory gathering dust in a warehouse. It appears inefficient because it is inefficient—deliberately so.

The logic is simple: nothing works forever. Parts fail. People make mistakes. Accidents happen. Rare events aren't as rare as we think. A system built to operate at maximum efficiency has no margin for error. When something breaks—and something always breaks—the entire system goes down.

Redundant systems absorb failure. The backup takes over. Operations continue, perhaps degraded, but not collapsed. The plane stays in the air on three engines. The website stays up when one server crashes. Your body keeps working when one kidney fails.

This is why commercial aircraft have multiple hydraulic systems, why hospitals keep backup generators, why suspension bridges use more cables than necessary. The cost of redundancy is constant and visible. The cost of its absence is catastrophic but invisible until the moment of failure.

But redundancy has diminishing returns. Two backups are dramatically better than one. Twenty backups aren't much better than ten. At some point, you're just maintaining expensive equipment that will never be used. The art is calibrating redundancy to actual risk.

It also creates its own problems. Redundant systems need testing, or they fail when you need them. Backup generators that sit idle for years don't start during blackouts. Spare parts rust in warehouses. Skills atrophy when they're never practiced. Redundancy requires maintenance, which requires discipline, which requires believing in disasters you haven't experienced yet.

The model fails when people confuse redundancy with resilience. Having two of everything doesn't help if both fail the same way. If your primary and backup servers run the same buggy software, redundancy is an illusion. This is why NASA didn't just duplicate systems—they used different technologies. The lunar module could serve as a lifeboat not because it was a backup but because it was fundamentally different.

Modern optimization has made redundancy unfashionable. Just-in-time inventory eliminated warehouses. Lean manufacturing cut slack from production lines. Cloud computing promised that you'd never need to own extra capacity. Then a pandemic closed one factory in China and suddenly no one could get computer chips for eighteen months. Efficiency had optimized away the buffer that made the system survive disruption.

The question isn't whether to build in redundancy. It's what failures you can afford and what failures you cannot. You don't need redundant shoelaces. You do need redundant parachutes.

Build slack into systems that cannot tolerate failure. Accept the cost when you're still safe, while redundancy feels like waste. Because the moment you need it, it's already too late to build it.

---
*Part of Mental Models: A Book of Better Thinking at alexandria.press*