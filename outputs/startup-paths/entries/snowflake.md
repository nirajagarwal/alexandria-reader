# Snowflake

***The data warehouse that made the cloud inevitable***

> **Years:** 2012-present

In 2012, three engineers sat in a Starbucks in San Mateo sketching out a problem that nearly everyone in enterprise software had learned to live with: data warehouses were terrible. Benoit Dageville, Thierry Cruanes, and Marcin Żukowski had spent years building database systems at Oracle and other established companies. They knew the architecture intimately. They also knew it was fundamentally broken for what came next.

The existing model—pioneered by Teradata, perfected by Oracle, extended by newer players like Vertica—required companies to buy hardware, install software, tune performance, manage capacity, and pray they'd guessed right about future data volumes. Amazon Redshift had just launched, promising cloud-based data warehousing, but it was essentially the old architecture transplanted to AWS. You still had to choose cluster sizes. You still paid whether you were running queries or not. Storage and compute were still coupled. The cloud providers were winning on convenience, not on architecture.

The three founders saw something different. What if you built a data warehouse designed for the cloud from first principles? What if storage and compute were completely separated? What if you could scale them independently? What if you paid only for what you used, like turning on a light switch? What if multiple users could query the same data simultaneously without performance degradation?

They started coding. No business plan. No market research. Just deep conviction that the architecture was solvable and that once solved, it would be obvious. They called it Snowflake—a name that captured both the uniqueness of each query and the idea of infinite scale through aggregation.

The technical challenges were immense. Separating storage and compute sounds simple until you consider that databases are fast because they keep data close to processing. Making a fully separated system perform at enterprise scale required innovations in caching, metadata management, query optimization, and concurrency control. They built their own columnar storage format. They invented a multi-cluster shared data architecture. They created a system where compute resources could spin up in seconds, run a query, and disappear.

By 2014, they had something that worked. Mike Speiser at Sutter Hill Ventures became their first institutional investor, leading a $5 million seed round. Speiser had a reputation for backing technical founders building infrastructure. He saw what they saw: this wasn't incrementally better, it was categorically different.

The challenge was that categorically different meant selling something that didn't fit existing procurement categories. Early customers had to understand why paying per-second of compute time was better than paying for reserved capacity. They had to trust a startup with their data warehouse—the system that powered their analytics, their reporting, their business intelligence. They had to believe that this strange architecture would actually perform.

The founders recruited Bob Muglia, former Microsoft executive who had run SQL Server and Azure, as CEO. Muglia brought enterprise credibility and sales discipline. But he also recognized that the product sold itself if you could get buyers to try it. Snowflake offered free trials and proof-of-concepts. The performance was undeniable. Queries that took hours on legacy systems ran in minutes. Systems that required weeks of capacity planning could be spun up instantly.

Capital One became an early enterprise customer. Then Informatica. The pattern was consistent: data engineers would start with a pilot project, experience the architecture, and advocate internally for broader adoption. IT departments discovered they could eliminate the capacity planning nightmare. Finance departments discovered they were paying for actual usage rather than theoretical capacity.

By 2017, Snowflake was processing over 25 million queries daily. Revenue was growing 300% year-over-year. The company raised $263 million at a $1.5 billion valuation. The data warehouse market, long considered mature and dominated by established players, was being disrupted by a startup with a fundamentally different approach.

The competitive response validated the architecture. AWS launched Athena and improved Redshift. Google promoted BigQuery. Microsoft built Azure Synapse. Every cloud provider needed an answer to Snowflake. But Snowflake had advantages: it ran on all three major clouds, making it the neutral choice for multi-cloud strategies. Its architecture was designed for the cloud rather than adapted to it. And it had accumulated years of operational knowledge about making separated storage and compute actually work at scale.

In 2019, Frank Slootman became CEO. Slootman had previously led Data Domain and ServiceNow, taking both from growth stage to public companies. His arrival signaled maturity and ambition. Under Slootman, Snowflake accelerated. The company expanded beyond data warehousing into data lakes, data sharing, and data marketplace features. The vision became not just a better warehouse, but a data cloud where organizations could store, process, and share data without moving it.

In September 2020, Snowflake went public in the largest software IPO in history. The stock priced at $120, opened at $245, and closed the first day at $253. The company was valued at over $70 billion—more than established database giants. Warren Buffett's Berkshire Hathaway bought nearly $1 billion in shares, a rare tech investment for the legendary value investor.

The valuation shocked observers. For a company selling data warehousing—a category that seemed commodified—to command such a premium required belief that this was something more. That belief was in the architecture. The cloud wasn't just a new deployment model. It was a new foundation that required new designs. Snowflake proved that rebuilding from first principles could create not just better products but new markets.

Today Snowflake processes hundreds of millions of queries daily for thousands of customers. The company that three engineers sketched in a coffee shop became the template for cloud-native data infrastructure: consumption-based pricing, separated compute and storage, multi-cloud by design. The data warehouse became elastic, instant, and inevitable.

---
*Part of All Paths Through a Startup at alexandria.press*