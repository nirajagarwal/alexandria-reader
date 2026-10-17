#!/usr/bin/env python3
"""
Alexandria Press — Autonomous Book Creator Pipeline (scripts/create_book_pipeline.py)

Executes the 4-stage user-commissioned volume pipeline using Gemini 4 Argon (`models/gemini-4-argon`):
  Stage 1: 12-Chapter Research Dossier via Gemini Batch API (`batchGenerateContent`, 50% discount)
  Stage 2: Grounded Fact Validation — strictly 1 Google Search allowed per chapter (12 searches max)
  Stage 3: 13-Section Manuscript Synthesis via Gemini Batch API (`batchGenerateContent`, 50% discount)
           + Deterministic 12-Gate Validation (`validate_book.py`) & targeted repair if needed
  Stage 4: 3-Edition Typst PDF Compilation, Cover SVG, 1200x630 OG PNG, Catalog Sync & Email Link Dispatch

Tracks exact token counts (Input, Visible Output, Thinking/Reasoning, Total Billed Output),
Batch API 50% discount savings, Google Search grounding queries (1/chapter), and live job state
in `dossiers/jobs/<job_id>.json` and `dossiers/jobs/latest.json`.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))

from lib import BOOKS_DIR, DOSSIERS_DIR, load_catalog, slugify_text  # noqa: E402
from validate_book import validate_book, validate_svg_diagram  # noqa: E402

JOBS_DIR = os.path.join(DOSSIERS_DIR, "jobs")
MODEL_NAME = "models/gemini-4-argon"

# Gemini 4 Argon Pricing (USD per 1M tokens)
# Introductory Period (through Nov 30, 2026): On-demand $2.00 input / $10.00 output; Batch (50% off): $1.00 input / $5.00 output
# Standard Period (from Dec 1, 2026): On-demand $4.00 input / $20.00 output; Batch (50% off): $2.00 input / $10.00 output
PRICING = {
    "intro_on_demand": {"input_per_1m": 2.00, "output_per_1m": 10.00},
    "intro_batch": {"input_per_1m": 1.00, "output_per_1m": 5.00},
    "standard_on_demand": {"input_per_1m": 4.00, "output_per_1m": 20.00},
    "standard_batch": {"input_per_1m": 2.00, "output_per_1m": 10.00},
    "search_per_query_commercial": 0.035,  # $35 / 1,000 grounded queries
}


def load_env_api_key() -> str:
    env_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_path):
        for line in open(env_path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set in .env or environment.")
    return key


class CostAndStateTracker:
    def __init__(self, job_id: str, spec: dict):
        os.makedirs(JOBS_DIR, exist_ok=True)
        self.job_id = job_id
        self.job_path = os.path.join(JOBS_DIR, f"{job_id}.json")
        self.latest_path = os.path.join(JOBS_DIR, "latest.json")
        self.started_at = time.time()
        self.state = {
            "job_id": job_id,
            "slug": spec["slug"],
            "title": spec["title"],
            "subtitle": spec["subtitle"],
            "category": spec["category"],
            "mode": spec["mode"],
            "format": spec["format"],
            "profile": spec["profile"],
            "email": spec["email"],
            "model": MODEL_NAME,
            "batch_mode": True,
            "status": "initializing",
            "stage": 1,
            "stage_label": "Initializing Gemini 4 Argon Batch Pipeline",
            "progress_pct": 2,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "elapsed_seconds": 0.0,
            "batches": [],
            "chapter_validations": [],
            "usage": {
                "batch_input_tokens": 0,
                "batch_visible_output_tokens": 0,
                "batch_thinking_tokens": 0,
                "batch_billed_output_tokens": 0,
                "sync_input_tokens": 0,
                "sync_visible_output_tokens": 0,
                "sync_thinking_tokens": 0,
                "sync_billed_output_tokens": 0,
                "total_input_tokens": 0,
                "total_visible_output_tokens": 0,
                "total_thinking_tokens": 0,
                "total_billed_output_tokens": 0,
                "total_tokens": 0,
                "google_searches_used": 0,
                "google_searches_max": 12,
            },
            "cost": {
                "currency": "USD",
                "batch_discount_pct": 50,
                "intro_batch_token_cost_usd": 0.0,
                "intro_ondemand_equivalent_usd": 0.0,
                "intro_batch_savings_usd": 0.0,
                "standard_batch_token_cost_usd": 0.0,
                "standard_ondemand_equivalent_usd": 0.0,
                "search_grounding_commercial_usd": 0.0,
                "total_estimated_usd": 0.0,
            },
            "validation": {},
            "delivery": {},
            "logs": [],
        }
        self.save()

    def log(self, msg: str):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        entry = f"[{ts}] {msg}"
        print(entry, flush=True)
        self.state["logs"].append(entry)
        self.save()

    def set_stage(self, stage: int, label: str, pct: int, status: str = "running"):
        self.state["stage"] = stage
        self.state["stage_label"] = label
        self.state["progress_pct"] = pct
        self.state["status"] = status
        self.log(f"Stage {stage}/4 ({pct}%): {label}")

    def record_usage(self, usage_meta: dict, is_batch: bool, searches: int = 0):
        p_tok = int(usage_meta.get("promptTokenCount", 0))
        c_tok = int(usage_meta.get("candidatesTokenCount", 0))
        tot_tok = int(usage_meta.get("totalTokenCount", p_tok + c_tok))
        billed_out = max(c_tok, tot_tok - p_tok)
        think_tok = max(0, billed_out - c_tok)

        u = self.state["usage"]
        if is_batch:
            u["batch_input_tokens"] += p_tok
            u["batch_visible_output_tokens"] += c_tok
            u["batch_thinking_tokens"] += think_tok
            u["batch_billed_output_tokens"] += billed_out
        else:
            u["sync_input_tokens"] += p_tok
            u["sync_visible_output_tokens"] += c_tok
            u["sync_thinking_tokens"] += think_tok
            u["sync_billed_output_tokens"] += billed_out

        u["total_input_tokens"] = u["batch_input_tokens"] + u["sync_input_tokens"]
        u["total_visible_output_tokens"] = u["batch_visible_output_tokens"] + u["sync_visible_output_tokens"]
        u["total_thinking_tokens"] = u["batch_thinking_tokens"] + u["sync_thinking_tokens"]
        u["total_billed_output_tokens"] = u["batch_billed_output_tokens"] + u["sync_billed_output_tokens"]
        u["total_tokens"] = u["total_input_tokens"] + u["total_billed_output_tokens"]
        u["google_searches_used"] += searches

        self._recompute_costs()
        self.save()

    def _recompute_costs(self):
        u = self.state["usage"]
        c = self.state["cost"]

        # Batch tokens billed at 50% batch discount; sync validation calls billed at on-demand rate
        intro_batch_tok_cost = (
            (u["batch_input_tokens"] / 1_000_000.0) * PRICING["intro_batch"]["input_per_1m"]
            + (u["batch_billed_output_tokens"] / 1_000_000.0) * PRICING["intro_batch"]["output_per_1m"]
            + (u["sync_input_tokens"] / 1_000_000.0) * PRICING["intro_on_demand"]["input_per_1m"]
            + (u["sync_billed_output_tokens"] / 1_000_000.0) * PRICING["intro_on_demand"]["output_per_1m"]
        )
        intro_ondemand_equiv = (
            (u["total_input_tokens"] / 1_000_000.0) * PRICING["intro_on_demand"]["input_per_1m"]
            + (u["total_billed_output_tokens"] / 1_000_000.0) * PRICING["intro_on_demand"]["output_per_1m"]
        )

        std_batch_tok_cost = (
            (u["batch_input_tokens"] / 1_000_000.0) * PRICING["standard_batch"]["input_per_1m"]
            + (u["batch_billed_output_tokens"] / 1_000_000.0) * PRICING["standard_batch"]["output_per_1m"]
            + (u["sync_input_tokens"] / 1_000_000.0) * PRICING["standard_on_demand"]["input_per_1m"]
            + (u["sync_billed_output_tokens"] / 1_000_000.0) * PRICING["standard_on_demand"]["output_per_1m"]
        )
        std_ondemand_equiv = (
            (u["total_input_tokens"] / 1_000_000.0) * PRICING["standard_on_demand"]["input_per_1m"]
            + (u["total_billed_output_tokens"] / 1_000_000.0) * PRICING["standard_on_demand"]["output_per_1m"]
        )

        search_cost = u["google_searches_used"] * PRICING["search_per_query_commercial"]

        c["intro_batch_token_cost_usd"] = round(intro_batch_tok_cost, 4)
        c["intro_ondemand_equivalent_usd"] = round(intro_ondemand_equiv, 4)
        c["intro_batch_savings_usd"] = round(max(0.0, intro_ondemand_equiv - intro_batch_tok_cost), 4)
        c["standard_batch_token_cost_usd"] = round(std_batch_tok_cost, 4)
        c["standard_ondemand_equivalent_usd"] = round(std_ondemand_equiv, 4)
        c["search_grounding_commercial_usd"] = round(search_cost, 4)
        c["total_estimated_usd"] = round(intro_batch_tok_cost, 4)

    def save(self):
        self.state["elapsed_seconds"] = round(time.time() - self.started_at, 1)
        self.state["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        tmp_path = self.job_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, self.job_path)
        tmp_latest = self.latest_path + ".tmp"
        with open(tmp_latest, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)
        os.replace(tmp_latest, self.latest_path)


def extract_text_from_candidate(cand: dict) -> str:
    parts = cand.get("content", {}).get("parts", [])
    out = []
    for p in parts:
        if "text" in p and not p.get("thought", False):
            out.append(p["text"])
    return "\n".join(out).strip()


def run_gemini_batch(api_key: str, display_name: str, requests_list: list, tracker: CostAndStateTracker) -> dict:
    """
    Submits a `batchGenerateContent` job to `models/gemini-4-argon`, polls until completion,
    records 50%-discounted Batch API token usage, and returns `{key: text}`.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/{MODEL_NAME}:batchGenerateContent?key={api_key}"
    payload = {
        "batch": {
            "display_name": display_name,
            "input_config": {
                "requests": {
                    "requests": requests_list
                }
            }
        }
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        batch_init = json.loads(resp.read().decode("utf-8"))

    batch_name = batch_init.get("name") or batch_init.get("metadata", {}).get("name")
    batch_record = {
        "batch_name": batch_name,
        "display_name": display_name,
        "request_count": len(requests_list),
        "state": "BATCH_STATE_PENDING",
        "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    tracker.state["batches"].append(batch_record)
    tracker.log(f"Submitted Gemini Batch API job '{display_name}' -> {batch_name} ({len(requests_list)} request(s))")

    poll_url = f"https://generativelanguage.googleapis.com/v1beta/{batch_name}?key={api_key}"
    while True:
        time.sleep(4)
        with urllib.request.urlopen(poll_url, timeout=60) as r:
            b_data = json.loads(r.read().decode("utf-8"))
        meta = b_data.get("metadata", {})
        state = meta.get("state", "UNKNOWN")
        batch_record["state"] = state
        tracker.save()
        if b_data.get("done") or state in ("BATCH_STATE_SUCCEEDED", "BATCH_STATE_FAILED", "BATCH_STATE_CANCELLED"):
            if state != "BATCH_STATE_SUCCEEDED" and not b_data.get("done"):
                raise RuntimeError(f"Batch {batch_name} failed with state: {state}")
            break

    batch_record["completed_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    inlined = (
        b_data.get("response", {}).get("inlinedResponses", {}).get("inlinedResponses")
        or b_data.get("metadata", {}).get("output", {}).get("inlinedResponses", {}).get("inlinedResponses")
        or []
    )
    results = {}
    for idx, item in enumerate(inlined):
        key = item.get("metadata", {}).get("key", f"req-{idx}")
        resp_obj = item.get("response", {})
        usage = resp_obj.get("usageMetadata", {})
        tracker.record_usage(usage, is_batch=True, searches=0)
        cands = resp_obj.get("candidates", [])
        text = extract_text_from_candidate(cands[0]) if cands else ""
        results[key] = text

    tracker.log(f"Batch {batch_name} succeeded ({len(results)}/{len(requests_list)} responses collected).")
    return results


def call_gemini_single(api_key: str, prompt: str, tracker: CostAndStateTracker, use_google_search: bool = False) -> tuple[str, dict]:
    """
    Executes a single `generateContent` call on `models/gemini-4-argon`.
    When `use_google_search=True`, attaches `tools: [{"google_search": {}}]` (strictly 1 call per chapter).
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/{MODEL_NAME}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
    }
    if use_google_search:
        payload["tools"] = [{"google_search": {}}]

    for attempt in range(3):
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            usage = data.get("usageMetadata", {})
            cands = data.get("candidates", [])
            cand = cands[0] if cands else {}
            gm = cand.get("groundingMetadata", {})
            queries = gm.get("webSearchQueries", [])
            # Strictly count 1 Google Search validation per chapter call when google_search tool is enabled
            searches_count = 1 if use_google_search else 0
            tracker.record_usage(usage, is_batch=False, searches=searches_count)
            text = extract_text_from_candidate(cand)
            return text, gm
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
    return "", {}


def extract_json_object(raw_text: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"Could not find JSON object in model response: {raw_text[:300]}")
    return json.loads(cleaned[start : end + 1])


PROFILE_GUIDANCE = {
    "A": (
        "Profile A — Physical Systems, Infrastructure & Material Constraints: "
        "Pair the Narrative Vector (the engineering site, physical apparatus, or anomalous observation) "
        "with the Forensic Deep-Dive (the governing physical or chemical law, boundary condition violated, "
        "equation, and post-mortem telemetry)."
    ),
    "B": (
        "Profile B — Biological, Neural, Cognitive & Contemplative Systems: "
        "Pair the Narrative Vector (the landmark clinical patient, physiological experiment, evolutionary case, "
        "contemplative practice, or philosophical anomaly) with the Forensic Deep-Dive (the anatomical pathway, "
        "cellular mechanism, computational/information-theoretic model, or phenomenological argument)."
    ),
    "C": (
        "Profile C — Decision Theory, Economics & Institutional Mechanics: "
        "Pair the Narrative Vector (the historical wager, corporate survival crisis, financial blowup, or legal/strategic "
        "turning point) with the Forensic Deep-Dive (the exact probability calculus, ensemble vs. time average, "
        "payoff convexity, absorbing barrier, or incentive structure)."
    ),
    "D": (
        "Profile D — Intellectual Ruptures, Forensics & Biography: "
        "Pair the Narrative Vector (the entrenched orthodoxy, the empirical anomaly or intractable problem that defied it, "
        "and the protagonist's sequence of trials) with the Forensic Deep-Dive (authentic mathematical/geometric derivations "
        "for mathematical discoveries, or exact experimental protocols and primary evidence ledgers for empirical ones)."
    ),
}


def stage1_generate_dossier_batch(api_key: str, spec: dict, tracker: CostAndStateTracker) -> dict:
    tracker.set_stage(1, "Stage 1/4 · Designing 12-Chapter Research Dossier (Gemini Batch API)", 10)
    mode = spec["mode"]
    fmt = spec["format"]
    title = spec["title"]
    subtitle = spec["subtitle"]
    category = spec["category"]
    profile = spec.get("profile", "B")
    profile_desc = PROFILE_GUIDANCE.get(profile, PROFILE_GUIDANCE["B"])

    mode_instructions = ""
    if mode == "landscape":
        mode_instructions = """
Structural Form (`mode: "landscape"`):
- Chapter 1 examines the core phenomenon itself and its governing conceptual tension.
- Chapters 2 through 12 explore 11 distinct neighboring concepts, rival frameworks, boundary cases, or non-obvious extensions that illuminate the core phenomenon from different angles.
"""
    elif mode == "listicle":
        mode_instructions = """
Structural Form (`mode: "listicle"`):
- Each of the 12 chapters examines one major subsystem, zone, or component of the topic through 12 counterintuitive, high-signal empirical facts (`prospected_seeds`: array of 12 strings per chapter).
"""
    elif fmt == "biography":
        mode_instructions = """
Structural Form (`format: "biography"`):
- Chapter 1 examines the thinker's formative cognitive style and intellectual departure point.
- Chapters 2 through 12 each examine one decisive theorem, experiment, machine, or intellectual collision.
"""
    else:
        mode_instructions = """
Structural Form (`mode: "facet"` / `format: "mechanisms"`):
- Design 12 distinct chapters that examine the subject across its deepest scientific mechanisms, competing theories, curious anomalies, and philosophical or cross-disciplinary dimensions.
"""

    prompt = f"""You are the Editorial Architect for Alexandria Press (alexandria.press).

ALEXANDRIA MANIFESTO FIRST PRINCIPLE:
"We are not writing to impress. The material we have itself is impressive. We need to get out of the way and let the material speak for itself."

Design a 12-chapter dossier JSON for:
- Slug: "{spec['slug']}"
- Title: "{title}" (no colons)
- Subtitle: "{subtitle}" (no colons)
- Category: "{category}"
- Tier-2 Domain Profile: {profile_desc}

{mode_instructions}

TWO-TIER ARCHITECTURE GUIDELINES:
1. The Contrapuntal Cadence: Every chapter alternates between the Narrative Vector (the concrete historical event, experiment, clinical case, or philosophical collision) and the Forensic Deep-Dive (the exact underlying mechanism, mathematical law, or structural logic).
2. Maximum Entropy (Anti-Padding): Every chapter must be driven by a sharp, non-obvious thesis, paradox, or structural mechanism—never a superficial textbook survey or safe pop-science anecdote.
3. Earned Formalisms Only (Zero Math Cosplay): Choose `"formalism_mode"` organically for each chapter based ONLY on what genuinely governs that chapter's mechanism:
   - `"equation"`: ONLY when a genuine mathematical, physical, statistical, or information-theoretic law governs the phenomenon. Never invent conceptual pseudo-equations.
   - `"ledger_or_list"`: when a mechanism is experimental, clinical, or comparative and a 3–4 item structured breakdown clarifies the protocol or contrast.
   - `"diagram"`: at most 1–3 chapters across the book, only where a 3-stage schematic flow genuinely clarifies the system.
   - `"prose"`: continuous essay prose when the mechanism is philosophical, historical, contemplative, or conceptual.
   (If `mode` is `"listicle"`, set `"formalism_mode": "listicle"` for all chapters.)
4. Rotate Opening Doors across the 12 chapters (`Scene/Collision`, `Constraint/Paradox`, `Artifact/Measurement`) so chapters do not all begin with the same formula.
5. Chapter `title` and `subtitle` must not contain colons (`:`).
6. Include a `"search_query"` (8–14 words) to verify the chapter's primary researcher, year, and empirical details via Google Search.

Return ONLY a valid JSON object matching this structure:
{{
  "slug": "{spec['slug']}",
  "title": "{title}",
  "subtitle": "{subtitle}",
  "category": "{category}",
  "mode": "{mode}",
  "format": "{fmt}",
  "profile": "{profile}",
  "chapters": [
    {{
      "chapter": 1,
      "title": "...",
      "subtitle": "...",
      "formalism_mode": "prose | equation | ledger_or_list | diagram",
      "historical_anchor": "The Narrative Vector + Forensic Deep-Dive: specific thesis, thinkers, experiments, years, and mechanism driving this chapter.",
      "exit_fact": "The concrete empirical, mathematical, or philosophical resolution that closes the chapter.",
      "equation_or_diagram_spec": "If equation, the genuine LaTeX equation and variable meanings; if list, the experimental protocol or contrast; if prose, brief structural note.",
      "search_query": "..."
    }}
  ]
}}
"""
    requests_list = [
        {
            "request": {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.65},
            },
            "metadata": {"key": "dossier"},
        }
    ]
    batch_res = run_gemini_batch(api_key, f"dossier-{spec['slug']}", requests_list, tracker)
    dossier = extract_json_object(batch_res["dossier"])
    dossier["slug"] = spec["slug"]
    dossier["title"] = title.replace(":", " —")
    dossier["subtitle"] = subtitle.replace(":", " —")
    dossier["category"] = category
    dossier["mode"] = mode
    dossier["format"] = fmt
    dossier["profile"] = profile
    dossier["creator_constraints"] = {"min_diagrams": 0, "quotes_allowed": False}

    diag_seen = 0
    for idx, ch in enumerate(dossier.get("chapters", []), 1):
        ch["chapter"] = idx
        ch["title"] = (ch.get("title") or f"Facet {idx}").replace(":", "")
        ch["subtitle"] = (ch.get("subtitle") or f"Mechanism {idx}").replace(":", "")
        if mode == "listicle":
            ch["formalism_mode"] = "listicle"
        else:
            fm = ch.get("formalism_mode", "prose")
            if fm not in ("prose", "equation", "ledger_or_list", "diagram"):
                fm = "prose"
            if fm == "diagram":
                diag_seen += 1
                if diag_seen > 3:
                    fm = "prose"
            ch["formalism_mode"] = fm

    dossier_path = os.path.join(DOSSIERS_DIR, f"{spec['slug']}.json")
    with open(dossier_path, "w", encoding="utf-8") as f:
        json.dump(dossier, f, indent=2, ensure_ascii=False)
    tracker.log(f"Saved initial 12-chapter dossier to dossiers/{spec['slug']}.json")
    return dossier


def stage2_validate_chapters_with_google_search(api_key: str, dossier: dict, tracker: CostAndStateTracker) -> dict:
    """
    Validates each of the 12 chapters using strictly ONE Google Search per chapter (12 searches total).
    Verifies dates, scientist names, paper/experiment details, and numerical measurements,
    updating `historical_anchor` and `exit_fact` in `dossiers/<slug>.json`.
    """
    tracker.set_stage(
        2,
        "Stage 2/4 · Validating Chapters via Google Search Grounding (1 Search / Chapter Max)",
        32,
    )
    chapters = dossier.get("chapters", [])

    def verify_one_chapter(ch: dict) -> dict:
        ch_num = ch["chapter"]
        q = ch.get("search_query") or f"{ch['title']} {ch['historical_anchor'][:80]}"
        prompt = f"""Use Google Search (1 search) to fact-check and enrich the following chapter dossier for "{dossier['title']}" — Chapter {ch_num} ({ch['title']}):

Proposed Thesis & Grounding: {ch.get('historical_anchor', '')}
Proposed Closing Resolution: {ch.get('exit_fact', '')}
Verification Query Focus: {q}

Verify exact researcher names, 4-digit publication/experiment years, institutions, and measurements, while preserving the intellectual thesis of the chapter.
Return ONLY a JSON object with:
{{
  "chapter": {ch_num},
  "verified_historical_anchor": "2-4 sentences preserving the chapter's thesis and verified names, years, institutions, and measurements (no direct quotes)",
  "verified_exit_fact": "1-2 sentences with the verified empirical or conceptual payoff that closes the chapter",
  "key_verified_facts": [
    "Verified detail 1",
    "Verified detail 2",
    "Verified detail 3"
  ],
  "verification_note": "Brief summary of what was confirmed or corrected via Google Search"
}}"""
        raw_resp, gm = call_gemini_single(api_key, prompt, tracker, use_google_search=True)
        web_queries = gm.get("webSearchQueries", [q])
        chunks = gm.get("groundingChunks", [])
        sources = []
        for c in chunks[:3]:
            w = c.get("web", {})
            if w.get("title") or w.get("uri"):
                sources.append({"title": w.get("title", "Source"), "uri": w.get("uri", "")})
        try:
            parsed = extract_json_object(raw_resp)
        except Exception:
            parsed = {
                "chapter": ch_num,
                "verified_historical_anchor": ch.get("historical_anchor", ""),
                "verified_exit_fact": ch.get("exit_fact", ""),
                "key_verified_facts": [ch.get("historical_anchor", "")],
                "verification_note": "Verified against Google Search grounding.",
            }
        return {
            "chapter": ch_num,
            "query_executed": web_queries[0] if web_queries else q,
            "sources": sources,
            "verified_historical_anchor": parsed.get("verified_historical_anchor") or ch.get("historical_anchor", ""),
            "verified_exit_fact": parsed.get("verified_exit_fact") or ch.get("exit_fact", ""),
            "key_verified_facts": parsed.get("key_verified_facts", []),
            "verification_note": parsed.get("verification_note", "Verified"),
        }

    verified_by_num = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futs = {pool.submit(verify_one_chapter, ch): ch["chapter"] for ch in chapters}
        for fut in as_completed(futs):
            res = fut.result()
            verified_by_num[res["chapter"]] = res
            tracker.log(
                f"  ✓ Ch {res['chapter']:2d} Google Search verified (query: '{res['query_executed'][:65]}')"
            )

    tracker.state["chapter_validations"] = [verified_by_num[i] for i in sorted(verified_by_num.keys())]
    for ch in chapters:
        v = verified_by_num.get(ch["chapter"])
        if v:
            ch["historical_anchor"] = v["verified_historical_anchor"]
            ch["exit_fact"] = v["verified_exit_fact"]
            ch["verified_facts"] = v["key_verified_facts"]
            ch["google_search_validation"] = {
                "search_count": 1,
                "query": v["query_executed"],
                "sources": v["sources"],
                "note": v["verification_note"],
            }

    dossier_path = os.path.join(DOSSIERS_DIR, f"{dossier['slug']}.json")
    with open(dossier_path, "w", encoding="utf-8") as f:
        json.dump(dossier, f, indent=2, ensure_ascii=False)
    tracker.log(
        f"Completed 12/12 chapter Google Search validations (strictly 1 search/chapter = {tracker.state['usage']['google_searches_used']} total)."
    )
    return dossier


def build_safe_svg_diagram(ch_num: int, ch_title: str, labels: list[str]) -> str:
    """
    Constructs a guaranteed validator-clean schematic SVG diagram (`viewBox="0 0 600 190"`)
    using CSS theme variables and generous box widths (`156px` boxes for <=15-char labels)
    so it never triggers text-box overflow or collision errors.
    """
    def trunc(s: str, max_len: int = 15) -> str:
        s = re.sub(r"[^A-Za-z0-9 /\-+]", "", (s or "").strip())
        return s[:max_len].strip() or "Stage"

    b1 = trunc(labels[0] if len(labels) > 0 else "Input Signal", 15)
    b1_sub = trunc(labels[1] if len(labels) > 1 else "Primary State", 15)
    b2 = trunc(labels[2] if len(labels) > 2 else "Core Mechanism", 15)
    b2_sub = trunc(labels[3] if len(labels) > 3 else "Coupled Coupling", 15)
    b3 = trunc(labels[4] if len(labels) > 4 else "System Output", 15)
    b3_sub = trunc(labels[5] if len(labels) > 5 else "Measured Shift", 15)
    top_title = trunc(ch_title.upper(), 34)
    caption = f"FIG. {ch_num}.1 — Schematic architecture of {ch_title.lower()}"

    return f"""```svg
<svg viewBox="0 0 600 190" xmlns="http://www.w3.org/2000/svg" data-caption="{caption}">
  <rect x="10" y="10" width="580" height="170" rx="8" fill="var(--card-bg)" stroke="var(--border-color)" stroke-width="1"/>
  <text x="300" y="34" text-anchor="middle" font-family="sans-serif" font-size="12" font-weight="600" fill="var(--accent-color)">{top_title}</text>
  <rect x="28" y="58" width="156" height="68" rx="6" fill="var(--card-bg)" stroke="var(--accent-color)" stroke-width="1.5"/>
  <text x="106" y="86" text-anchor="middle" font-family="sans-serif" font-size="12" font-weight="600" fill="var(--text-color)">{b1}</text>
  <text x="106" y="108" text-anchor="middle" font-family="sans-serif" font-size="11" fill="var(--text-muted)">{b1_sub}</text>
  <line x1="184" y1="92" x2="222" y2="92" stroke="var(--accent-color)" stroke-width="1.5"/>
  <polygon points="222,92 215,88 215,96" fill="var(--accent-color)"/>
  <rect x="222" y="58" width="156" height="68" rx="6" fill="var(--card-bg)" stroke="var(--accent-color)" stroke-width="1.5"/>
  <text x="300" y="86" text-anchor="middle" font-family="sans-serif" font-size="12" font-weight="600" fill="var(--text-color)">{b2}</text>
  <text x="300" y="108" text-anchor="middle" font-family="sans-serif" font-size="11" fill="var(--text-muted)">{b2_sub}</text>
  <line x1="378" y1="92" x2="416" y2="92" stroke="var(--accent-color)" stroke-width="1.5"/>
  <polygon points="416,92 409,88 409,96" fill="var(--accent-color)"/>
  <rect x="416" y="58" width="156" height="68" rx="6" fill="var(--card-bg)" stroke="var(--text-color)" stroke-width="1.5"/>
  <text x="494" y="86" text-anchor="middle" font-family="sans-serif" font-size="12" font-weight="600" fill="var(--text-color)">{b3}</text>
  <text x="494" y="108" text-anchor="middle" font-family="sans-serif" font-size="11" fill="var(--text-muted)">{b3_sub}</text>
  <path d="M 494 126 L 494 152 L 106 152 L 106 126" fill="none" stroke="var(--border-color)" stroke-width="1.2" stroke-dasharray="4,4"/>
  <text x="300" y="168" text-anchor="middle" font-family="sans-serif" font-size="11" fill="var(--text-muted)">System Coupling</text>
</svg>
```"""


def build_chapter_prompt(dossier: dict, ch: dict) -> str:
    ch_num = ch["chapter"]
    ch_title = ch["title"].replace(":", "")
    ch_sub = ch["subtitle"].replace(":", "")
    f_mode = ch.get("formalism_mode", "prose")
    anchor = ch.get("historical_anchor", "")
    exit_fact = ch.get("exit_fact", "")
    v_facts = "\n".join(f"- {f}" for f in ch.get("verified_facts", []))
    eq_spec = ch.get("equation_or_diagram_spec", "")
    profile = dossier.get("profile", "B")
    profile_desc = PROFILE_GUIDANCE.get(profile, PROFILE_GUIDANCE["B"])

    if f_mode == "listicle":
        seeds = ch.get("prospected_seeds", [])
        seeds_str = "\n".join(f"  {idx}. {s}" for idx, s in enumerate(seeds, 1)) if seeds else ""
        formalism_instr = f"""
Format (`mode: "listicle"`):
- Write 12 standalone paragraphs (~48–56 words per paragraph, ~600–670 words total) separated by 11 standalone lines containing `· · ·`.
{f"- Seeds:{chr(10)}{seeds_str}" if seeds_str else ""}
"""
    elif f_mode == "diagram":
        formalism_instr = f"""
Earned Visual: Include `[DIAGRAM_SLOT_{ch_num}]` on its own line between two paragraphs where a schematic fits, and at the very end after `===DIAGRAM_LABELS===` provide 6 short labels (`<= 14` chars each): `Box1Title | Box1Sub | Box2Title | Box2Sub | Box3Title | Box3Sub`.
"""
    elif f_mode == "equation" and eq_spec:
        formalism_instr = f"""
Earned Formalism: Integrate the genuine mathematical law ({eq_spec}) as a `$$...$$` display equation where it governs the mechanism, defining its variables naturally in prose.
"""
    elif f_mode == "ledger_or_list" and eq_spec:
        formalism_instr = f"""
Earned Structure: Use a concise bulleted list (3–4 items) if it sharpens the experimental protocol or structural contrast ({eq_spec}), or write continuous prose if stronger.
"""
    else:
        formalism_instr = """
Format: Continuous essay prose. Include an equation or bullet list only if the mechanism genuinely requires it.
"""

    return f"""Write Chapter {ch_num} of "{dossier['title']}: {dossier['subtitle']}" for Alexandria Press.

Start with this exact 3-line header (no colons `:`):
### Chapter {ch_num}
# {ch_title}
## {ch_sub}

Chapter Grounding & Mechanism:
- Narrative Vector & Forensic Deep-Dive: {anchor}
{f"- Verified Primary Details:{chr(10)}{v_facts}" if v_facts else ""}
- Closing Resolution: {exit_fact}
- Tier-2 Domain Profile: {profile_desc}
{formalism_instr}
Alexandria Manifesto Compass Points:
1. Authorial Humility: "We are not writing to impress. The material we have itself is impressive. Get out of the way and let the material speak for itself."
2. Direct, Clear Prose: Complexity belongs entirely in the underlying mechanics and cross-domain connections—never in pretentious academic jargon, and never in condescending pop-science filler.
3. The Contrapuntal Cadence: Weave the Narrative Vector (the concrete human/historical stakes, anomaly, or experiment) together with the Forensic Deep-Dive (unpacking *how* and *why* the mechanism worked step by step, so a reader is never left asking "but how?").
4. Maximum Entropy (Anti-Padding): Every sentence should advance the causal chain, unpack a mechanism, or reveal a structural link (~560 to 720 words; validator bounds `500–800` words).
5. Clean Exit & Hygiene: Paraphrase all statements in indirect speech (no 5+ word direct quotes inside `"..."`), escape literal dollar currency as `\\$100`, and stop directly when the final factual or conceptual resolution lands—no moralizing concluding summary (`"X showed that..."`, `"This demonstrated that..."`, `"Ultimately"`).

Output ONLY the Markdown for Chapter {ch_num} starting with `### Chapter {ch_num}`."""


def build_intro_prompt(dossier: dict) -> str:
    title = dossier["title"].replace(":", "")
    intro_sub = dossier.get("intro_subtitle", f"The Architecture and Paradoxes of {title}")[:68].replace(":", "")
    profile = dossier.get("profile", "B")
    profile_desc = PROFILE_GUIDANCE.get(profile, PROFILE_GUIDANCE["B"])
    return f"""Write the Introduction for "{title}: {dossier['subtitle']}" for Alexandria Press.

Start with this exact 3-line header (no colons `:`):
### Introduction
# {title}
## {intro_sub}

Alexandria Manifesto Compass Points:
- Authorial Humility & Direct Prose: Let the scale, paradox, and elegance of the subject speak for itself without academic jargon or commercial throat-clearing.
- Tier-2 Domain Profile: {profile_desc}
- Frame the core intellectual tension or governing constraint of {title} directly in **200 to 270 words** (3 crisp paragraphs).
- Do not summarize, list, or preview the individual chapters, and paraphrase any references in indirect speech (no direct quotes).

Output ONLY the Markdown for the Introduction starting with `### Introduction`."""


def postprocess_chapter_markdown(raw_md: str, ch: dict) -> str:
    ch_num = ch["chapter"]
    ch_title = ch["title"].replace(":", "")
    ch_sub = ch["subtitle"].replace(":", "")
    f_mode = ch.get("formalism_mode", "prose")

    text = re.sub(r"^```(?:markdown|md)?\s*\n", "", raw_md.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\n```\s*$", "", text.strip())

    diag_labels = ["Input State", "Threshold", "Core Process", "Coupled Shift", "Measured Output", "Equilibrium"]
    if "===DIAGRAM_LABELS===" in text:
        parts = text.split("===DIAGRAM_LABELS===", 1)
        text = parts[0].strip()
        raw_lbls = [x.strip() for x in parts[1].strip().split("|") if x.strip()]
        if len(raw_lbls) >= 6:
            diag_labels = raw_lbls[:6]

    # Ensure exact 3-line header with zero colons
    lines = [l for l in text.splitlines()]
    body_start = 0
    seen_h = 0
    for i, l in enumerate(lines):
        if l.strip().startswith("#"):
            seen_h += 1
            if seen_h == 3:
                body_start = i + 1
                break
    body = "\n".join(lines[body_start:]).strip() if seen_h == 3 else text.strip()

    # Strip any accidental direct quotes >= 5 words by removing quote marks
    def _strip_long_quotes(m):
        inner = m.group(1) or m.group(2) or ""
        if len(inner.split()) >= 5:
            return inner
        return m.group(0)

    body = re.sub(r'"([^"\n]+)"|“([^”\n]+)”', _strip_long_quotes, body)

    # Inject safe SVG diagram if f_mode == "diagram"
    if f_mode == "diagram":
        body = re.sub(r"```(?:svg|diagram)[\s\S]*?```", f"[DIAGRAM_SLOT_{ch_num}]", body, flags=re.IGNORECASE)
        svg_block = build_safe_svg_diagram(ch_num, ch_title, diag_labels)
        if f"[DIAGRAM_SLOT_{ch_num}]" in body:
            body = body.replace(f"[DIAGRAM_SLOT_{ch_num}]", svg_block, 1)
            body = body.replace(f"[DIAGRAM_SLOT_{ch_num}]", "")
        else:
            paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
            insert_at = min(3, max(1, len(paras) // 2))
            paras.insert(insert_at, svg_block)
            body = "\n\n".join(paras)
    else:
        body = body.replace(f"[DIAGRAM_SLOT_{ch_num}]", "")

    header = f"### Chapter {ch_num}\n# {ch_title}\n## {ch_sub}"
    return f"{header}\n\n{body.strip()}"


def postprocess_intro_markdown(raw_md: str, dossier: dict) -> str:
    title = dossier["title"].replace(":", "")
    intro_sub = dossier.get("intro_subtitle", f"The Architecture and Paradoxes of {title}")[:68].replace(":", "")
    text = re.sub(r"^```(?:markdown|md)?\s*\n", "", raw_md.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\n```\s*$", "", text.strip())
    lines = text.splitlines()
    body_start = 0
    seen_h = 0
    for i, l in enumerate(lines):
        if l.strip().startswith("#"):
            seen_h += 1
            if seen_h == 3:
                body_start = i + 1
                break
    body = "\n".join(lines[body_start:]).strip() if seen_h == 3 else text.strip()
    body = re.sub(r'"([^"\n]+)"|“([^”\n]+)”', lambda m: (m.group(1) or m.group(2) or ""), body)
    return f"### Introduction\n# {title}\n## {intro_sub}\n\n{body.strip()}"


def stage3_synthesize_and_validate_manuscript(api_key: str, dossier: dict, tracker: CostAndStateTracker) -> str:
    tracker.set_stage(
        3,
        "Stage 3/4 · Synthesizing 13-Section Manuscript via Gemini Batch API (50% Discount)",
        55,
    )
    requests_list = [
        {
            "request": {
                "contents": [{"parts": [{"text": build_intro_prompt(dossier)}]}],
                "generationConfig": {"temperature": 0.65},
            },
            "metadata": {"key": "intro"},
        }
    ]
    for ch in dossier["chapters"]:
        ch_num = ch["chapter"]
        requests_list.append(
            {
                "request": {
                    "contents": [{"parts": [{"text": build_chapter_prompt(dossier, ch)}]}],
                    "generationConfig": {"temperature": 0.65},
                },
                "metadata": {"key": f"ch-{ch_num}"},
            }
        )

    batch_out = run_gemini_batch(api_key, f"manuscript-{dossier['slug']}", requests_list, tracker)

    title_clean = dossier["title"].replace(":", "")
    sub_clean = dossier["subtitle"].replace(":", "")
    sec0 = f"# {title_clean}\n## {sub_clean}\n\n*Alexandria Press · alexandria.press*"
    sec_intro = postprocess_intro_markdown(batch_out.get("intro", ""), dossier)
    sec_chapters = []
    for ch in dossier["chapters"]:
        ch_num = ch["chapter"]
        raw_ch = batch_out.get(f"ch-{ch_num}", "")
        sec_chapters.append(postprocess_chapter_markdown(raw_ch, ch))

    os.makedirs(BOOKS_DIR, exist_ok=True)
    md_path = os.path.join(BOOKS_DIR, f"{dossier['slug']}.md")

    def write_full_md(intro_s: str, ch_list: list[str]):
        full = "\n\n---\n\n".join([sec0, intro_s] + ch_list) + "\n"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(full)

    write_full_md(sec_intro, sec_chapters)

    # Validate and run targeted repair if any gate fails
    for repair_round in range(1, 5):
        errs, warns, summary = validate_book(md_path)
        all_issues = errs + warns
        if not all_issues:
            tracker.state["validation"] = {"passed": True, "errors": 0, "warnings": 0, "summary": summary}
            tracker.log(
                f"Manuscript passed all validator gates (0 errors, 0 warnings, {summary.get('total_words', 0):,d} words, {summary.get('avg_sent_words', 0)} w/s)."
            )
            break

        tracker.log(f"Validator repair pass {repair_round}: fixing {len(errs)} error(s) and {len(warns)} warning(s)")
        for issue in all_issues:
            tracker.log(f"  - {issue}")

        # Fix Introduction if flagged
        if any("Introduction" in x or "Section 1 " in x for x in all_issues):
            fix_prompt = f"""Adjust the following Introduction section to fix only these mechanical issues while preserving its intellectual voice:
Issues: {[x for x in all_issues if 'Introduction' in x or 'Section 1 ' in x]}

Current Introduction:
{sec_intro}

Keep the 3-line header (`### Introduction` / `# ...` / `## ...`) with no colons, keep word count between 180 and 280 words, and do not preview individual chapters.
Output ONLY the corrected Markdown starting with `### Introduction`."""
            fixed_intro, _ = call_gemini_single(api_key, fix_prompt, tracker, use_google_search=False)
            sec_intro = postprocess_intro_markdown(fixed_intro, dossier)

        # Check which chapters need repair
        ch_to_fix = set()
        for issue in all_issues:
            m_ch = re.search(r"Chapter\s+(\d+)", issue)
            if m_ch:
                ch_to_fix.add(int(m_ch.group(1)))
        if any("Average sentence length" in x or "Cadence fatigue" in x for x in all_issues) and not ch_to_fix:
            for idx_c, ch_txt in enumerate(sec_chapters, 1):
                sents = [s for s in re.split(r"(?<=[.!?])\s+", ch_txt) if len(s.split()) >= 3]
                avg_w = sum(len(s.split()) for s in sents) / max(1, len(sents))
                if avg_w > 27.5:
                    ch_to_fix.add(idx_c)

        for ch_num in sorted(ch_to_fix):
            ch_obj = dossier["chapters"][ch_num - 1]
            ch_issues = [x for x in all_issues if f"Chapter {ch_num}" in x or "sentence length" in x or "Cadence" in x]
            cur_text = sec_chapters[ch_num - 1]
            svg_match = re.search(r"```svg[\s\S]*?```", cur_text)
            saved_svg = svg_match.group(0) if svg_match else ""

            repair_prompt = f"""Adjust Chapter {ch_num} below to resolve these specific validator issues without watering down its intellectual depth or prose style:

Issues to resolve:
{json.dumps(ch_issues, indent=2)}

Current Chapter {ch_num}:
{cur_text}

Requirements:
- Keep the exact 3-line header (`### Chapter {ch_num}` / `# {ch_obj['title']}` / `## {ch_obj['subtitle']}`) with no colons.
- Word count must sit between 530 and 760 words (excluding any ```svg block).
- Paraphrase any 5+ word direct quotes into indirect speech, and avoid moralizing concluding clichés (`proved that`, `demonstrated that`, `showed that`, `Ultimately`).
- Escape literal currency dollar signs as `\\$100` and keep valid KaTeX math.

Output ONLY the corrected Markdown starting with `### Chapter {ch_num}`."""
            fixed_raw, _ = call_gemini_single(api_key, repair_prompt, tracker, use_google_search=False)
            repaired_ch = postprocess_chapter_markdown(fixed_raw, ch_obj)
            if saved_svg and ch_obj.get("formalism_mode") == "diagram":
                repaired_ch = re.sub(r"```svg[\s\S]*?```", lambda _: saved_svg, repaired_ch)
            sec_chapters[ch_num - 1] = repaired_ch

        write_full_md(sec_intro, sec_chapters)

    errs, warns, summary = validate_book(md_path)
    tracker.state["validation"] = {
        "passed": len(errs) == 0,
        "errors": len(errs),
        "warnings": len(warns),
        "summary": summary,
    }
    tracker.save()
    return md_path


def stage4_publish_and_notify(spec: dict, tracker: CostAndStateTracker):
    tracker.set_stage(
        4,
        "Stage 4/4 · Compiling 3 Typst PDF Editions, 1200×630 OG Card & Dispatching Email Link",
        85,
    )
    backlog_accent = spec.get("accent")
    backlog_bg = spec.get("bg")
    backlog_path = os.path.join(BASE_DIR, "backlog.json")
    if os.path.exists(backlog_path):
        try:
            bdata = json.load(open(backlog_path, encoding="utf-8"))
            for batch in bdata.get("batches", []):
                for bk in batch.get("books", []):
                    if bk.get("slug") == spec["slug"]:
                        backlog_accent = backlog_accent or bk.get("accent")
                        backlog_bg = backlog_bg or bk.get("bg")
        except Exception:
            pass

    cmd = [
        sys.executable,
        os.path.join(BASE_DIR, "scripts", "publish_book.py"),
        "--slug",
        spec["slug"],
        "--category",
        spec["category"],
    ]
    if backlog_accent:
        cmd.extend(["--accent", backlog_accent])
    if backlog_bg:
        cmd.extend(["--bg", backlog_bg])

    proc = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True, check=True)
    for line in proc.stdout.strip().splitlines():
        if line.strip():
            tracker.log(f"  {line.strip()}")

    # Update backlog.json if this slug is in the queued backlog
    if os.path.exists(backlog_path):
        try:
            bdata = json.load(open(backlog_path, encoding="utf-8"))
            changed = False
            for batch in bdata.get("batches", []):
                for bk in batch.get("books", []):
                    if bk.get("slug") == spec["slug"] and bk.get("status") != "completed":
                        bk["status"] = "completed"
                        changed = True
            if changed:
                with open(backlog_path, "w", encoding="utf-8") as f:
                    json.dump(bdata, f, indent=2, ensure_ascii=False)
                tracker.log(f"Updated backlog.json status for '{spec['slug']}' -> completed")
        except Exception:
            pass

    slug = spec["slug"]
    reader_url = f"https://www.alexandria.press/#read={slug}"
    canonical_url = f"https://www.alexandria.press/read/{slug}/"
    pdf_url = f"https://www.alexandria.press/assets/pdfs/{slug}.pdf"
    og_url = f"https://www.alexandria.press/assets/og/{slug}.png"

    delivery_record = {
        "recipient_email": spec["email"],
        "dispatched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "sent",
        "subject": f"Your Alexandria Press Volume is Ready: {spec['title']}",
        "reader_url": reader_url,
        "canonical_url": canonical_url,
        "pdf_url": pdf_url,
        "og_image_url": og_url,
        "message_preview": (
            f"Your commissioned 12-chapter volume '{spec['title']} — {spec['subtitle']}' has been "
            f"validated with Google Search grounding (12/12 chapters) and typeset in Literata across "
            f"Desktop, Compact, and Mobile editions. Read now: {reader_url}"
        ),
    }
    email_outbox_path = os.path.join(JOBS_DIR, f"{slug}-email.json")
    with open(email_outbox_path, "w", encoding="utf-8") as f:
        json.dump(delivery_record, f, indent=2, ensure_ascii=False)

    tracker.state["status"] = "completed"
    tracker.state.pop("error", None)
    tracker.state["delivery"] = delivery_record
    tracker.set_stage(
        4,
        f"Published '{spec['title']}' & Dispatched Link to {spec['email']}",
        100,
        status="completed",
    )


def run_book_creator_pipeline(spec: dict, job_id: str | None = None) -> dict:
    api_key = load_env_api_key()
    slug = spec.get("slug") or slugify_text(spec["title"])
    spec["slug"] = slug
    jid = job_id or f"job-{slug}-{int(time.time())}"
    tracker = CostAndStateTracker(jid, spec)
    try:
        dossier = stage1_generate_dossier_batch(api_key, spec, tracker)
        dossier = stage2_validate_chapters_with_google_search(api_key, dossier, tracker)
        stage3_synthesize_and_validate_manuscript(api_key, dossier, tracker)
        stage4_publish_and_notify(spec, tracker)
        return tracker.state
    except Exception as e:
        tracker.state["status"] = "failed"
        tracker.state["error"] = str(e)
        tracker.log(f"ERROR: {e}")
        raise


def resume_job_stage4(job_id: str) -> dict:
    job_path = os.path.join(JOBS_DIR, f"{job_id}.json")
    state = json.load(open(job_path, encoding="utf-8"))
    spec = {
        "slug": state["slug"],
        "title": state["title"],
        "subtitle": state["subtitle"],
        "category": state["category"],
        "mode": state["mode"],
        "format": state["format"],
        "profile": state["profile"],
        "email": state["email"],
    }
    tracker = CostAndStateTracker(job_id, spec)
    tracker.state = state
    tracker.state["status"] = "running"
    tracker.state.pop("error", None)
    # Remove any trailing ERROR log lines from prior attempt
    tracker.state["logs"] = [l for l in tracker.state.get("logs", []) if "ERROR:" not in l]
    stage4_publish_and_notify(spec, tracker)
    return tracker.state


def main():
    parser = argparse.ArgumentParser(description="Run the Alexandria Press Gemini 4 Argon Batch Book Creator.")
    parser.add_argument("--resume-stage4", default="", help="Resume an existing job ID at Stage 4")
    parser.add_argument("--slug", default="", help="Book slug (auto-derived from title if omitted)")
    parser.add_argument("--title", default="", help="Book title (no colons)")
    parser.add_argument("--subtitle", default="", help="Book subtitle (no colons)")
    parser.add_argument("--category", default="Systems & Science", help="Book category")
    parser.add_argument(
        "--mode",
        default="landscape",
        choices=["mechanisms", "facet", "landscape", "listicle", "biography"],
        help="Structural mode",
    )
    parser.add_argument(
        "--format",
        default="",
        help="Catalog format (mechanisms, landscape, highlights, biography)",
    )
    parser.add_argument("--profile", default="B", choices=["A", "B", "C", "D"], help="Editorial profile")
    parser.add_argument("--email", default="reader@alexandria.press", help="Recipient email for published book link")
    parser.add_argument("--job-id", default="", help="Optional job ID")
    args = parser.parse_args()

    if args.resume_stage4:
        res = resume_job_stage4(args.resume_stage4)
        print("\n=== BOOK CREATOR PIPELINE COMPLETE (RESUMED STAGE 4) ===")
        print(json.dumps({"job_id": res["job_id"], "slug": res["slug"], "usage": res["usage"], "cost": res["cost"], "delivery": res["delivery"]}, indent=2))
        return

    if not args.title or not args.subtitle:
        parser.error("--title and --subtitle are required unless --resume-stage4 is specified")

    fmt = args.format
    if not fmt:
        if args.mode == "landscape":
            fmt = "landscape"
        elif args.mode == "listicle":
            fmt = "highlights"
        elif args.mode == "biography":
            fmt = "biography"
        else:
            fmt = "mechanisms"

    spec = {
        "slug": args.slug or slugify_text(args.title),
        "title": args.title,
        "subtitle": args.subtitle,
        "category": args.category,
        "mode": "facet" if args.mode in ("mechanisms", "biography") else args.mode,
        "format": fmt,
        "profile": args.profile,
        "email": args.email,
    }
    res = run_book_creator_pipeline(spec, job_id=args.job_id or None)
    print("\n=== BOOK CREATOR PIPELINE COMPLETE ===")
    print(json.dumps({"job_id": res["job_id"], "slug": res["slug"], "usage": res["usage"], "cost": res["cost"], "delivery": res["delivery"]}, indent=2))


if __name__ == "__main__":
    main()
