# Graceful Degradation

***Systems that fail well fail less***

> **Section:** Systems Thinking

In 1989, United Airlines Flight 232 lost all hydraulic systems over Iowa. The DC-10 became, in theory, unflyable. No way to control the ailerons, rudders, or elevators. The captain, Al Haynes, and his crew did something unprecedented: they flew the plane using only thrust from the two remaining engines, pushing one forward to turn left, the other to turn right. They crash-landed in Sioux City. Of 296 people aboard, 185 survived.

The aircraft wasn't designed to fly this way. But the control systems degraded gracefully enough that improvisation became possible. The engines could still be throttled independently. The basic structure held. Complete failure became partial failure, and partial failure became survivable.

Graceful degradation is the principle that systems should fail in stages, not all at once. When something breaks, the system loses capability but doesn't collapse entirely. A staircase with a broken step is still usable. A bridge with one damaged support can often carry reduced load. A computer that slows down when memory runs low beats one that simply crashes.

The opposite is catastrophic failure — the cliff edge where everything works until suddenly nothing does. Glass under stress shows no warning before it shatters. A rope holds its full load until the instant it doesn't. These systems offer binary outcomes: perfect function or complete collapse.

Graceful degradation requires deliberate design. It means building in redundancy, but not just redundancy. You need partial independence between components. If one part fails, others continue operating. The electrical grid does this: when one section loses power, circuit breakers isolate the problem rather than letting the cascade bring down the whole network. Well-designed software does this: when one feature breaks, the rest of the application keeps running.

It means accepting that things will break. Instead of trying to prevent all failure — an impossible goal — you ask: "When this fails, what's the least terrible thing that could happen?" Then you design for that.

The human body exemplifies graceful degradation. You can lose a kidney and survive. Break a bone and still move. Tear a muscle and compensate with others. The system sacrifices performance before sacrificing survival. Contrast this with a house of cards, where removing one element brings down everything.

But graceful degradation has costs. Redundancy takes resources. Extra support beams cost money. Backup systems add complexity. The trade-off isn't always worth making. For a disposable pen, catastrophic failure is fine — when it stops writing, you throw it away. For an aircraft control system, the cost of graceful degradation is mandatory.

The model misleads when people mistake it for weakness. "Designed to fail" sounds like an admission of defeat. But the opposite is true: systems designed to fail gracefully are more robust than systems designed never to fail. The latter is arrogance. Graceful degradation is realism.

It also fails when partial failure creates false security. A car's anti-lock brakes that work intermittently might be more dangerous than brakes that simply stop working — at least then you know you have a problem. Degradation is only graceful if the system's new limitations are obvious to whoever operates it.

Watch for situations where small failures compound into large ones. That's where graceful degradation matters most. A bridge should show warning signs before it collapses. A business should be able to lose a client without shutting down. A friendship should survive a disagreement without ending entirely.

The question isn't whether your systems will fail. They will. The question is: when they do, will they fail gradually or all at once?

---
*Part of Mental Models: A Book of Better Thinking at alexandria.press*