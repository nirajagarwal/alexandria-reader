#!/usr/bin/env python3
"""
Alexandria Press - Programmatic Vector SVG Book Cover Generator
Generates mathematically precise, publication-grade SVG covers (1600x2400) for all volumes,
along with favicons, web manifest, and OpenGraph social preview assets.
"""

import os
import math

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COVERS_DIR = os.path.join(BASE_DIR, "assets", "covers")
os.makedirs(COVERS_DIR, exist_ok=True)

VOLUMES = [
    {
        "id": "non-linear-engines",
        "title": "Non-Linear Engines",
        "subtitle": "Structural Mechanics of Asymmetric Enterprise Creation",
        "category": "Startups & Strategy",
        "vol": "Volume I",
        "bg": "#1a140e",
        "card_bg": "#241b12",
        "accent": "#d97706",
        "accent_dim": "rgba(217, 119, 6, 0.18)",
        "accent_glow": "rgba(217, 119, 6, 0.35)",
        "fg": "#faf9f6",
        "muted": "#a8a29e",
        "theme": "star-graph"
    },
    {
        "id": "latent-fragility",
        "title": "Latent Fragility",
        "subtitle": "Forensic Post-Mortems of Optimal Systems That Collapsed",
        "category": "Systemic Failure & Risk",
        "vol": "Volume II",
        "bg": "#0f172a",
        "card_bg": "#1e293b",
        "accent": "#6366f1",
        "accent_dim": "rgba(99, 102, 241, 0.18)",
        "accent_glow": "rgba(99, 102, 241, 0.35)",
        "fg": "#f8fafc",
        "muted": "#94a3b8",
        "theme": "bifurcation"
    },
    {
        "id": "singular-minds",
        "title": "Singular Minds",
        "subtitle": "Forensic Dissections of Anomalous Cognitive Architectures",
        "category": "Cognitive Architecture",
        "vol": "Volume III",
        "bg": "#062828",
        "card_bg": "#0c3b3b",
        "accent": "#14b8a6",
        "accent_dim": "rgba(20, 184, 166, 0.18)",
        "accent_glow": "rgba(20, 184, 166, 0.35)",
        "fg": "#f0fdfa",
        "muted": "#99f6e4",
        "theme": "sheaf-manifold"
    },
    {
        "id": "radical-subtraction",
        "title": "Radical Subtraction",
        "subtitle": "The Neuroscience and Information Theory of the Silent Contemplatives",
        "category": "Apophatic Contemplation",
        "vol": "Volume IV",
        "bg": "#121212",
        "card_bg": "#1c1c1e",
        "accent": "#a1a1aa",
        "accent_dim": "rgba(161, 161, 170, 0.18)",
        "accent_glow": "rgba(161, 161, 170, 0.35)",
        "fg": "#f4f4f5",
        "muted": "#71717a",
        "theme": "apophatic-void"
    },
    {
        "id": "liminal-thresholds",
        "title": "Liminal Thresholds",
        "subtitle": "Forensic Investigations of Phenomena That Defied Scientific Orthodoxy",
        "category": "Anomalous Physics",
        "vol": "Volume V",
        "bg": "#0b192c",
        "card_bg": "#1e3e62",
        "accent": "#38bdf8",
        "accent_dim": "rgba(56, 189, 248, 0.18)",
        "accent_glow": "rgba(56, 189, 248, 0.35)",
        "fg": "#f0f9ff",
        "muted": "#7dd3fc",
        "theme": "soliton-shock"
    },
    {
        "id": "the-autonomous-engine",
        "title": "The Autonomous Engine",
        "subtitle": "Structural Control Systems of Human Physiology",
        "category": "Physiology & Cybernetics",
        "vol": "Volume VI",
        "bg": "#240a0a",
        "card_bg": "#361212",
        "accent": "#ef4444",
        "accent_dim": "rgba(239, 68, 68, 0.18)",
        "accent_glow": "rgba(239, 68, 68, 0.35)",
        "fg": "#fef2f2",
        "muted": "#fca5a5",
        "theme": "cybernetic-loop"
    },
    {
        "id": "elemental-asymmetries",
        "title": "Elemental Asymmetries",
        "subtitle": "The Geopolitical Thermodynamics of Twelve Atoms",
        "category": "Material Geopolitics",
        "vol": "Volume VII",
        "bg": "#1c1917",
        "card_bg": "#292524",
        "accent": "#eab308",
        "accent_dim": "rgba(234, 179, 8, 0.18)",
        "accent_glow": "rgba(234, 179, 8, 0.35)",
        "fg": "#fafaf9",
        "muted": "#d6d3d1",
        "theme": "quantum-lattice"
    },
    {
        "id": "alexandria-manifesto",
        "title": "Alexandria Manifesto",
        "subtitle": "Principles of the Living Machine-Synthesized Library",
        "category": "Platform & Philosophy",
        "vol": "Special Edition",
        "bg": "#291809",
        "card_bg": "#3d240e",
        "accent": "#fbbf24",
        "accent_dim": "rgba(251, 191, 36, 0.18)",
        "accent_glow": "rgba(251, 191, 36, 0.35)",
        "fg": "#fffbeb",
        "muted": "#fde68a",
        "theme": "golden-spiral"
    }
]

def generate_geometry(theme, accent, glow):
    cx, cy = 800, 1380
    
    if theme == "star-graph":
        nodes = []
        lines = []
        r_outer = 380
        num_spokes = 24
        for i in range(num_spokes):
            angle = (i * 2 * math.pi) / num_spokes
            ox = cx + r_outer * math.cos(angle)
            oy = cy + r_outer * math.sin(angle)
            ctrl_r = 180
            ctrl_x = cx + ctrl_r * math.cos(angle + 0.3)
            ctrl_y = cy + ctrl_r * math.sin(angle + 0.3)
            lines.append(f'<path d="M {cx} {cy} Q {ctrl_x} {ctrl_y} {ox} {oy}" stroke="{accent}" stroke-width="1.8" fill="none" opacity="0.6"/>')
            nodes.append(f'<circle cx="{ox}" cy="{oy}" r="4.5" fill="{accent}" opacity="0.85"/>')
            if i % 3 == 0:
                nxt_angle = ((i + 7) * 2 * math.pi) / num_spokes
                nx = cx + r_outer * math.cos(nxt_angle)
                ny = cy + r_outer * math.sin(nxt_angle)
                lines.append(f'<path d="M {ox} {oy} Q {cx} {cy} {nx} {ny}" stroke="{accent}" stroke-width="0.9" fill="none" opacity="0.25"/>')
        
        hub = f'''
            <circle cx="{cx}" cy="{cy}" r="42" fill="{accent}" opacity="0.12"/>
            <circle cx="{cx}" cy="{cy}" r="22" fill="{accent}" opacity="0.3"/>
            <circle cx="{cx}" cy="{cy}" r="9" fill="{accent}"/>
        '''
        return f'<g class="emblem-star">{"".join(lines)}{"".join(nodes)}{hub}</g>'

    elif theme == "bifurcation":
        curves = []
        for j in range(-7, 8):
            pts = []
            y_base = cy + j * 38
            for x in range(300, 1301, 20):
                dx = (x - cx) / 280
                decay = math.exp(-dx * dx)
                freq = 0.025 + abs(j) * 0.003
                bifurc = 1.0 + (1.2 if x > cx else 0.0) * ((x - cx) / 500)
                y = y_base + math.sin(x * freq) * 45 * decay * bifurc
                pts.append(f"{x},{y:.1f}")
            pts_str = " ".join(pts)
            op = max(0.15, 0.75 - abs(j) * 0.08)
            curves.append(f'<polyline points="{pts_str}" stroke="{accent}" stroke-width="1.6" fill="none" opacity="{op}"/>')
        
        cross_line = f'<line x1="{cx}" y1="{cy-320}" x2="{cx}" y2="{cy+320}" stroke="{accent}" stroke-width="1" stroke-dasharray="6,6" opacity="0.4"/>'
        return f'<g class="emblem-bifurcation">{"".join(curves)}{cross_line}</g>'

    elif theme == "sheaf-manifold":
        paths = []
        for step in range(16):
            r = 90 + step * 20
            rot = step * 11
            paths.append(f'''
                <ellipse cx="{cx}" cy="{cy}" rx="{r * 1.5}" ry="{r * 0.72}" 
                         transform="rotate({rot} {cx} {cy})" 
                         stroke="{accent}" stroke-width="1.3" fill="none" opacity="{0.18 + step * 0.04}"/>
            ''')
        core = f'<circle cx="{cx}" cy="{cy}" r="6" fill="{accent}" opacity="0.9"/>'
        return f'<g class="emblem-manifold">{"".join(paths)}{core}</g>'

    elif theme == "apophatic-void":
        circles = []
        for idx in range(18, 0, -1):
            r = idx * 21
            op = 0.04 + (18 - idx) * 0.045
            stroke_w = 1.2 if idx % 2 == 0 else 0.8
            circles.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke="{accent}" stroke-width="{stroke_w}" fill="none" opacity="{op}"/>')
        singularity = f'<circle cx="{cx}" cy="{cy}" r="3" fill="{accent}" opacity="0.95"/>'
        cross_h = f'<line x1="{cx-360}" y1="{cy}" x2="{cx+360}" y2="{cy}" stroke="{accent}" stroke-width="0.75" opacity="0.25"/>'
        cross_v = f'<line x1="{cx}" y1="{cy-360}" x2="{cx}" y2="{cy+360}" stroke="{accent}" stroke-width="0.75" opacity="0.25"/>'
        return f'<g class="emblem-void">{"".join(circles)}{cross_h}{cross_v}{singularity}</g>'

    elif theme == "soliton-shock":
        curves = []
        for k in range(-6, 7):
            pts = []
            y_base = cy + k * 28
            for x in range(320, 1281, 15):
                dx = (x - cx) / 120
                sech = 1.0 / math.cosh(dx * 1.4)
                soliton = (sech * sech) * 110 * math.exp(-abs(k) * 0.22)
                y = y_base - soliton
                pts.append(f"{x},{y:.1f}")
            pts_str = " ".join(pts)
            op = max(0.18, 0.85 - abs(k) * 0.1)
            curves.append(f'<polyline points="{pts_str}" stroke="{accent}" stroke-width="1.8" fill="none" opacity="{op}"/>')
        shock_pts = []
        for x in range(400, 1201, 20):
            dx = (x - cx) / 220
            sy = cy - 160 + dx * dx * 75
            shock_pts.append(f"{x},{sy:.1f}")
        shock = f'<polyline points="{" ".join(shock_pts)}" stroke="{accent}" stroke-width="2.2" stroke-dasharray="4,6" fill="none" opacity="0.6"/>'
        return f'<g class="emblem-soliton">{"".join(curves)}{shock}</g>'

    elif theme == "cybernetic-loop":
        loops = []
        for r_mod in range(-4, 5):
            w = 260 + r_mod * 18
            h = 170 + r_mod * 12
            op = max(0.15, 0.7 - abs(r_mod) * 0.1)
            loops.append(f'<ellipse cx="{cx-120}" cy="{cy}" rx="{w}" ry="{h}" transform="rotate(-25 {cx-120} {cy})" stroke="{accent}" stroke-width="1.4" fill="none" opacity="{op}"/>')
            loops.append(f'<ellipse cx="{cx+120}" cy="{cy}" rx="{w}" ry="{h}" transform="rotate(25 {cx+120} {cy})" stroke="{accent}" stroke-width="1.4" fill="none" opacity="{op}"/>')
        center = f'''
            <circle cx="{cx}" cy="{cy}" r="32" fill="{accent}" opacity="0.15"/>
            <circle cx="{cx}" cy="{cy}" r="6" fill="{accent}" opacity="0.9"/>
        '''
        return f'<g class="emblem-cybernetic">{"".join(loops)}{center}</g>'

    elif theme == "quantum-lattice":
        hexagons = []
        s = 48
        h_step = s * math.sqrt(3)
        v_step = s * 1.5
        for row in range(-4, 5):
            for col in range(-4, 5):
                hx = cx + col * h_step + (h_step / 2 if row % 2 != 0 else 0)
                hy = cy + row * v_step
                dist = math.hypot(hx - cx, hy - cy)
                if dist < 320:
                    pts = []
                    for vertex in range(6):
                        angle = (vertex * math.pi) / 3 - math.pi / 6
                        vx = hx + s * 0.55 * math.cos(angle)
                        vy = hy + s * 0.55 * math.sin(angle)
                        pts.append(f"{vx:.1f},{vy:.1f}")
                    op = max(0.12, 0.65 - (dist / 320) * 0.5)
                    hexagons.append(f'<polygon points="{" ".join(pts)}" stroke="{accent}" stroke-width="1.2" fill="none" opacity="{op:.2f}"/>')
        orbitals = []
        for r_orb in [90, 190, 290]:
            orbitals.append(f'<circle cx="{cx}" cy="{cy}" r="{r_orb}" stroke="{accent}" stroke-width="1.5" stroke-dasharray="8,10" fill="none" opacity="0.45"/>')
        return f'<g class="emblem-lattice">{"".join(hexagons)}{"".join(orbitals)}</g>'

    elif theme == "golden-spiral":
        pts = []
        turns = 4.2
        a = 9.0
        b = 0.30635
        total_steps = 220
        for i in range(total_steps):
            theta = (i / total_steps) * turns * 2 * math.pi
            r = a * math.exp(b * theta)
            if r > 380:
                break
            px = cx + r * math.cos(theta)
            py = cy + r * math.sin(theta)
            pts.append(f"{px:.1f},{py:.1f}")
        spiral = f'<polyline points="{" ".join(pts)}" stroke="{accent}" stroke-width="2.6" fill="none" opacity="0.85"/>'
        rays = []
        for ray_idx in range(12):
            ray_ang = (ray_idx * 2 * math.pi) / 12
            rx = cx + 360 * math.cos(ray_ang)
            ry = cy + 360 * math.sin(ray_ang)
            rays.append(f'<line x1="{cx}" y1="{cy}" x2="{rx:.1f}" y2="{ry:.1f}" stroke="{accent}" stroke-width="0.8" opacity="0.2"/>')
        return f'<g class="emblem-spiral">{"".join(rays)}{spiral}<circle cx="{cx}" cy="{cy}" r="4" fill="{accent}"/></g>'

    return ""

def create_book_svg(vol):
    title = vol["title"]
    subtitle = vol["subtitle"]
    cat = vol["category"]
    vol_num = vol["vol"]
    bg = vol["bg"]
    card_bg = vol["card_bg"]
    accent = vol["accent"]
    fg = vol["fg"]
    muted = vol["muted"]
    geom = generate_geometry(vol["theme"], accent, vol["accent_glow"])
    
    sub_words = subtitle.split()
    sub_line1 = []
    sub_line2 = []
    sub_target = 38
    cur_len = 0
    for w in sub_words:
        if cur_len + len(w) < sub_target:
            sub_line1.append(w)
            cur_len += len(w) + 1
        else:
            sub_line2.append(w)
    
    sub_line1_str = " ".join(sub_line1)
    sub_line2_str = " ".join(sub_line2)

    sub_line2_tag = ""
    if sub_line2_str:
        sub_line2_tag = '<text x="800" y="625" font-family="\'Literata\', Georgia, serif" font-size="28" font-weight="300" font-style="italic" fill="' + muted + '">' + sub_line2_str + '</text>'

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 2400" width="1600" height="2400">
  <defs>
    <linearGradient id="bg-grad-{vol['id']}" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{card_bg}" stop-opacity="0.95"/>
      <stop offset="60%" stop-color="{bg}" stop-opacity="1.0"/>
      <stop offset="100%" stop-color="{bg}" stop-opacity="1.0"/>
    </linearGradient>
    <radialGradient id="halo-{vol['id']}" cx="50%" cy="58%" r="42%">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0.22"/>
      <stop offset="60%" stop-color="{accent}" stop-opacity="0.04"/>
      <stop offset="100%" stop-color="{accent}" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <rect width="1600" height="2400" fill="url(#bg-grad-{vol['id']})"/>
  <rect width="1600" height="2400" fill="url(#halo-{vol['id']})"/>

  <rect x="76" y="76" width="1448" height="2248" fill="none" stroke="{accent}" stroke-width="1.5" opacity="0.35"/>
  <rect x="92" y="92" width="1416" height="2216" fill="none" stroke="{accent}" stroke-width="0.75" opacity="0.2"/>

  <g stroke="{accent}" stroke-width="1.5" opacity="0.6">
    <path d="M 68 116 L 68 68 L 116 68" fill="none"/>
    <path d="M 1532 116 L 1532 68 L 1484 68" fill="none"/>
    <path d="M 68 2284 L 68 2332 L 116 2332" fill="none"/>
    <path d="M 1532 2284 L 1532 2332 L 1484 2332" fill="none"/>
  </g>

  <g text-anchor="middle" font-family="'Inter', -apple-system, BlinkMacSystemFont, sans-serif">
    <text x="800" y="210" font-size="20" font-weight="700" letter-spacing="9" fill="{accent}" opacity="0.95">ALEXANDRIA PRESS</text>
    <text x="800" y="250" font-size="13" font-weight="500" letter-spacing="4" fill="{muted}" opacity="0.75">{vol_num.upper()} · {cat.upper()}</text>
    <line x1="680" y1="285" x2="920" y2="285" stroke="{accent}" stroke-width="1" opacity="0.35"/>
  </g>

  <g text-anchor="middle">
    <text x="800" y="490" font-family="'Literata', Georgia, serif" font-size="78" font-weight="700" letter-spacing="-0.5" fill="{fg}">
      {title}
    </text>
    <text x="800" y="575" font-family="'Literata', Georgia, serif" font-size="28" font-weight="300" font-style="italic" fill="{muted}">
      {sub_line1_str}
    </text>
    {sub_line2_tag}
  </g>

  {geom}

  <g text-anchor="middle" font-family="'Inter', -apple-system, BlinkMacSystemFont, sans-serif">
    <line x1="620" y1="2160" x2="980" y2="2160" stroke="{accent}" stroke-width="1" opacity="0.35"/>
    <text x="800" y="2210" font-size="13" font-weight="600" letter-spacing="5" fill="{muted}" opacity="0.8">LIVING LIBRARY ARCHITECTURE</text>
    <text x="800" y="2246" font-size="11" font-weight="400" letter-spacing="3" fill="{muted}" opacity="0.55">ALEXANDRIA.PRESS · AUTONOMOUS EDITION</text>
  </g>
</svg>'''
    return svg

def generate_favicon_svg():
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">
  <defs>
    <linearGradient id="fav-bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#241b12"/>
      <stop offset="100%" stop-color="#120e0a"/>
    </linearGradient>
    <linearGradient id="fav-gold" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fbbf24"/>
      <stop offset="100%" stop-color="#d97706"/>
    </linearGradient>
  </defs>
  <rect width="128" height="128" rx="28" fill="url(#fav-bg)"/>
  <rect x="6" y="6" width="116" height="116" rx="22" fill="none" stroke="#d97706" stroke-width="1.5" opacity="0.4"/>
  <g stroke="url(#fav-gold)" stroke-width="2.8" stroke-linecap="round" fill="none">
    <path d="M 64 22 L 32 98 L 96 98 Z" stroke-linejoin="round"/>
    <line x1="42" y1="74" x2="86" y2="74"/>
    <line x1="64" y1="22" x2="64" y2="74" stroke-width="1.8" opacity="0.65"/>
    <circle cx="64" cy="22" r="5" fill="url(#fav-gold)"/>
    <circle cx="64" cy="74" r="3.5" fill="url(#fav-gold)"/>
  </g>
</svg>'''

def generate_og_image_svg():
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">
  <defs>
    <linearGradient id="og-bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1a140e"/>
      <stop offset="50%" stop-color="#120e0a"/>
      <stop offset="100%" stop-color="#0a0806"/>
    </linearGradient>
    <radialGradient id="og-glow" cx="80%" cy="40%" r="50%">
      <stop offset="0%" stop-color="#d97706" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="#d97706" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#og-bg)"/>
  <rect width="1200" height="630" fill="url(#og-glow)"/>

  <rect x="36" y="36" width="1128" height="558" fill="none" stroke="#d97706" stroke-width="1.5" opacity="0.35"/>
  <rect x="48" y="48" width="1104" height="534" fill="none" stroke="#d97706" stroke-width="0.75" opacity="0.2"/>

  <g font-family="'Inter', -apple-system, sans-serif">
    <text x="96" y="135" font-size="16" font-weight="700" letter-spacing="8" fill="#d97706">ALEXANDRIA PRESS</text>
    <text x="96" y="165" font-size="13" font-weight="500" letter-spacing="3" fill="#a8a29e">THE LIVING MACHINE-SYNTHESIZED LIBRARY</text>
  </g>

  <g font-family="'Literata', Georgia, serif" fill="#faf9f6">
    <text x="96" y="275" font-size="58" font-weight="700" letter-spacing="-1">Autonomous Synthesis</text>
    <text x="96" y="345" font-size="58" font-weight="700" letter-spacing="-1">for High-Entropy Reality</text>
  </g>

  <g font-family="'Inter', -apple-system, sans-serif" fill="#a8a29e">
    <text x="96" y="415" font-size="19" font-weight="400">
      Eight forensic volumes across physics, cognitive architectures, systemic collapse,
    </text>
    <text x="96" y="445" font-size="19" font-weight="400">
      material constraints, and non-linear leverage. Digital-native two-column paged reader.
    </text>
  </g>

  <g font-family="'Inter', -apple-system, sans-serif" font-size="12" font-weight="600" letter-spacing="2">
    <rect x="96" y="495" width="170" height="34" rx="4" fill="#241b12" stroke="#d97706" stroke-width="1" opacity="0.9"/>
    <text x="181" y="517" text-anchor="middle" fill="#fbbf24">STARTUPS</text>

    <rect x="282" y="495" width="160" height="34" rx="4" fill="#1e293b" stroke="#6366f1" stroke-width="1" opacity="0.9"/>
    <text x="362" y="517" text-anchor="middle" fill="#a5b4fc">FAILURES</text>

    <rect x="458" y="495" width="160" height="34" rx="4" fill="#0c3b3b" stroke="#14b8a6" stroke-width="1" opacity="0.9"/>
    <text x="538" y="517" text-anchor="middle" fill="#5eead4">THINKERS</text>

    <rect x="634" y="495" width="160" height="34" rx="4" fill="#1e3e62" stroke="#38bdf8" stroke-width="1" opacity="0.9"/>
    <text x="714" y="517" text-anchor="middle" fill="#7dd3fc">PHYSICS</text>
  </g>

  <g transform="translate(940, 315)">
    <circle cx="0" cy="0" r="160" fill="#241b12" stroke="#d97706" stroke-width="1.8" opacity="0.5"/>
    <circle cx="0" cy="0" r="120" fill="none" stroke="#d97706" stroke-width="1" stroke-dasharray="6,8" opacity="0.35"/>
    <circle cx="0" cy="0" r="8" fill="#fbbf24"/>
    <line x1="-140" y1="0" x2="140" y2="0" stroke="#d97706" stroke-width="1" opacity="0.4"/>
    <line x1="0" y1="-140" x2="0" y2="140" stroke="#d97706" stroke-width="1" opacity="0.4"/>
    <path d="M 0 -95 L -75 80 L 75 80 Z" stroke="#fbbf24" stroke-width="2.5" fill="none" stroke-linejoin="round"/>
    <line x1="-45" y1="30" x2="45" y2="30" stroke="#fbbf24" stroke-width="2"/>
  </g>
</svg>'''

def main():
    print("=== Generating Vector SVG Book Covers & Branding Assets ===")
    
    for vol in VOLUMES:
        fname = f"{vol['id']}.svg"
        path = os.path.join(COVERS_DIR, fname)
        svg_code = create_book_svg(vol)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg_code)
        print(f"Generated cover: assets/covers/{fname} ({len(svg_code):,} bytes)")

    fav_path = os.path.join(BASE_DIR, "favicon.svg")
    fav_code = generate_favicon_svg()
    with open(fav_path, "w", encoding="utf-8") as f:
        f.write(fav_code)
    print(f"Generated favicon: favicon.svg ({len(fav_code):,} bytes)")

    og_path = os.path.join(BASE_DIR, "og-image.svg")
    og_code = generate_og_image_svg()
    with open(og_path, "w", encoding="utf-8") as f:
        f.write(og_code)
    print(f"Generated OG image: og-image.svg ({len(og_code):,} bytes)")

    manifest_path = os.path.join(BASE_DIR, "site.webmanifest")
    manifest_content = '''{
  "name": "Alexandria Press",
  "short_name": "Alexandria",
  "description": "The Living Library of Machine-Synthesized Knowledge. Digital-native two-column paged reader.",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#faf9f6",
  "theme_color": "#92400e",
  "icons": [
    {
      "src": "/favicon.svg",
      "sizes": "any",
      "type": "image/svg+xml",
      "purpose": "any maskable"
    }
  ]
}'''
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(manifest_content)
    print(f"Generated web manifest: site.webmanifest")

    print("\n--- ALL ASSETS GENERATED SUCCESSFULLY ---")

if __name__ == "__main__":
    main()
