# Tight Coupling

***When one failure guarantees another***

> **Section:** Systems

In the early morning of March 28, 1979, a valve failed in Unit 2 of the Three Mile Island nuclear plant. A small malfunction — the kind engineers plan for. But the valve's failure triggered a pressure relief valve. That valve stuck open. The stuck valve drained cooling water. The dropping water level confused the operators, who were trained to prevent overflow, not underfill. They throttled back the emergency cooling system. The reactor began to overheat. Each component worked as designed. The catastrophe emerged from how tightly they were connected.

This is tight coupling: when components in a system are so interdependent that the state of one directly determines the state of another, with no slack, no buffer, no time to intervene. In a tightly coupled system, problems propagate instantly. A stumble becomes a fall becomes a cascade.

Consider an assembly line. Each station depends on the one before it. If Station 3 stops, Station 4 has nothing to work on. Station 5 waits on Station 4. The entire line halts. This is tight coupling by design — it creates efficiency under normal conditions. But when something breaks, everything breaks together.

Contrast this with loose coupling: a newsroom where reporters work independently, turning in stories throughout the day. One reporter's delay doesn't stop the others. The system has slack. Problems remain local.

Tight coupling appears wherever parts of a system must operate in strict sequence, where timing is unforgiving, where there's no inventory or buffer between stages. Financial markets during a flash crash. Rush hour traffic where one stalled car spawns a twenty-minute backup. A court system where the judge, jury, attorneys, and defendant must all be present simultaneously — if one is late, nothing happens.

The danger multiplies when you combine tight coupling with complexity. Charles Perrow, who studied Three Mile Island, called these "normal accidents" — not because they happen often, but because they're inevitable. In a complex, tightly coupled system, components interact in ways operators can't fully predict. When something fails, the tight coupling ensures the failure spreads faster than anyone can respond. The system becomes its own enemy.

You see this in modern supply chains. Just-in-time manufacturing eliminates warehouses and excess inventory — loose coupling that costs money. Parts arrive exactly when needed. Efficient. Profitable. Until a snowstorm closes a port or a factory in Malaysia floods. Then every assembly line downstream stops at once. The coupling that created efficiency now creates fragility.

Software systems inherit this vulnerability. Microservices that call other services that depend on databases that query APIs — each connection a point where failure can propagate. The 2021 Fastly outage took down Amazon, Reddit, CNN, The New York Times. One CDN failed. The internet shrugged.

Tight coupling misleads in one critical way: it looks like a coordination problem when it's actually a design problem. After a cascade failure, the instinct is to improve communication, train people better, add monitoring. These help. But they don't address the coupling itself. If the system requires perfect execution to avoid catastrophic failure, you have a system designed to eventually fail.

The solution is deliberate slack: buffers, redundancies, circuit breakers. Inventory between production stages. Backup systems that can operate independently. Time delays that prevent instantaneous propagation. Modularity that contains failures. These cost money and efficiency under normal conditions. They're insurance against cascade conditions.

Tight coupling is often invisible until it fails. You don't notice it in the smooth hum of normal operations. You notice it when one small thing breaks and everything else breaks with it — faster than you can understand why, let alone stop it.

**See also:** Fat Tails, Second-Order Effects

The question isn't whether your system has tight coupling. It does. The question is whether you've identified it and built in the slack to survive when coupling becomes contagion.

---
*Part of Mental Models: A Book of Better Thinking at alexandria.press*