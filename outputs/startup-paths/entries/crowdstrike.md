# CrowdStrike

***The security company that became infrastructure — until a single update brought the world down***

> **Years:** 2011-present

George Kurtz had already sold one cybersecurity company when he started thinking about the next one. In 2011, he was CTO at McAfee, watching the industry miss what seemed obvious: enterprises were moving to the cloud, attackers were getting more sophisticated, and traditional antivirus software — installed locally, updated periodically, signature-based — was fundamentally inadequate for what was coming.

The insight wasn't novel. Every security vendor could see cloud computing arriving. But Kurtz, along with co-founders Dmitri Alperovitch (McAfee's VP of threat research) and Gregg Marston (an entrepreneur and CFO), saw something more specific: endpoint security could be reimagined as a cloud-native platform. Instead of software that lived on each computer, phone, and server — updated in batches, limited by local processing power — they would build a lightweight agent that streamed data to the cloud for analysis. The intelligence would live centrally. Updates would be instant. The system would learn from every endpoint simultaneously.

They called it CrowdStrike. The name evoked both the collective defense (the crowd) and the precision attack (the strike). Kurtz brought operational experience. Alperovitch brought deep expertise in threat intelligence — he'd led the investigations into high-profile breaches and nation-state attacks. Marston brought the business framework. They raised $26 million in Series A funding from Warburg Pincus in 2012, before they had a product.

The founding thesis was platform thinking applied to security. Their Falcon platform would protect endpoints, but the real value was the cloud architecture: CrowdStrike could see attacks across all customers simultaneously, identify patterns, update defenses in real-time. An attack on one customer could protect all customers within seconds. Traditional vendors took weeks or months to update signature files.

The early market was enterprise. CrowdStrike wasn't selling to individuals or small businesses. They were selling to Fortune 500 companies, government agencies, organizations that were already being targeted by sophisticated attackers. The pitch was simple: traditional antivirus is dead, and you know it. Every major breach of the last decade happened at organizations with enterprise security software installed. What you need is cloud-speed intelligence and active protection.

They launched Falcon in 2013. The product was a small agent installed on endpoints — computers, servers, mobile devices — that continuously streamed data to CrowdStrike's cloud platform. The platform analyzed behavior, identified threats, and could respond automatically or alert security teams. Crucially, it didn't rely on known signatures of malware. It looked for malicious behavior patterns. It could catch zero-day attacks — brand new exploits no one had seen before.

The timing was perfect. Between 2013 and 2016, a wave of massive breaches made headlines: Target, Home Depot, Sony Pictures, the Office of Personnel Management. Every breach asked the same question: how did this happen with security software installed? CrowdStrike had an answer: because that software was obsolete.

They also had something else: threat intelligence that made news. Alperovitch built CrowdStrike's intelligence team into a high-profile operation. In 2016, when the Democratic National Committee was hacked, CrowdStrike did the forensics investigation. They publicly attributed the attack to Russian intelligence groups, giving those groups colorful names: Cozy Bear and Fancy Bear. The attribution was controversial — Russia denied involvement, and the public attribution of nation-state attacks was still relatively new — but it made CrowdStrike a household name among people who paid attention to such things.

The business scaled fast. By 2017, they'd raised over $480 million in venture funding. Customers included major financial institutions, healthcare providers, energy companies. The sales motion was direct: let us protect your endpoints, and if there's a breach, let us investigate and respond. Some customers used CrowdStrike to replace legacy antivirus. Others layered it on top. Revenue grew from tens of millions to hundreds of millions.

In June 2019, CrowdStrike went public. The IPO priced at $34 per share, above the expected range. The company raised $612 million. On the first day of trading, shares jumped 71%. The market valued CrowdStrike at over $20 billion. Kurtz rang the NASDAQ opening bell wearing sunglasses indoors, an image that became a minor meme. The company was profitable on a non-GAAP basis and growing revenue over 100% year-over-year.

The product expanded beyond endpoint protection. CrowdStrike added cloud workload protection, identity threat protection, log management, threat intelligence services. The platform strategy was working. Customers who came for endpoint security bought additional modules. The Falcon platform became infrastructure — a core layer of protection that touched everything in an organization's IT environment.

By 2024, CrowdStrike protected endpoints at more than half of the Fortune 500. The stock had risen from its IPO price to over $300 per share. The company was worth over $80 billion. It had become what it set out to be: the dominant next-generation cybersecurity platform, replacing legacy vendors like McAfee and Symantec.

Then came July 19, 2024.

CrowdStrike pushed a routine content update to its Falcon sensor — a small configuration file that updated the threat detection logic. The update contained a defect. On Windows systems, the Falcon sensor crashed on boot. The crash triggered a Windows "blue screen of death" error. The system couldn't start.

Millions of Windows machines around the world went down simultaneously. Airlines grounded flights. Hospitals canceled procedures. Banks closed branches. 911 systems went offline. Broadcasting stopped. The scale was unprecedented — not because of the technical severity, but because CrowdStrike had become infrastructure. When infrastructure fails, everything built on it fails too.

The fix was straightforward but painful: boot each affected machine into safe mode, manually delete the bad update file, reboot. But enterprise environments had millions of machines, many in data centers or remote locations. IT teams spent days working through the recovery. The estimated global economic impact ran into billions of dollars.

CrowdStrike's stock dropped 30% in the weeks after the incident. Lawsuits followed. Delta Air Lines alone claimed $500 million in losses and sued for damages. Customers demanded explanations. How could a content update — not even a software update, just a configuration change — crash systems globally? Why wasn't it tested more carefully? Why was there no staged rollout? Why did the Falcon sensor have kernel-level access that could crash the entire operating system?

The incident exposed the paradox of CrowdStrike's success. Endpoint security software requires deep system access to protect against sophisticated threats. That access creates risk. CrowdStrike had argued for years that cloud-based updates were superior to legacy approaches — faster, more responsive, more effective. But speed creates risk too. The very architecture that made CrowdStrike powerful made its failures catastrophic.

The company responded with apologies, technical explanations, promises of new testing protocols. Kurtz testified before Congress. The long-term business impact remained unclear. Some customers would leave. Others would stay — because switching security vendors is difficult, because breaches are still a bigger risk than outages, because alternatives have their own problems.

CrowdStrike had built what it set out to build: a platform that became critical infrastructure. It learned what infrastructure companies always learn eventually. When you're infrastructure, failure isn't just your problem. It's everyone's problem. And the world notices.

---
*Part of All Paths Through a Startup at alexandria.press*