# Single Points of Failure

***When one component can bring down the entire system***

> **Section:** Systems Thinking

On January 28, 1986, the Space Shuttle Challenger lifted off from Cape Canaveral in front of millions of television viewers. Seventy-three seconds later, it exploded. Seven astronauts died. The investigation revealed that a single rubber O-ring, chilled by overnight freezing temperatures, had failed to seal properly. One small component, costing a few dollars, destroyed a $2 billion spacecraft and ended the shuttle program for nearly three years.

The O-ring was a single point of failure — a component whose breakdown causes the entire system to fail.

Every system contains dependencies. Water depends on pipes. Power depends on transformers. Your morning depends on your alarm. Most of these dependencies are redundant: if one pipe bursts, water flows through others. But single points of failure have no backup. When they break, everything breaks.

The danger isn't always obvious. The Challenger's engineers knew the O-rings were important, but didn't fully grasp that they were the *only* seal preventing hot gases from breaching the solid rocket booster. NASA's systems had redundancies for almost everything — backup computers, redundant sensors, multiple engines. But redundancy in 99 systems means nothing when system 100 has none.

Single points of failure hide in plain sight because most systems work most of the time. Your company's entire customer database runs on one aging server. Fine — until it crashes. Your business has one person who knows how the payroll system works. Fine — until they quit. You have one supplier for a critical component. Fine — until they go bankrupt. The absence of failure masks the presence of fragility.

The model applies beyond physical systems. A startup with one major customer has a single point of failure. So does a career built on a single skill in a changing industry. A relationship where only one person knows how to manage money, or cook, or navigate conflict. A government where one person can halt all legislation.

Identifying single points of failure requires asking: What would break everything? Then: What is the backup plan? If there is no backup plan, you've found your single point of failure.

Eliminating them isn't always possible or practical. Redundancy costs money, adds complexity, and sometimes contradicts other goals. A business can't maintain three CEOs as backup. But you can document systems, cross-train people, diversify suppliers, and design processes that degrade gracefully rather than collapse completely.

The most dangerous single points of failure are the ones you discover only when they fail. The Challenger crew didn't know their lives depended on a rubber ring. Most people don't know what single point of failure they're trusting until it's too late to add redundancy.

This model misleads when it encourages paranoid over-engineering. Not every dependency needs backup. Your coffee maker is a single point of failure for your morning coffee, but you don't need a second coffee maker. The question is: What is the cost of failure? For coffee, it's annoyance. For the Challenger, it was seven lives. Scale your redundancy to the stakes.

The clearest signal of a single point of failure: when someone says "Nothing can go wrong as long as..." Everything after "as long as" is your vulnerability.

One component. One person. One assumption. When it holds, everything works. When it breaks, everything stops. The system may run smoothly for years, creating the illusion of robustness. But fragility isn't revealed by what usually happens. It's revealed by what happens when the one critical thing finally fails.

---
*Part of Mental Models: A Book of Better Thinking at alexandria.press*