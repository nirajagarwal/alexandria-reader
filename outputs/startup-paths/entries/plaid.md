# Plaid

***The infrastructure play that became a $13 billion bet on financial data***

> **Years:** 2013-present

Zach Perret and William Hockey met at Bain & Company, where they spent their days building financial models in Excel and their nights complaining about how hard it was to get data out of banks. They were consultants, not engineers, but they kept returning to the same frustration: connecting a bank account to anything — budgeting apps, investment platforms, tax software — required screen scraping, credential sharing, or manual CSV uploads. The infrastructure of personal finance was stuck in 1995.

In 2013, they left Bain to fix it. The initial idea wasn't Plaid. They wanted to build Mint for millennials, a consumer-facing budgeting app that would be beautiful and social. But to make that app work, they needed to solve the connectivity problem first. So they built an API that could securely link to bank accounts and pull transaction data. They figured they'd use it internally, then launch their consumer product.

The API took longer than expected. Banks didn't have standard interfaces. Each institution required custom integration work — reverse engineering mobile apps, maintaining scrapers when banks changed their login flows, dealing with security tokens and multi-factor authentication. It was unglamorous infrastructure work, the kind most startups would outsource. But Perret and Hockey kept building. By late 2013, they had connections to a few dozen banks. They started testing their budgeting app.

Then something unexpected happened. Other developers asked if they could use Plaid's API. Small fintech startups, side projects, weekend experiments — everyone was solving the same problem Plaid had just solved. Perret and Hockey said yes. They opened up the API, charged a few cents per connection, and watched usage grow. Within months, the API business was generating more revenue than they'd projected for their consumer app. The infrastructure they'd built as scaffolding was more valuable than the thing they'd meant to build on top of it.

In 2014, they shut down the consumer app and became an infrastructure company. It was an unsexy pivot. Instead of building a brand consumers would love, they'd be middleware — invisible, technical, boring. But the market was massive. Every fintech startup needed what Plaid had. Venmo, Robinhood, Acorns, Betterment — the explosion of consumer finance apps in the mid-2010s all needed a way to connect to banks. Plaid became the de facto standard.

The growth was steady but not spectacular. Banks viewed Plaid with suspicion. Who were these startup guys accessing customer data? What if there was a breach? The big banks — Chase, Bank of America, Wells Fargo — kept trying to cut Plaid off, changing APIs and login flows to break integrations. Plaid would fix them within hours. It became a cat-and-mouse game. Banks couldn't stop their customers from using apps like Venmo and Robinhood, and those apps all ran on Plaid. By 2016, Plaid was processing millions of connections.

The business model was straightforward: charge per API call, or per connected account. Pricing was low enough that startups could afford it, high enough that scale would generate serious revenue. By 2018, Plaid was connecting to over 15,000 financial institutions across North America and Europe. More than 25% of Americans with bank accounts had unknowingly used Plaid to connect an app to their bank. The company raised a $250 million Series C at a $2.65 billion valuation.

Then in 2019, Plaid made a move that changed everything: it announced it would go beyond read-only data. The company launched products for payments initiation — not just seeing transactions, but actually moving money. This put Plaid in direct competition with the credit card networks. If apps could initiate bank transfers via Plaid, they could bypass Visa and Mastercard entirely. The infrastructure layer was becoming a platform.

In January 2020, Visa announced it would acquire Plaid for $5.3 billion — double its most recent valuation and one of the largest fintech acquisitions ever. The logic was defensive: if Plaid enabled a world where apps could move money directly between bank accounts, credit cards might become obsolete. Better to own the threat.

But the Department of Justice saw it differently. In November 2020, the DOJ sued to block the acquisition, arguing that Visa was eliminating a nascent competitive threat. The complaint was unusually blunt: Plaid was building the infrastructure for a future without card networks, and Visa wanted to kill that future by buying it.

Visa and Plaid fought the suit for two months, then gave up. In January 2021, they mutually agreed to terminate the deal. Plaid was independent again, suddenly worth $5.3 billion in the public's mind, but with no cash from the acquisition.

The company raised a $425 million Series D two months later at a $13.4 billion valuation — 2.5x the Visa price. The market had decided Plaid was worth more as an independent company building the alternative to card networks than as an acqui-hire inside Visa.

By 2024, Plaid was powering over 8,000 fintech apps and serving more than 200 million consumer accounts. The company expanded beyond consumer banking into lending, payroll, and business accounts. Revenue crossed $500 million. The company remained private, but speculation about an IPO was constant.

What Plaid had built was rare: actual infrastructure. Not a consumer brand or a media business disguised as tech, but genuine picks-and-shovels for an industry gold rush. The founders had stumbled into it — they'd wanted to build a budgeting app — but once they saw the opportunity, they committed fully. They chose boring over sexy, infrastructure over consumer glory. And in doing so, they built something more durable than almost any consumer fintech of their era. The apps that ran on Plaid could come and go. Plaid would remain.

---
*Part of All Paths Through a Startup at alexandria.press*