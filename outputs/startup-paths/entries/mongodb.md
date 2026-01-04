# MongoDB

***The document database that thrived by refusing to be everything to everyone***

> **Years:** 2007-present

In 2007, Dwight Merriman, Eliot Horowitz, and Kevin Ryan were building DoubleClick's successor — a platform-as-a-service play called 10gen. They needed a database that could handle internet-scale data without the rigidity of traditional relational databases. When they couldn't find one that worked, they built their own. Within two years, they realized the database was more valuable than the platform.

The timing was accidental genius. Web 2.0 companies were drowning in user-generated content, activity streams, and rapidly evolving data structures. MySQL required schema migrations that locked tables. Oracle was expensive and designed for different problems. The emerging NoSQL movement promised liberation from relational tyranny, but most solutions were exotic research projects or infrastructure only Google could operate.

MongoDB offered something deceptively simple: store JSON-like documents, query them flexibly, scale horizontally. Developers could start using it in minutes. No schema to design upfront. No joins to optimize. Just store your objects and query them. For startups moving fast, it felt like freedom.

The early adoption came from exactly where it needed to: developers at startups who could make technology choices without enterprise procurement. Foursquare used it to store check-ins. Craigslist migrated archives to it. The New York Times used it for their article management system. These weren't billion-dollar deals. They were developers choosing tools and telling other developers.

But freedom has costs. MongoDB's early versions had a reputation for losing data. The default write concern didn't wait for writes to persist to disk. Replication was eventually consistent in ways that surprised people. Developers who treated it like MySQL — assuming ACID guarantees they never explicitly configured — discovered data loss in production. "MongoDB is web scale" became a sarcastic meme in 2010, capturing both the hype and the problems.

The company could have collapsed under the weight of its reputation. Instead, they fixed it. Version by version, they added durability controls, improved replication, built better tooling. They were transparent about limitations. They documented the tradeoffs. They didn't promise what they couldn't deliver. The honesty rebuilt trust faster than the features.

The real strategic insight was what they refused to become. As NoSQL fragmented into dozens of specialized databases — graph stores, time series, column-family, key-value — MongoDB stayed focused on document storage. When investors pushed them to add graph queries or analytics, they said no. When customers wanted it to be everything, they pointed to what it did well. This discipline made them legible. "Document database" was a category developers understood.

The competition was ferocious but fragmented. Couchbase pivoted multiple times. Cassandra was powerful but operationally complex. DynamoDB was locked into AWS. Riak had traction but struggled with commercial adoption. MongoDB's advantage wasn't technical superiority in every dimension. It was coherence: a clear use case, decent tooling, and a business model that worked for both startups and enterprises.

Going public in 2017 revealed the business they'd built. Revenue was growing 50% annually. Customers included Forbes, Cisco, Adobe. The Atlas managed service — MongoDB running in the cloud — was becoming the dominant revenue driver. They'd figured out how to sell to enterprises without alienating the developers who loved them. The stock priced at $24, giving them a $1.6 billion valuation.

The market initially skeptical about a database company's growth potential was proven wrong. MongoDB grew revenue from $101 million in fiscal 2017 to over $1.7 billion by fiscal 2024. The stock would eventually 10x from the IPO price. The key was Atlas: fully managed MongoDB in the cloud, billed by consumption, integrated with AWS, Azure, and Google Cloud. They'd bet that developers who started with the free tier would grow into enterprise customers, and the bet paid off.

The cloud providers noticed. Amazon launched DocumentDB in 2018, API-compatible with MongoDB but running on their own engine. It was the ultimate validation and threat: big enough that Amazon wanted the business. MongoDB sued over trademark usage, argued DocumentDB wasn't truly compatible, and pushed Atlas harder. The existence of a competitor with infinite resources focused them. They had to be better at running MongoDB than Amazon could be at emulating it.

What kept them ahead was staying close to developers. They open-sourced the core database under SSPL — a license that let anyone use it but required cloud providers offering it as a service to open-source their platform. Controversial, but clear. They invested in drivers for every language, documentation that didn't assume expertise, and a university program that certified hundreds of thousands of developers. The community became a moat.

Today, MongoDB runs some of the largest applications in the world. It powers content management systems, mobile apps, real-time analytics platforms. The company's market cap exceeds $25 billion. They've survived the hype cycle, the backlash, the cloud competition, and the ongoing debate about whether document databases were the right answer.

The path reveals a pattern: focus wins. They didn't chase every use case or promise to solve every data problem. They built a document database that developers wanted to use, made it reliable enough for production, and figured out how to scale the business before the market moved on. The outcome wasn't inevitable in 2007 when three guys decided to extract the database from their failing platform. But once they committed to being great at one thing, the path became clearer.

---
*Part of All Paths Through a Startup at alexandria.press*