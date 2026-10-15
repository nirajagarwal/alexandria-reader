# Latent Fragility
## Why Optimized Systems Suddenly Fail

*Alexandria Press · alexandria.press*

---

### Introduction
# Latent Fragility
## Why Optimization Creates Fragility

Most catastrophic failures do not happen because someone was lazy, corrupt, or incompetent. The bridges that shake, the algorithms that liquidate fortunes in minutes, and the platforms that sink to the seabed are usually designed by capable engineers working with verified mathematics and audited materials.

The trouble begins with optimization.

When an engineer, a trader, or a software team optimizes a system, they remove slack. They reduce weight to cut costs, trim latency to beat competitors, or eliminate redundant safety buffers that appear unnecessary during normal operations. On paper, the system becomes more efficient. Under ordinary conditions, it performs reliably.

Slack, however, is not waste. Slack is what absorbs the unexpected.

When slack is removed, a system's tolerance for surprise drops to zero. A microscopic disturbance—a three-millimeter sway in a steel deck, a missing software update on one server, or an eight-bit counter rolling over to zero—is no longer absorbed by the structure. Instead of bending, the system snaps.

This book examines eight cases where competence, precision, and optimization created the exact conditions for collapse. In each instance, the failure was not an accident waiting to happen; it was an architecture engineered to perfection until the world introduced an unmodeled variable.

---

### Chapter 1
# The Resonance of the Crowd
## The Millennium Footbridge (River Thames, London)

At 11:00 AM on Saturday, June 10, 2000, police opened the gates of the Millennium Footbridge, a £18.2 million horizontal suspension crossing connecting St. Paul’s Cathedral to London's Bankside. Within fifteen minutes, two thousand pedestrians were walking simultaneously across the 320-meter aluminum deck. On the 144-meter central span, the structure began sliding sideways, oscillating at a rhythmic cadence of slightly less than once per second with a peak lateral displacement of 70 millimeters. Pedestrians staggered, grabbed handrails, and experienced motion sickness in windless 18°C weather, forcing city authorities to padlock the crossing forty-eight hours later.

The post-mortem conducted by Ove Arup revealed that the bridge’s natural lateral eigenfrequency was exactly 0.8 Hz. A human walking produces a vertical impact at 2.0 Hz, but shifts weight laterally from left to right foot at exactly 1.0 Hz, across a natural biological distribution spanning 0.7 to 1.2 Hz. Engineers had assumed pedestrian footfalls were randomly phased, canceling each other out. But when crowd density passed 0.2 people per square meter, random statistical noise caused a 3-millimeter lateral deck shift. Human vestibular balance reflexes involuntarily forced walkers to widen their stance and step with the deck’s motion to avoid falling, converting inert pedestrians into active pumps injecting 300 Newtons of lateral force at 0.8 Hz.

The architectural competition in 1996 had demanded an unobstructed sightline across the Thames, leading Sir Norman Foster to mandate a 'blade of light' with no vertical towers or overhead cables. To suspend a pedestrian deck across 320 meters without towers, engineers anchored two clusters of 120-millimeter steel cables into concrete abutments under 2,000 tons of horizontal tension, producing an unprecedentedly shallow sag ratio of 1:63. The design satisfied British Standard 5400 across all vertical dead loads, live loads, and aerodynamic wind flutter, yet it remained legally blind to the horizontal plane because no civil code mandated testing lateral human coupling.

The mathematical physics of the bridge deck corresponds directly to the Kuramoto model of coupled non-linear oscillators:

$$\frac{d\theta_{i}}{dt} = \omega_{i} + \frac{K}{N} \sum_{j=1}^{N} \sin(\theta_{j} - \theta_{i})$$

The flexible steel deck functions as the coupling medium ($K$). Each pedestrian is an independent biological oscillator with a baseline frequency ($\omega_i$). When pedestrian density exceeds a critical threshold ($K > K_c$), the system undergoes a spontaneous phase transition, collapsing individual independence into forced mathematical synchrony without central leadership or intent.

Three hundred and thirty-five years earlier, in February 1665, Dutch polymath Christiaan Huygens lay ill in bed observing two pendulum clocks mounted to a single wooden beam. Regardless of their initial starting positions, within thirty minutes the two pendulums swung in exact, synchronized anti-phase. When Huygens moved the clocks to separate walls, the synchronization stopped; the wooden beam had been transmitting imperceptible vibrations, serving as the mechanical coupling medium that modern London engineers unknowingly rebuilt out of 2,000 tons of tensile steel.

Identical Kuramoto dynamics govern biological communication along the Selangor River in Malaysia, where thousands of male fireflies (*Pteroptyx malaccae*) synchronize flash intervals until thirty-meter trees pulse as a single coherent emitter. In human cardiac physiology, 10,000 pacemaker cells in the sinoatrial node couple via electrical gap junctions, depolarizing in phase lock to drive coordinated ventricular contractions. On financial trading floors, high-frequency algorithms monitoring identical order-book latency thresholds synchronize quote cancellations, triggering liquidity flash crashes through the exact feedback loop that shook the Thames.

The physical resolution required two years and £5 million—over a quarter of the bridge’s original budget. The retrofit did not alter Foster’s profile or stiffen the shallow suspension cables. Instead, contractors installed 37 viscous fluid dampers to dissipate lateral motion through silicone fluid resistance and 52 tuned mass dampers to oscillate in counter-phase beneath the aluminum deck. When the bridge reopened on February 22, 2002, four million visitors crossed without detecting a vibration.

---

### Chapter 2
# The Secret Welds of Midtown
## The Citicorp Center Crisis (1978, Manhattan)

To build a fifty-nine-story skyscraper at 601 Lexington Avenue in Midtown Manhattan, structural engineer William LeMessurier had to work around a nineteenth-century church occupying the northwest corner of the lot. St. Peter’s Lutheran Church had agreed to sell its air rights only on the condition that a new sanctuary remain standing on the exact corner footprint, untouched by tower columns. LeMessurier solved the geometry by suspending the 915-foot Citicorp Center nine stories above street level on four massive steel stilts—positioned not at the four corners of the building, but at the midpoint of each outer wall. To transfer wind loads around the cantilevered corners, he wrapped the exterior facade in a skeleton of eight-story, chevron-shaped diagonal steel trusses.

Under standard New York City building codes when the tower opened in May 1977, structural wind calculations were performed assuming winds striking perpendicular to the flat faces of the building. In perpendicular wind regimes, structural loads travel symmetrically down the chevron diagonals into the central stilts. However, LeMessurier's original engineering specification had called for full-penetration welded joints at every chevron splice. During construction in 1976, contractor Bethlehem Steel requested a change order to replace the welded joints with bolted connections using high-strength A325 bolts to save \$250,000 and accelerate fabrication. The change was approved without calculating the effect of quartering winds—gusts striking the building diagonally at 45 degrees.

In June 1978, Diane Hartley, an undergraduate civil engineering student at Princeton University, was writing her senior thesis on the structural geometry of Citicorp Center. When she modeled the chevron truss loads under diagonal wind conditions, her calculations showed that quartering winds placed 40 percent more tensile load on the chevron braces than perpendicular winds:

$$F_{\text{diagonal}} \approx 1.40 \cdot F_{\text{perpendicular}}$$

Hartley contacted LeMessurier's office to resolve what she assumed was an error in her own mathematical model. When LeMessurier personally recalculated the numbers over a weekend in Maine, he discovered that while full-penetration welds could have withstood the diagonal load, the bolted joints would shear at their mechanical limit. A 16-year storm—a hurricane hitting Manhattan every decade and a half—would snap the bolts and topple the 59-story skyscraper into the surrounding neighborhood.

The skyscraper's only active defense was a 400-ton tuned mass damper installed on the 63rd floor—a massive concrete block floating on an oil film, controlled by hydraulic pistons to oppose building sway. LeMessurier calculated that if the tuned mass damper was operating, the building could survive a 55-year storm. But hurricanes routinely knock out regional electrical grids. If high winds severed midtown Manhattan’s power supply, the hydraulic pumps would stall, leaving the building vulnerable to structural failure in a 16-year storm. Meteorological data indicated that the probability of a catastrophic failure was approximately one in sixteen per year during hurricane season.

Rather than waiting for litigation, LeMessurier alerted Citicorp chairman Walter Wriston, the American Red Cross, and the New York City Department of Buildings, and assembled emergency welding crews. Every night between 8:00 PM and 4:00 AM, out of sight of office workers and a newspaper press corps that happened to be on strike that summer, ironworkers climbed through drywall access panels to weld two-inch-thick steel plates over all 212 bolted chevron joints. While the nocturnal welding was still underway in late August 1978, Hurricane Ella moved up the Eastern seaboard with sustained winds of 140 mph, charting directly toward New York Harbor before veering out to sea hours before landfall. By October, the welded plates were complete, giving the tower enough structural reserve to withstand a 700-year storm without power.

---

### Chapter 3
# The Gaussian Mirage
## Long-Term Capital Management (September 1998, Greenwich)

To generate forty-percent annual returns from bond price discrepancies of a single hundredth of a cent, Long-Term Capital Management (LTCM) had to borrow twenty-five dollars for every dollar of capital it held. By the summer of 1998, operating from an unmarked stone office building in Greenwich, Connecticut, the hedge fund managed \$4.7 billion in equity, held balance-sheet assets exceeding \$125 billion, and carried off-balance-sheet derivatives with a notional value of \$1.25 trillion. Its partners were the intellectual aristocracy of quantitative finance: former Salomon Brothers vice chairman John Meriwether, bond trader Eric Rosenfeld, and economists Robert Merton and Myron Scholes, who had received the Nobel Memorial Prize in Economic Sciences ten months earlier for their option-pricing formula.

LTCM’s core strategy was fixed-income convergence arbitrage. The firm identified tiny yield spreads between closely related securities—such as newly issued, liquid 30-year U.S. Treasuries ('on-the-run') and older, slightly less liquid 30-year Treasuries issued six months earlier ('off-the-run'). Because both bonds were backed by the same sovereign guarantee and matured within months of each other, their yields always converged over time. The firm's risk exposure was governed by daily Value-at-Risk (VaR) models assuming asset price fluctuations followed a Gaussian normal distribution, where the probability density of a return deviation $x$ decays exponentially with the square of standard deviation $\sigma$:

$$P(x) = \frac{1}{\sigma \sqrt{2\pi}} \exp\left(-\frac{(x - \mu)^2}{2\sigma^2}\right)$$

Under those Gaussian assumptions, a daily loss exceeding \$35 million was a normal fluctuation, while an outlier beyond five or six standard deviations had a theoretical probability of once in millions of years.

On August 17, 1998, the Russian government devalued the ruble and defaulted on \$40 billion of domestic ruble debt (GKO bonds). In LTCM's correlation matrices, a Russian default was statistically independent of American, Danish, and Japanese bond spreads. In actual markets, global institutional investors panicked and initiated an immediate flight to liquidity. Every trading desk on earth dumped off-the-run bonds simultaneously to buy on-the-run U.S. Treasuries, blowing yield spreads apart across every market in which LTCM held leveraged positions.

On Friday, August 21, 1998, LTCM lost \$553 million in a single trading session—a statistical 'ten-sigma event' that its Gaussian models calculated should never occur in the lifetime of the universe. Financial markets during a panic do not obey independent normal distributions; hidden correlations jump toward 1.0 as every participant crowds toward the same exit door. Because LTCM's positions were too massive to unwind without crashing prices further, rival Wall Street desks began front-running the fund's distressed holdings. In five weeks, LTCM's equity collapsed from \$4.7 billion to \$400 million, pushing its effective leverage ratio past 250-to-1.

On Sunday, September 23, 1998, William McDonough, President of the Federal Reserve Bank of New York, convened the chief executives of fourteen major Wall Street banks on the tenth floor of the New York Fed. Federal Reserve auditors warned the bankers that if LTCM defaulted at the Monday opening bell, the simultaneous forced liquidation of \$1.25 trillion in bilateral derivatives contracts would freeze global interbank clearing. Under regulatory pressure, the consortium injected \$3.625 billion in an emergency private bailout, seizing 90 percent of the fund's equity and liquidating its positions over the next fourteen months.

---

### Chapter 4
# The Vortex of Delcambre
## The Lake Peigneur Inundation (November 20, 1980, Louisiana)

At 5:30 AM on Thursday, November 20, 1980, a twelve-man contract crew aboard Texaco oil rig Wilson Brothers No. 35 was drilling an exploratory well into the muddy bed of Lake Peigneur, a shallow freshwater body in Iberia Parish, Louisiana. The lake covered 1,300 acres and had an average depth of just six to ten feet, surrounded by residential waterfronts, live oak groves, and the Rip Van Winkle botanical gardens. At a drilling depth of approximately 1,245 feet, the drill string seized. When the crew attempted to pull the 14-inch steel drill bit free, a series of loud subterranean pops vibrated up the pipe and the heavy pontoon platform listed sharply toward the water, forcing the toolpusher to order an immediate evacuation.

Thirteen hundred feet directly beneath the lakebed lay the Jefferson Island Diamond Crystal Salt Mine—a vast underground complex of solid halite chambers spanning five levels, supported by unexcavated pillars of rock salt fifty feet wide and eighty feet high. Fifty-five miners were working in the active third and fourth levels that morning. The Texaco engineering team had mapped the drill target using Universal Transverse Mercator (UTM) coordinates instead of the modified Lambert projection grid used by the subterranean mine survey, misaligning the surface rig by roughly four hundred feet. The 14-inch drill bit had punched straight through the ceiling of an excavated salt cavern on Level 3.

Freshwater is an aggressive solvent to sodium chloride ($\text{NaCl}$), capable of dissolving 360 grams of solid salt per liter of water. As lake water entered the 14-inch puncture under a hydrostatic pressure differential exceeding 500 pounds per square inch, turbulent flow scoured the halite walls of the bore, dissolving the opening from fourteen inches to thirty feet within minutes. In the mine tunnels below, electrical lights flashed off as muddy torrents roared into the corridors. Mine electrician Randy LaSalle spotted a six-inch stream of murky lake water pouring around a salt pillar and triggered the emergency evacuation signal—three flashes of the mine lamps. In darkness, all 55 miners rode the slow hoist cage up the 1,300-foot main shaft to the surface twenty minutes before the caverns flooded completely.

As 3.5 billion gallons of lake water drained into the salt dome, the localized suction created a whirlpool a quarter-mile wide across Lake Peigneur. The vortex swallowed the \$5 million drilling derrick, eleven commercial canal barges, a tugboat, a parking lot, and sixty-five acres of the botanical gardens. Water pouring down the mine shafts displaced millions of cubic feet of underground air, firing geysers of compressed air, brine, and mud four hundred feet into the sky through the ventilation shafts. Once the lakebed emptied into the cavern, the twelve-mile Delcambre Canal—which normally drained Lake Peigneur southward into Vermilion Bay and the Gulf of Mexico—reversed direction, pulling brackish ocean water backward into the crater over a temporary 150-foot waterfall for forty-eight hours. When the pressures equalized, the ten-foot-deep freshwater lake had become a two-hundred-foot-deep saltwater bay, and nine of the eleven swallowed barges popped back to the surface like corks.

---

### Chapter 5
# The Silent Overdose
## The Therac-25 Accidents (1985–1987, North America)

In earlier generations of medical linear accelerators—the Therac-6 and Therac-20—physical safety did not depend on computer code. If a hospital technician selected high-energy X-ray mode, heavy electromechanical interlocks physically locked a tungsten-tantalum target and a flattening filter into the path of the 25-megaelectronvolt (MeV) electron beam before the magnetron could fire. When Atomic Energy of Canada Limited (AECL) designed the dual-mode Therac-25 in the early 1980s, engineers eliminated those mechanical interlocks to reduce hardware costs, delegating all safety verification to a 16-bit PDP-11 minicomputer running 20,000 lines of assembly language written by a single programmer.

On the morning of June 3, 1985, a sixty-one-year-old woman entered the Kennestone Regional Oncology Center in Marietta, Georgia, for routine postoperative radiation following a lumpectomy. Placed beneath the Therac-25 treatment head, she felt a searing thermal burn across her chest the instant the machine fired. The clinic’s radiation dosimetry console displayed zero abnormal output. Over the next twenty months, five more patients in Ontario, Washington, and Texas suffered identical catastrophic radiation burns.

The fatal mechanism surfaced on March 21, 1986, at the East Texas Cancer Center in Tyler, Texas. Patient Ray Cox was scheduled for a routine 180-rad electron treatment to his upper back. The technician, who had operated the machine hundreds of times, typed the session parameters rapidly into the VT100 terminal. By muscle memory, she initially typed `x` (for 25 MeV X-ray mode), noticed the mistake immediately, hit the up-arrow key, overwrote the character with `e` (for low-energy electron mode), and pressed Enter—completing the edit in under eight seconds.

Inside the PDP-11 assembly code, keyboard input (`Datent`) and magnet-setting hardware control (`Hand`) ran as concurrent asynchronous tasks sharing unprotected memory variables:
- When the operator first typed `x`, the software began a full eight-second mechanical sequence to set the bending magnets for a raw, high-current 25 MeV beam.
- While the magnets were still moving, the `Datent` routine only checked for keyboard edits if a shared 8-bit boolean flag (`Class3`) was non-zero.
- Every pass through the control loop incremented the 8-bit `Class3` counter by 1. Because an 8-bit unsigned integer holds a maximum value of $2^8 - 1 = 255$, on every 256th tick the counter rolled over to zero (`0x00`).

When the Tyler technician hit Enter during that exact millisecond of 8-bit overflow, the software read `Class3 = 0`, skipped reloading the updated low-energy beam parameters, retracted the tungsten target out of the way, and fired a concentrated, unattenuated 25 MeV raw electron beam straight into Ray Cox's spine. The console flashed an cryptic status line—`MALFUNCTION 54`—which the operator manual defined simply as a minor "dose input 2" discrepancy. Believing no radiation had been delivered, the technician pressed `P` (Proceed) twice more. Cox received roughly 25,000 rads in three microsecond bursts and died five months later of radiation-induced paralysis.

---

### Chapter 6
# The Shear of Gandsfjorden
## The Sleipner A Platform Collapse (August 23, 1991, Norway)

Before the concrete gravity base of the Sleipner A offshore gas platform was towed into Norway's Gandsfjorden in August 1991, finite element models run by Norwegian Contractors displayed a smooth blue stress contour across its twenty-four ballast cells. Modeled in NASTRAN—the aerospace structural analysis package originally developed for NASA—the simulation predicted that during submergence to 65 meters, the concrete cell junctions would experience a maximum shear stress of 1.2 megapascals, well below the concrete's 2.0-megapascal design limit.

At 5:00 AM on Friday, August 23, 1991, the 57,000-ton honeycombed concrete raft was undergoing a controlled test submergence in the calm fjord near Stavanger to prepare for mating with its 40,000-ton topside steel deck. As ballast water filled the outer cylinders, the hydrostatic pressure differential between the flooded exterior cells and the dry interior utility shafts climbed to 650 kilopascals—roughly 65 metric tons of water pressure per square meter of wall surface.

At 5:49 AM, a dull bang echoed up the hollow shafts. At a depth of 65 meters, one of the internal triangular spaces formed where three cylindrical concrete shells met—a "tri-cell"—sheared completely through its 55-centimeter-thick concrete wall. Cold fjord water roared into the buoyancy cells at more than one thousand metric tons per minute, overwhelming the bilge pumps by an order of magnitude. The fourteen crew members scrambled onto a standby tugboat. Eighteen minutes later, the \$700 million structure vanished beneath the surface and struck the granite floor of Gandsfjorden 220 meters below, imploding its remaining buoyancy chambers with an acoustic shock wave that registered 3.0 on the Richter scale at seismic stations in Bergen.

The post-mortem investigation by SINTEF and the Norwegian Petroleum Directorate traced the collapse to a single finite element meshing approximation. Because the 24-cell platform geometry was computationally massive for 1990 workstations, engineers had modeled the acute 60-degree intersections of the tri-cell walls using coarse, skewed eight-node hexahedral elements. In linear elasticity, sharp re-entrant corners concentrate shear and tensile stress:

$$\tau_{\text{actual}} = K_{t} \cdot \tau_{\text{nominal}}$$

Because the coarse finite element mesh lacked sufficient nodes across the wall thickness at the corner junction, the mathematical solver smoothed away the local stress peak, under-reporting the true shear force by 47 percent. Simultaneously, the blueprint detailing the steel T-headed shear reinforcement bars inside the tri-cell corner specified bars that were anchored too shallowly to resist the splitting tension once water penetrated a hairline crack. In physical reality, the wall experienced 3.8 megapascals of shear—nearly double its unreinforced capacity. When Norwegian Contractors cast the replacement Sleipner A base in 1992, engineers verified the corner junctions with hand-calculated truss models and packed the tri-cell intersections with dense stirrup reinforcement.

---

### Chapter 7
# The Forty-Five Minute Liquidation
## The Knight Capital Algorithmic Crash (August 1, 2012, New Jersey)

At 9:30 AM on Wednesday, August 1, 2012, the opening bell rang at the New York Stock Exchange. Across the Hudson River in Jersey City, Knight Capital Group—the largest market-making firm in American equities, executing 17 percent of all volume on the NYSE and NASDAQ—switched on its automated routing engines. Within forty-five seconds, trading desks across Wall Street noticed violent anomalies across 154 stocks. Shares of companies like Wizzard Software and Harley-Davidson were trading thousands of times per minute, oscillating wildly. Knight Capital's servers were firing 4,000 orders per second into the market—buying shares at the higher ask price and milliseconds later selling them back at the lower bid price, losing pennies on every share thousands of times a second.

A week earlier, Knight's software team had modified its Smart Market Access Routing System (`SMARS`) to connect to the NYSE’s new Retail Liquidity Program. To clean up legacy code during the update, programmers repurposed an old configuration flag that had previously activated an eight-year-old, dead test algorithm named `Power Peg`. Written in 2003 to stress-test institutional execution algorithms in staging environments, `Power Peg` was intentionally designed to move stock prices by buying and selling aggressively without price limits, incrementing a cumulative share counter only when a confirmation message returned from a defunct internal component. Because that verification component had been removed in 2005, `Power Peg` could never receive a "stop" signal.

On the evening of July 27, 2012, a systems administrator manually deployed the updated `SMARS` binary onto Knight’s eight production servers—and accidentally skipped the eighth server. For four days the dormant bug sat unnoticed. When the NYSE Retail Liquidity flag flipped live at 9:30 AM on August 1, servers 1 through 7 routed orders normally. Server 8 read the same flag, woke up the dead `Power Peg` routine from 2003, and entered an infinite loop.

Knight’s engineers had no master kill switch to isolate a single routing server. When technicians realized Server 8 was misbehaving at 9:58 AM, they rolled back the new `SMARS` software across the other seven servers—inadvertently activating the dormant `Power Peg` code on all eight production servers simultaneously. Before technicians physically pulled the network plugs at 10:14 AM, Knight had executed four million trades across 397 million shares, accumulating \$3.5 billion in long positions and \$3.15 billion in short positions.

To avoid defaulting at the Depository Trust & Clearing Corporation, Knight had to liquidate the entire \$6.65 billion unintended portfolio before the closing bell, realizing a cash loss of \$440 million in forty-four minutes—a burn rate of \$10 million per minute that wiped out the firm's \$365 million equity cushion before sunset.

---

### Chapter 8
# The Admiral’s Folly
## The Swedish Warship Vasa (August 10, 1628, Stockholm)

When marine archaeologists raised the intact oak hull of the Swedish warship *Vasa* from thirty-two meters of anoxic Baltic mud in April 1961, the sixty-four gun carriages were still in place and the lower gunports stood wide open. Three hundred and thirty-three years earlier, on the afternoon of Sunday, August 10, 1628, the 69-meter flagship of King Gustavus Adolphus had cast off from the royal quay below Tre Kronor castle in Stockholm Harbor before ten thousand spectators and foreign ambassadors. Carrying 1,210 tons of displacement and two full enclosed decks of heavy 24-pounder bronze cannon, the ship drifted out of the lee of the Södermalm cliffs, caught a four-knot summer breeze, heeled once to port, recovered, heeled a second time in a light gust near Beckholmen island, and buried her open lower gunports beneath the water. She sank in thirty minutes, 1,300 meters into her maiden voyage.

The hydrostatic autopsy performed on the salvaged hull revealed a violation of metacentric stability. When a floating hull rolls through a small angle $\phi$, the center of buoyancy $B$ shifts laterally as the submerged hull cross-section changes shape. The vertical line of upward buoyant force intersects the ship's centerline at a point called the metacenter $M$. For a ship to generate a positive righting lever $\text{GZ}$ that pushes it back upright, the metacenter $M$ must sit well above the ship's center of gravity $G$:

$$\text{GZ} = \text{GM} \cdot \sin\phi$$

While *Vasa*'s keel was already laid in 1626 as a single-deck vessel, King Gustavus Adolphus—then campaigning in Poland during the Thirty Years' War—sent letters ordering the shipyard to add a second enclosed gun deck armed with thirty-six-hundred-pound bronze cannon. Master Dutch shipwright Henrik Hybertsson fell ill and died in 1627 without leaving written hydrostatic drawings, and his assistant Hein Jacobsson completed the tall superstructure onto a narrow, flat-bottomed hull whose beam was too slender for the lofty armament. To lower the center of gravity $G$, builders packed 120 tons of cobble ballast into the bilge, filling the hold to capacity; adding a single additional ton of stone would have dragged the lower gunport sills beneath the harbor surface at rest.

Two weeks before the launch, Vice Admiral Klas Fleming supervised a traditional dockside inclining test (`luta`). Thirty sailors ran in unison from port to starboard across the upper deck while Fleming watched the roll amplitude. On the third pass, the hull lurched so deeply toward the pier that Fleming shouted for the men to stop running before the warship capsized at its moorings. Captain Söfring Hansson remarked that the ship was tender in the bottom, but with the King dispatching impatient letters from Prussia demanding his flagship at the front immediately, neither Fleming nor Jacobsson reported the failed stability test to the Royal Council.

Modern laser reconstructions of the 1961 hull measured *Vasa*'s metacentric height $\text{GM}$ at just 12 centimeters (4.8 inches)—less than a tenth of the 1.2 meters required for an armed galleon. A four-knot breeze exerting modest pressure against the topsails produced a 10-degree heel, submerging the lower gunport sills located 1.4 meters above the waterline and pouring thirty tons of seawater per minute onto the lower gundeck.

---

