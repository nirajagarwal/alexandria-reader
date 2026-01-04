# Datadog

***The monitoring company that solved the cloud's visibility crisis***

> **Years:** 2010–present

In 2010, Olivier Pomel and Alexis Lê-Quôc were infrastructure engineers at Wireless Generation, an education technology company in New York. They had the same problem every engineering team dealing with distributed systems had: they couldn't see what was happening inside their infrastructure. Traditional monitoring tools were built for the server era — static machines in known locations running predictable workloads. The cloud broke all those assumptions.

When Amazon Web Services started gaining traction in the late 2000s, it introduced a new operational reality. Infrastructure became ephemeral. Servers spun up and disappeared. Services split into microservices. A single web request might touch dozens of different systems across multiple availability zones. The old monitoring tools — Nagios, Cacti, homegrown scripts — couldn't handle this complexity. They were built to watch fixed infrastructure, not fluid systems where the topology changed by the minute.

Pomel and Lê-Quôc had spent years stitching together monitoring solutions from open-source tools and custom code. They knew the pain intimately. More importantly, they recognized that this wasn't a problem specific to their company. Every engineering team moving to the cloud faced the same visibility crisis. The market was heading toward massive infrastructure complexity, and the tooling hadn't caught up.

They left Wireless Generation in 2010 to build what became Datadog. The initial product was focused on server monitoring — collecting metrics from cloud instances and presenting them in a unified dashboard. Nothing revolutionary in concept, but the execution was different. It was built cloud-native from the start. It understood that infrastructure was dynamic, that servers came and went, that the question wasn't "Is this specific server healthy?" but "Is this service healthy across all its instances?"

The technical insight was making monitoring agent-based but lightweight, designed to run on ephemeral infrastructure without manual configuration. The agents auto-discovered what was running on each server and started collecting relevant metrics immediately. As servers spun up and down, Datadog's view updated automatically. This sounds obvious now, but in 2010 it was a significant departure from how monitoring worked.

The business insight was timing. They launched just as infrastructure-as-a-service was crossing from early adopter territory into mainstream engineering practice. Companies were moving to AWS not because it was trendy but because it was cheaper and more flexible than managing data centers. This migration created an enormous market for cloud-native tooling. Datadog wasn't the only company to see this — New Relic, AppDynamics, and others were building monitoring solutions — but Datadog's specific focus on infrastructure gave them a distinct wedge.

Early traction came from exactly the engineering teams Pomel and Lê-Quôc understood: startups and technology companies running on AWS. These were teams who valued developer experience and were willing to adopt new tools if they solved real problems. Datadog's model was product-led: free tier to get started, usage-based pricing as you scaled, self-service signup. No enterprise sales cycle, no lengthy procurement. Engineers could start using it in the afternoon.

By 2012, they had enough momentum to raise a Series A from Index Ventures. The product was evolving beyond basic server monitoring into application performance monitoring, adding the ability to trace requests through distributed systems. This was crucial. Understanding infrastructure metrics was valuable, but correlating them with application performance was transformative. When a service degraded, engineers needed to see both the infrastructure metrics and the application traces to diagnose the root cause.

The company expanded by adding integrations. Datadog built connections to every major cloud service, database, message queue, and framework that engineering teams used. These integrations weren't just data collection — they provided pre-built dashboards and alerts tailored to each technology. An engineering team running PostgreSQL on AWS could install Datadog and immediately get intelligent monitoring without configuring anything. The integrations became a moat. Each one made Datadog more valuable to teams using that specific stack, and the breadth of integrations made it harder for competitors to match.

Growth accelerated through the mid-2010s as cloud adoption became standard practice, not just among startups but across enterprises. Large companies moving to AWS needed the same visibility that startups did. Datadog's product-led growth model scaled up market. The platform expanded into log management, security monitoring, and real user monitoring. Each addition made the product more comprehensive, and comprehensiveness created switching costs. Once Datadog was your observability platform, replacing it meant replacing multiple tools.

By 2019, when Datadog went public, it had over 8,000 customers and $363 million in annual revenue. The IPO priced at $27 per share, valuing the company at $10.9 billion. The market was betting that observability was a massive, enduring category, and that Datadog's position at the center of cloud infrastructure made it the category winner.

The bet proved correct. The stock climbed through 2020 and 2021 as cloud migration accelerated during the pandemic. Companies that had been gradually moving to the cloud suddenly needed to move everything remote-accessible immediately. Datadog's revenue growth remained above 60% year-over-year. By late 2021, the market cap exceeded $50 billion.

The story isn't one of brilliant pivots or near-death experiences. It's the rarer path: founders who identified a real problem at the right moment, built a product that solved it well, and scaled steadily as the market validated their thesis. The success came from understanding infrastructure engineers deeply, building for their actual workflow, and timing the launch to match a major platform shift. Datadog worked because the cloud created a genuine visibility problem, and the founders built a genuine solution at the exact moment the market needed it most.

---
*Part of All Paths Through a Startup at alexandria.press*