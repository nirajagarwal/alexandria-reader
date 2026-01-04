# Elastic

***The open-source company that refused to stay open***

> **Years:** 2012-present

Shay Banon didn't set out to build a company. He built Elasticsearch because he needed it — a search engine that could actually handle the messy, unstructured data that real applications produced. It was 2010, and Banon, an Israeli developer living in London, was working on a recipe search app for his wife. Apache Lucene existed, but wrapping it in something usable and scalable was another matter entirely. So he built Elasticsearch: distributed, JSON-based, RESTful, designed to just work.

He released it as open source under the Apache 2.0 license. Developers found it. They loved it. By 2012, enough companies were running it in production that Banon could see the shape of a business. He founded Elasticsearch (later renamed Elastic) with a model already proven by others: give away the core product, sell enterprise features, support, and hosting. The timing was perfect. The Big Data wave was cresting, and every company suddenly needed to make sense of massive log files, user behavior, sensor data. Elasticsearch was fast, flexible, and most importantly, it didn't require a PhD to deploy.

The growth was organic, viral in the way only developer tools can be. No sales team needed — engineers installed it, it solved their problem, they told other engineers. By 2014, Elastic had raised $70 million in venture funding. The company built the ELK stack — Elasticsearch, Logstash, Kibana — three tools that together formed a complete pipeline for ingesting, searching, and visualizing data. Enterprises bought support contracts and proprietary features through X-Pack: security, monitoring, alerting, machine learning.

Then Amazon showed up.

In 2015, AWS launched Amazon Elasticsearch Service — a fully managed version of Elasticsearch. They took the open-source code, which they were perfectly entitled to do under Apache 2.0, and turned it into a cloud service. Amazon had the distribution, the existing customer relationships, the integration with every other AWS service. Elastic still had the expertise and the community, but now they had to compete with a version of their own product sold by the biggest cloud provider in the world.

Elastic went public in 2018 at a $5 billion valuation. The company was growing — revenues doubled year over year — but the Amazon question hung over everything. AWS was capturing an unknown but substantial share of Elasticsearch workloads. Elastic had built managed cloud offerings, but competing with AWS on AWS infrastructure was asymmetric warfare.

The company tried coexistence. They documented the differences between their cloud service and AWS's. They emphasized innovation speed — Elastic could ship new features to Elasticsearch and the ecosystem faster than Amazon could integrate them. They courted enterprises who wanted vendor support. It worked, but not well enough.

In January 2021, Elastic made the move that had been building for years. They changed the license. Elasticsearch and Kibana would no longer be Apache 2.0. Instead, they would be dual-licensed under the Elastic License 2.0 and Server Side Public License — both designed explicitly to prevent cloud providers from offering them as a service without contributing back or paying.

The open-source community erupted. Elastic claimed they were still open source, just not "Open Source™" by the strict definition. Critics called it a bait-and-switch — building community and adoption on the promise of Apache 2.0, then pulling up the ladder once threatened. The practical effect was clear: Amazon could no longer simply use new versions of Elasticsearch.

Amazon's response was swift and dramatic. They forked Elasticsearch and Kibana at the last Apache-licensed version, creating OpenSearch. They committed significant engineering resources to developing it independently. AWS, Google Cloud, and others rallied around OpenSearch as the true open-source heir. The community split. Some stayed with Elastic, some moved to OpenSearch, some maintained compatibility with both.

Elastic's bet was that their innovation speed and integrated ecosystem would matter more than license purity. They had the brand, the original team, the vision. OpenSearch was a fork, and forks historically struggled to keep pace with their parents.

The bet appears to be working, at least financially. By 2024, Elastic's market cap exceeded $10 billion. Revenue continued growing. The generative AI boom created new use cases for search and vector databases, playing to Elastic's strengths. OpenSearch existed and had adoption, particularly among AWS-native companies, but it hadn't killed Elastic.

What Elastic proved was that open source had always been a means, not an end. When the means stopped serving the end — sustainable business versus cloud giant extraction — they changed it. The developers who felt betrayed weren't wrong about the principle. But Elastic's investors and employees weren't wrong about the practical reality that Apache 2.0 in the cloud era meant subsidizing Amazon's margins.

The company navigated the most treacherous passage for developer-facing infrastructure companies: maintaining legitimacy and momentum while closing the license door just enough to matter. Too early and you never build community. Too late and the cloud giants own your market. Elastic's timing, though contentious, proved viable.

They remain a public company, growing, competing with their own fork, defending the proposition that the original is worth more than the copy — even when both are made of the same code.

---
*Part of All Paths Through a Startup at alexandria.press*