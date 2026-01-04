# Defense in Depth

***Why single barriers fail***

> **Section:** Systems & Strategy

In 1912, the *Titanic* carried sixteen watertight compartments designed to contain flooding. The ship could survive four breached compartments and still float. Naval architects called this "practically unsinkable." They built the ship to withstand the worst collision they could imagine, then stopped there.

On April 14, the iceberg opened six compartments to the sea. The ship sank in less than three hours.

The designers had made a common error: they built one layer of protection and assumed it was enough. They didn't ask what happens when that layer fails. They didn't plan for the unimaginable, which has a habit of happening anyway.

Defense in depth is the principle that no single barrier is sufficient. You protect what matters by stacking multiple, independent layers of defense. When one fails—and it will—the next layer catches what breaks through.

The concept comes from military strategy. A castle didn't rely solely on its walls. It had walls, yes, but also a moat, a drawbridge, an outer bailey, an inner keep, and archers at every level. An attacker who breached the outer wall still faced five more obstacles. Each layer bought time and forced the enemy to solve a different problem.

This thinking applies far beyond warfare. Computer security works the same way. A network protected only by a firewall is vulnerable the moment that firewall is compromised. A well-designed system stacks defenses: firewall, intrusion detection, access controls, encryption, backups, monitoring. An attacker who gets through the firewall still faces authentication. Someone who steals credentials still can't read encrypted data. Someone who corrupts files encounters backups.

The key is independence. Layers that fail together provide no depth. If your fire alarm and sprinkler system both rely on the same power source, a power outage defeats both. If your backup server sits in the same building as your primary server, the same flood destroys both copies. True defense in depth means each layer protects against different failure modes.

This costs more than a single barrier. It requires redundancy, which feels wasteful when everything works. It's tempting to ask: Why maintain three systems when one has never failed? The answer: because the day it fails is the day you need the other two.

Where defense in depth misleads is in creating a false sense of security through theatrical layers. Adding ten locks to a door made of paper doesn't help. The layers must actually be capable of stopping threats. Security theater—the appearance of protection without substance—is worse than no defense at all because it creates complacency.

The model also suggests that more is always better, but there's a point of diminishing returns. Too many layers create complexity that becomes its own vulnerability. A system so complex that no one understands it fully, where interactions between defensive layers create new failure modes, has defeated itself.

The lesson is this: anything worth protecting is worth protecting multiply. The first barrier will fail. Plan for that failure. Build the second barrier different from the first. When the second fails—and it might—have a third ready. Don't ask "How can I make this one thing strong enough?" Ask "What happens when it breaks, and what catches it?"

The *Titanic* taught this lesson in the coldest possible terms. One layer of defense, no matter how well-designed, is a single point of failure. And single points of failure eventually fail.

---
*Part of Mental Models: A Book of Better Thinking at alexandria.press*