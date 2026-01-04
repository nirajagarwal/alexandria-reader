# Bottlenecks

***Why your fastest machine might slow you down***

> **Section:** Systems Thinking

In 1984, Eliyahu Goldratt walked into a failing manufacturing plant and asked a question that seemed too simple: "What's stopping you from making more money?" The plant manager pointed to everything — outdated equipment, unreliable suppliers, worker productivity, quality control. Goldratt spent a week watching the production line. Then he pointed to a single heat-treatment oven in the middle of the facility. "That," he said. "That's your entire problem."

The oven could process 25 units per hour. Everything before it could produce 40 units per hour. Everything after it could handle 50. The plant had spent millions upgrading the faster machines. But production never exceeded 25 units per hour — the speed of that one oven. The bottleneck.

A bottleneck is the constraint that determines the throughput of an entire system. No matter how fast the rest of the system operates, output cannot exceed the capacity of the slowest critical step. The chain breaks at its weakest link.

This shows up everywhere. A restaurant with a brilliant chef but only one oven. A software team with ten developers but one person who can deploy to production. A highway with four lanes that narrows to one. An emergency room with plenty of beds but not enough nurses to staff them.

The cruel mathematics: improving anything except the bottleneck wastes resources. That manufacturing plant could have bought ten new machines for the front end of production. Output would still be 25 units per hour. The money would be gone, the problem unchanged. Only improvements to the bottleneck increase total throughput.

This is counterintuitive because the bottleneck often looks fine. It's not broken. It's working at full capacity. The problem is that full capacity isn't enough. Meanwhile, every other part of the system has idle time. They could do more, but they're waiting. The bottleneck dictates the pace of everything upstream and downstream.

Worse, bottlenecks hide. That oven was obvious once someone looked. But in knowledge work, the constraint might be buried. Is it the approval process? The weekly meeting? The one person who knows the legacy codebase? The bottleneck could be a person, a policy, a piece of equipment, or a step in a process. Finding it requires watching the whole system, not just the parts that feel slow.

Goldratt's insight went deeper. He argued that every system has exactly one bottleneck at any given time. Fix that constraint and you'll see immediate improvement — until you hit the next bottleneck. Production increases until something else becomes the limiting factor. Then that's your new target. The process repeats. Continuous improvement means continuous bottleneck hunting.

This model misleads in one critical way: not every constraint is worth fixing. Sometimes the bottleneck is there by design. A quality control checkpoint that deliberately slows production to catch defects. A hiring process that's intentionally selective. A security review that takes time because it prevents disasters. The bottleneck isn't always the enemy. The question is whether it's serving the system's actual goal.

The practical test: look at what's waiting. If work piles up before a particular step, that's your bottleneck. If resources sit idle after a particular step, that's your bottleneck. The constraint reveals itself through the queues around it.

The deepest lesson from bottlenecks: local optimization often makes the system worse. Making non-bottleneck steps faster just creates more waiting. The system runs at the speed of its slowest critical point. Everything else is theater.

Find the constraint. Fix the constraint. Find the next constraint.

---
*Part of Mental Models: A Book of Better Thinking at alexandria.press*