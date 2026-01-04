# Datadog

***The monitoring company that won by solving the cloud transition first***

> **Years:** 2010–present

In 2010, Olivier Pomel and Alexis Lê-Quôc were infrastructure engineers at Wireless Generation, an edtech company dealing with a problem that was becoming universal: their systems were moving to the cloud, and none of their monitoring tools worked anymore.

Traditional monitoring was built for a world of stable servers with predictable hostnames. You'd set up Nagios to ping `web-server-01` and `db-server-02`, write custom scripts, and call it done. But in the cloud, servers spun up and disappeared by the minute. Auto-scaling meant the infrastructure itself was fluid. The old tools couldn't handle ephemeral instances, dynamic IP addresses, or the sheer volume of metrics streaming from distributed systems.

Pomel and Lê-Quôc built an internal tool to solve this. It aggregated metrics from everywhere—servers, databases, applications—into a single timeline view. When Wireless Generation was acquired by News Corp in 2010, they took their tool and left. They saw the future: every company was going to face this problem as they moved to AWS. The incumbents were too slow to adapt. There was a window.

They raised a small seed round and launched Datadog in 2010. The pitch was simple: monitoring built for dynamic infrastructure. No more maintaining a labyrinth of custom scripts. No more tools that broke when you scaled. One agent on every host, streaming metrics to a cloud platform that understood tags, not hostnames.

The early customers were startups and engineers at companies beginning their AWS migrations. Datadog wasn't selling to procurement departments or IT managers. They were selling to the people actually running the systems—DevOps engineers who wanted something that worked without fighting it. The product was API-first, developer-friendly, and priced on usage rather than seat licenses. You paid for what you monitored. It scaled with you.

The timing was perfect. AWS was exploding. Docker containers launched in 2013, making infrastructure even more dynamic. Kubernetes followed. Every new layer of abstraction made traditional monitoring tools more useless and made Datadog more essential. Companies weren't just monitoring virtual machines anymore—they were monitoring containers, microservices, serverless functions, each one ephemeral and multiplying.

Datadog kept expanding. They added APM (application performance monitoring) in 2015, letting customers trace requests across distributed systems. Then log management. Then security monitoring. Then network performance, real user monitoring, incident management. Each addition wasn't a separate product sold separately—it was integrated into the same platform, queryable alongside everything else. The value proposition shifted from "monitoring tool" to "observability platform." One place to understand everything happening in your infrastructure.

The flywheel spun faster. More data types meant more reasons to consolidate on Datadog. More customers meant more integrations—over 600 eventually, covering everything from Postgres to Slack. Engineers loved it because it actually worked. Finance teams loved it because consolidating tools saved money. Everyone loved the unified timeline view—when something broke, you could see metrics, logs, and traces together, not scattered across five different dashboards.

Competitors emerged. New Relic pivoted toward APM. Splunk bought SignalFx. Every cloud provider launched their own monitoring. But Datadog had advantages: they'd designed for cloud-native from day one, not retrofitted legacy architecture. They were multi-cloud, which mattered as companies adopted hybrid infrastructure. And they had network effects—the more services you monitored, the more valuable the unified view became.

Revenue grew relentlessly. They passed $100 million in ARR around 2017. They filed to go public in 2019, priced the IPO at $27, and opened at $37.55. The S&P 500 added them in 2020. By 2024, they were doing over $2.7 billion in annual revenue with a market cap exceeding $45 billion.

The business model held up because cloud infrastructure kept growing and kept getting more complex. Every new service, every new deployment pattern, every new compliance requirement created more things to monitor. Datadog's land-and-expand motion was elegant: start with infrastructure monitoring, expand to APM once they trust you, add logs when they're ready, layer in security. Average customer spend grew year over year not through aggressive upselling but through organic expansion as customers monitored more.

They avoided the traps that killed other monitoring companies. They didn't get stuck selling to legacy enterprises running on-premise datacenters. They didn't over-customize and turn into a services business. They didn't let feature bloat make the product unusable. The core experience—install agent, see metrics, query everything—stayed simple even as capabilities expanded.

The story isn't finished. Observability is now a massive market, crowded and contested. Open-source alternatives like Prometheus and Grafana have real traction. Hyperscalers keep improving their native tools. AI-driven observability promises to change what's possible. But Datadog succeeded because they recognized the cloud transition early, built for it natively, and executed relentlessly on a clear vision: make infrastructure observable in a world where infrastructure never stops changing.

They won the timing, they won the product, and they won the market that emerged when the data center moved to the cloud.

---
*Part of All Paths Through a Startup at alexandria.press*