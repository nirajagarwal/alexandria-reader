# Plaid

***The infrastructure play that turned rejection into a category***

> **Years:** 2013–present

In 2013, Zach Perret and William Hockey were building a personal finance app called Plaid. It wasn't going well. The app itself was fine — clean interface, decent features — but they kept hitting the same wall: connecting to users' bank accounts was maddeningly difficult. Every bank had different security protocols, different data formats, different API quirks. What should have been plumbing became the entire engineering challenge.

They noticed something else. Every other fintech startup was solving the exact same problem. Venmo was doing it. Betterment was doing it. Robinhood was doing it. Each team was independently rebuilding the same terrible infrastructure, writing custom integrations for thousands of banks, maintaining brittle code that broke whenever a bank changed its login flow.

Perret and Hockey made a decision that felt like retreat: they killed their consumer app and pivoted to selling the bank connectivity layer they'd built. It wasn't glamorous. Infrastructure rarely is. But it was the problem everyone actually had.

The early product was an API. Developers could integrate Plaid and instantly connect to thousands of banks without building any of the integrations themselves. For fintech startups, this was transformative. What used to take months of engineering could now happen in days. The value proposition was so obvious that Plaid barely had to sell — word spread through developer networks.

But banks hated it. Plaid worked by asking users for their actual bank login credentials, then scraping account data by logging in as the user. From a security perspective, this was nightmare fuel. Banks saw Plaid as a credential theft layer with good PR. They weren't entirely wrong — the model was fundamentally insecure by design, a hack made necessary because banks hadn't built proper APIs.

The genius of Plaid's positioning was that they made this the banks' problem, not theirs. When banks complained, Plaid said: build us a real API and we'll use it. Some banks did. Most didn't. Meanwhile, users kept giving Plaid their credentials because the apps they wanted to use required it. Plaid became infrastructure despite opposition from the institutions whose infrastructure they were replacing.

By 2015, the company had raised $60 million and was powering hundreds of fintech apps. Venmo, Acorns, Coinbase, TransferWise — any app that touched a bank account was likely using Plaid. The network effects kicked in hard. The more apps integrated Plaid, the more valuable Plaid's bank coverage became. The more banks Plaid supported, the more apps wanted to integrate. They had built a two-sided platform without really intending to.

The business model was simple: charge per API call. Every time a user connected their bank account, checked their balance, or initiated a transaction, Plaid got paid. As fintech exploded, so did Plaid's revenue. They weren't riding one company's success — they were the substrate beneath an entire category.

In 2018, they raised $250 million at a $2.65 billion valuation. By then, one in four Americans with a bank account had used Plaid, whether they knew it or not. The infrastructure had become invisible, which is the sign of infrastructure working.

Then came the Visa acquisition. In January 2020, Visa announced it would buy Plaid for $5.3 billion — double the last valuation, an extraordinary multiple for a seven-year-old company. The logic was clear: Visa saw ACH transfers moving through Plaid's rails as an existential threat to card networks. Better to own the threat than compete with it.

The deal fell apart. The Department of Justice sued to block it in November 2020, arguing that Visa was acquiring a nascent competitor. The complaint was remarkably specific: Visa executives had called Plaid an existential threat in internal documents. They'd tracked Plaid's growth in payment initiation, seen it as the future of account-to-account transfers, and decided to neutralize the threat through acquisition.

Visa and Plaid abandoned the deal in January 2021. Visa paid Plaid a $250 million breakup fee. The companies called it mutual, but the subtext was clear: the DOJ had killed it and everyone knew further litigation was pointless.

What looked like failure was actually validation. The DOJ doesn't sue to block acquisitions of infrastructure plays unless they think that infrastructure might become something much bigger. Plaid's positioning had shifted from "useful API" to "potential threat to payment networks." They were no longer just connecting accounts — they were potentially replacing entire layers of financial infrastructure.

Post-Visa, Plaid raised $425 million at a $13.4 billion valuation. They'd more than doubled the Visa price without being acquired. The new capital went toward expanding beyond read-only data access into payment initiation, identity verification, income verification — every point where financial data gets passed between systems.

The original insight — that bank connectivity is infrastructure, not a feature — proved more valuable than anyone predicted. What started as two founders frustrated by their personal finance app became the layer beneath modern fintech. They didn't create a new consumer behavior. They didn't invent a new financial product. They just made existing products possible by solving the boring, hard problem that everyone else treated as an obstacle.

By 2024, Plaid powers over 8,000 financial apps and reaches more than 200 million consumer accounts. The infrastructure is still invisible. Most users have no idea what Plaid is, even as they use it multiple times per week. That's exactly what successful infrastructure looks like: essential and unknown.

---
*Part of All Paths Through a Startup at alexandria.press*