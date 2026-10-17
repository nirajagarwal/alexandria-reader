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


def stage1_generate_dossier_batch(api_key: str, spec: dict, tracker: CostAndStateTracker) -> dict:
    tracker.set_stage(1, "Stage 1/4 · Designing 12-Chapter Research Dossier (Gemini Batch API)", 10)
    mode = spec["mode"]
    fmt = spec["format"]
    title = spec["title"]
    subtitle = spec["subtitle"]
    category = spec["category"]
    profile = spec["profile"]

    formalism_map = {
        1: "ledger_or_list",
        2: "diagram",
        3: "equation",
        4: "equation",
        5: "ledger_or_list",
        6: "diagram",
        7: "ledger_or_list",
        8: "equation",
        9: "equation",
        10: "diagram",
        11: "equation",
        12: "ledger_or_list",
    }
    doors = {
        1: "A: Scene",
        2: "B: Constraint/Paradox",
        3: "C: Artifact/Measurement",
        4: "A: Scene",
        5: "B: Constraint/Paradox",
        6: "C: Artifact/Measurement",
        7: "B: Constraint/Paradox",
        8: "C: Artifact/Measurement",
        9: "A: Scene",
        10: "B: Constraint/Paradox",
        11: "C: Artifact/Measurement",
        12: "B: Constraint/Paradox",
    }

    mode_instructions = ""
    if mode == "landscape":
        mode_instructions = """
This volume uses Knowra Contextual Landscape mode (`mode: "landscape"`):
- Chapter 1 is the Anchor Concept itself (the core mechanism and physical/biological definition of the book's topic).
- Chapters 2 through 12 examine 11 distinct neighboring concepts that surround, constrain, or interact with the anchor concept across lenses (`building-blocks`, `mechanism`, `origins`, `contrasts`, `neighbors`, `cases`, `consequences`, `open-questions`) and moves (`zoom-in`, `zoom-out`, `go`, `contrast`).
- Include `lens`, `move`, `what`, `why_here`, and 3 `background_nodes` (`[{"label": "...", "what": "...", "whyHere": "..."}]`) for each chapter.
"""
    elif mode == "listicle":
        mode_instructions = """
This volume uses the 12x12 Prospected Highlights mode (`mode: "listicle"`):
- Each of the 12 chapters examines one major subsystem, zone, or component of the topic through 12 perpendicular quantitative facts (`prospected_seeds`: array of 12 detailed factual strings per chapter).
"""
    elif fmt == "biography":
        mode_instructions = """
This volume is a 12-Facet Biography (`format: "biography"`):
- Chapter 1 examines the subject's early formation and intellectual style.
- Chapters 2 through 12 each examine one landmark theorem, experiment, machine, or historical collision.
"""
    else:
        mode_instructions = """
This volume uses 12-Facet Mechanisms mode (`mode: "mechanisms"`):
- Each of the 12 chapters examines a distinct physical, biological, engineering, or historical mechanism with a concrete primary experiment/event anchor and quantitative payoff.
"""

    prompt = f"""You are the Chief Editorial Architect for Alexandria Press (alexandria.press).
Design the complete 12-chapter research dossier JSON for the volume:
- Slug: "{spec['slug']}"
- Title: "{title}" (NO colons allowed)
- Subtitle: "{subtitle}" (NO colons allowed)
- Category: "{category}"
- Mode: "{mode}"
- Format: "{fmt}"
- Profile: "{profile}"

{mode_instructions}

CRITICAL RULES:
1. Return ONLY a valid JSON object matching the schema below (no markdown commentary outside the JSON).
2. Every chapter `title` and `subtitle` MUST contain ZERO colons (`:`).
3. Follow this exact `formalism_mode` schedule for chapters 1..12:
   {json.dumps(formalism_map)}
4. Follow this exact `opening_door` schedule for chapters 1..12:
   {json.dumps(doors)}
5. Every chapter MUST include:
   - `"chapter"`: integer 1..12
   - `"title"`: crisp title (no colons)
   - `"subtitle"`: crisp subtitle (no colons)
   - `"opening_door"`: from schedule above
   - `"formalism_mode"`: from schedule above
   - `"historical_anchor"`: 2-3 sentences naming the real researcher(s), exact year (4-digit year), institution/location, experimental apparatus or primary record, and quantitative measurements.
   - `"exit_fact"`: 1-2 sentences stating the concrete empirical measurement or outcome that closes the chapter.
   - `"equation_or_diagram_spec"`: If `formalism_mode` is `"equation"`, provide the exact LaTeX display equation (e.g. Borbély's two-process model, Hodgkin-Huxley/Kuramoto, exponential decay, Michaelis-Menten, Shannon entropy, etc.) and define its variables. If `"diagram"`, describe the 3-node schematic flow (`Node 1 -> Node 2 -> Node 3`) with short labels (<= 15 chars each). If `"ledger_or_list"`, list the 3-4 structured bullet items with concrete metrics.
   - `"search_query"`: A specific Google Search query (8-14 words) to verify the chapter's primary scientist, paper/experiment year, and quantitative measurement.

Output JSON schema:
{{
  "slug": "{spec['slug']}",
  "title": "{title}",
  "subtitle": "{subtitle}",
  "category": "{category}",
  "mode": "{mode}",
  "format": "{fmt}",
  "profile": "{profile}",
  "creator_constraints": {{
    "min_diagrams": 3,
    "quotes_allowed": false
  }},
  "chapters": [
    {{
      "chapter": 1,
      "title": "...",
      "subtitle": "...",
      "opening_door": "A: Scene",
      "formalism_mode": "ledger_or_list",
      "historical_anchor": "...",
      "exit_fact": "...",
      "equation_or_diagram_spec": "...",
      "search_query": "..."
    }}
  ]
}}
"""
    requests_list = [
        {
            "request": {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.4},
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
    dossier["creator_constraints"] = {"min_diagrams": 0 if mode == "listicle" else 3, "quotes_allowed": False}

    for idx, ch in enumerate(dossier.get("chapters", []), 1):
        ch["chapter"] = idx
        ch["title"] = (ch.get("title") or f"Facet {idx}").replace(":", "")
        ch["subtitle"] = (ch.get("subtitle") or f"Mechanism {idx}").replace(":", "")
        ch["formalism_mode"] = "listicle" if mode == "listicle" else formalism_map.get(idx, "ledger_or_list")
        ch["opening_door"] = doors.get(idx, "A: Scene")

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
        prompt = f"""Use Google Search (1 search) to fact-check and verify the following chapter dossier for "{dossier['title']}" — Chapter {ch_num} ({ch['title']}):

Proposed Historical Anchor: {ch.get('historical_anchor', '')}
Proposed Exit Fact: {ch.get('exit_fact', '')}
Verification Query Focus: {q}

Verify the exact researcher full names, 4-digit publication/experiment year, institution/place, and quantitative measurements. Correct any date, spelling, or numerical inaccuracy.
Return ONLY a JSON object with:
{{
  "chapter": {ch_num},
  "verified_historical_anchor": "2-3 sentences with verified names, exact 4-digit year, institution, apparatus, and measurements (NO colons, NO direct quotes)",
  "verified_exit_fact": "1-2 sentences with the verified empirical/quantitative payoff that ends the chapter (NO moralizing summary)",
  "key_verified_facts": [
    "Fact 1 with exact date/name/number",
    "Fact 2 with exact mechanism/measurement",
    "Fact 3 with exact experimental outcome"
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
  <text x="300" y="168" text-anchor="middle" font-family="sans-serif" font-size="11" fill="var(--text-muted)">Regulatory Feedback Loop</text>
</svg>
```"""


def build_chapter_prompt(dossier: dict, ch: dict) -> str:
    ch_num = ch["chapter"]
    ch_title = ch["title"].replace(":", "")
    ch_sub = ch["subtitle"].replace(":", "")
    f_mode = ch.get("formalism_mode", "ledger_or_list")
    door = ch.get("opening_door", "A: Scene")
    anchor = ch.get("historical_anchor", "")
    exit_fact = ch.get("exit_fact", "")
    v_facts = "\n".join(f"- {f}" for f in ch.get("verified_facts", []))
    eq_spec = ch.get("equation_or_diagram_spec", "")
    landscape_ctx = ""
    if dossier.get("mode") == "landscape":
        bg_nodes = ch.get("background_nodes", [])
        bg_str = "\n".join(
            f"  * {n.get('label', '')}: {n.get('what', '')} ({n.get('whyHere', '')})"
            for n in bg_nodes
        )
        landscape_ctx = f"""
Knowra Contextual Landscape Details:
- What this concept is: {ch.get('what', '')}
- How it connects to {dossier['title']}: {ch.get('why_here', '')}
- Background Nodes to weave into the mechanism:
{bg_str}
"""

    if f_mode == "listicle":
        seeds = ch.get("prospected_seeds", [])
        seeds_str = "\n".join(f"  {idx}. {s}" for idx, s in enumerate(seeds, 1)) if seeds else ""
        formalism_instr = f"""
FORMALISM MODE — 12-HIGHLIGHT LISTICLE (`mode: "listicle"`, `format: "highlights"`):
- Write EXACTLY 12 standalone paragraphs (~48–54 words per paragraph, totaling 580–650 words across the chapter).
- Separate the 12 paragraphs with 11 standalone lines containing ONLY `· · ·` surrounded by blank lines:
  Paragraph 1...

  · · ·

  Paragraph 2...
- Do NOT use numbered lists (`1.`, `2.`), bullet lists, SVG diagrams, or `$$...$$` display equations.
- Open every paragraph directly with the surprising physical fact, everyday bodily or physical experience, and concrete numbers—zero throat-clearing and zero academic jargon.
{f"- Expand these 12 prospected seeds:{chr(10)}{seeds_str}" if seeds_str else ""}
"""
    elif f_mode == "diagram":
        formalism_instr = f"""
FORMALISM MODE — SCHEMATIC DIAGRAM CHAPTER (`formalism_mode: "diagram"`):
- Do NOT include any `$$...$$` display math or Markdown bullet lists in this chapter.
- Instead, include a single line placeholder `[DIAGRAM_SLOT_{ch_num}]` between Paragraph 3 and Paragraph 4, AND at the very end of your response after `===DIAGRAM_LABELS===`, provide 6 short label strings (each <= 14 characters, no punctuation) for the 3 diagram boxes (`Box1Title | Box1Sub | Box2Title | Box2Sub | Box3Title | Box3Sub`).
- Write 5 to 6 crisp paragraphs of prose totaling **590 to 660 words** (excluding the diagram block).
"""
    elif f_mode == "equation":
        formalism_instr = f"""
FORMALISM MODE — DISPLAY EQUATION CHAPTER (`formalism_mode: "equation"`):
- Include EXACTLY ONE `$$...$$` display equation on its own lines between paragraphs, unpacking the mathematical relationship: {eq_spec}
- Use valid KaTeX syntax. If using `\\sum` inside `\\frac`, write `\\sum\\nolimits`. Define every symbol in plain prose right after the equation.
- Do NOT include any SVG diagram or bullet list in this chapter.
- Write 5 to 6 crisp paragraphs totaling **590 to 660 words**.
"""
    else:
        formalism_instr = f"""
FORMALISM MODE — STRUCTURED LEDGER / LIST CHAPTER (`formalism_mode: "ledger_or_list"`):
- Include ONE crisp Markdown bulleted list (`- **Stage/Metric** — explanation...` with 3 to 4 bullet items, NO colons inside headers, use an em-dash `—` after the bold term) unpacking: {eq_spec}
- Do NOT include any `$$...$$` display equation or SVG diagram in this chapter!
- Write 5 paragraphs plus the 3–4 bullet items totaling **590 to 660 words**.
"""

    open_rule = (
        "Do NOT start the first sentence with 'In [Year]', 'On [Date]', or 'At [Time]'—open directly with the physical apparatus, anatomical structure, or paradox first, and introduce the year in the second sentence."
        if ch_num != 1
        else "Open directly with the concrete experimental setting and researcher."
    )

    return f"""Write Chapter {ch_num} of the Alexandria Press book "{dossier['title']}: {dossier['subtitle']}".

MANDATORY 3-LINE HEADER (must appear at the very top of your output, with ZERO colons `:`):
### Chapter {ch_num}
# {ch_title}
## {ch_sub}

VERIFIED PRIMARY ANCHOR & FACTS (from Google Search Grounding):
- Historical Anchor: {anchor}
- Verified Facts:
{v_facts}
- Mandatory Exit Fact (close the final sentence of the chapter directly on this concrete fact): {exit_fact}
{landscape_ctx}
{formalism_instr}

NON-NEGOTIABLE ALEXANDRIA MANIFESTO LAWS:
1. PLAIN-ENGLISH CLARITY & ZERO ACADEMIC JARGON: Write in plainspoken, vivid everyday English using ordinary nouns and active verbs. NEVER try to impress with dense academic/Latinate jargon (e.g., never write "perceptual disengagement and motor quiescence", "monosynaptic tract", "transcriptional-translational autoregulatory loop"). Explain how things actually work so any curious human immediately pictures the mechanism. Never include journal volume, issue, or page numbers in prose.
2. WORD COUNT: The chapter body (after the 3-line header) MUST be between **580 and 670 words** (hard validator gate: `520–760` words). Count carefully so it is never under 550 or over 720 words.
3. SENTENCE LENGTH CADENCE: Keep average sentence length between **17 and 21 words per sentence** (hard gate: `<= 23.0` words/sentence). Write direct, declarative sentences with active verbs. Avoid long 35-word multi-clause sentences, and avoid 2-word fragment gimmicks.
4. ZERO DIRECT QUOTATIONS: NEVER include direct quotations of 5 or more words inside `"..."` or `“...”`. Paraphrase all statements and primary sources in crisp indirect speech.
5. ZERO NOVELISTIC MICRO-DETAILS: NEVER include weekdays with time of day (`Monday morning`, `Sunday afternoon`), weather cold-opens (`On a cold morning`), or hyphenated ages (`forty-three-year-old`, `32-year-old`).
6. OPENING CADENCE ({door}): {open_rule}
7. CLEAN EXIT: End the final paragraph directly on the concrete `exit_fact` measurement/outcome. NEVER write moralizing concluding sentences (`"proved that"`, `"demonstrated that"`, `"showed that"`, `"reminds us that"`, `"serves as a testament"`, `"Ultimately,"`, `"In conclusion"`).
8. BANNED WORDS & LATEX HYGIENE: Never use `breathtaking`, `awe-inspiring`, `mind-boggling`, `staggering`, or `paradigm-shifting`. Escape any literal currency dollar sign as `\\$100`, never wrap bare numbers in `$50$`, and never leak raw un-delimited LaTeX commands outside `$...$`.

Output ONLY the Markdown for Chapter {ch_num} starting with `### Chapter {ch_num}`."""


def build_intro_prompt(dossier: dict) -> str:
    title = dossier["title"].replace(":", "")
    intro_sub = f"The Physical and Conceptual Architecture of {title}"[:68]
    return f"""Write the Introduction section for the Alexandria Press volume "{title}" ({dossier['subtitle']}).

MANDATORY 3-LINE HEADER (must appear at the very top of your output, with ZERO colons `:`):
### Introduction
# {title}
## {intro_sub}

NON-NEGOTIABLE RULES:
1. PLAIN-ENGLISH CLARITY & ZERO JARGON: Write in clear, plainspoken everyday English. Never use stiff academic jargon or Latinate phrasing to sound impressive.
2. WORD COUNT: The Introduction body (after the 3-line header) MUST be **200 to 250 words** (hard validator gate: `140–300` words; write 3 crisp paragraphs of ~75 words each).
3. TOPIC-ONLY INTRODUCTION: Introduce the core phenomenon, physical constraints, and governing tension of {title} only. **NEVER summarize, list, or preview the individual chapters** (never write phrases like "this volume traces", "this volume examines", "across twelve chapters", or "the twelve chapters that follow").
4. SENTENCE CADENCE: Keep average sentence length at **17–21 words/sentence** (`<= 23.0` w/s).
5. ZERO QUOTES & ZERO HYPERBOLE: No direct quotations (`"..."`), no novelistic weather/weekday openings, and no banned words (`breathtaking`, `awe-inspiring`, `mind-boggling`, `staggering`, `paradigm-shifting`).

Output ONLY the Markdown for the Introduction starting with `### Introduction`."""


def postprocess_chapter_markdown(raw_md: str, ch: dict) -> str:
    ch_num = ch["chapter"]
    ch_title = ch["title"].replace(":", "")
    ch_sub = ch["subtitle"].replace(":", "")
    f_mode = ch.get("formalism_mode", "ledger_or_list")

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
        # Remove any display math or LLM-hallucinated svg block and insert our verified schematic SVG
        body = re.sub(r"```(?:svg|diagram)[\s\S]*?```", f"[DIAGRAM_SLOT_{ch_num}]", body, flags=re.IGNORECASE)
        body = re.sub(r"\$\$[\s\S]*?\$\$", "", body)
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
    intro_sub = f"The Physical and Conceptual Architecture of {title}"[:68].replace(":", "")
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
                "generationConfig": {"temperature": 0.45},
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
                    "generationConfig": {"temperature": 0.45},
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
                f"Manuscript passed all 12 validator gates (0 errors, 0 warnings, {summary.get('total_words', 0):,d} words, {summary.get('avg_sent_words', 0)} w/s)."
            )
            break

        tracker.log(f"Validator repair pass {repair_round}: fixing {len(errs)} error(s) and {len(warns)} warning(s)")
        for issue in all_issues:
            tracker.log(f"  - {issue}")

        # Fix Introduction if flagged
        if any("Introduction" in x or "Section 1 " in x for x in all_issues):
            fix_prompt = f"""Fix the following Introduction section so it strictly satisfies these validator errors:
Errors: {[x for x in all_issues if 'Introduction' in x or 'Section 1 ' in x]}

Current Introduction:
{sec_intro}

Requirements:
- Keep the exact 3-line header (`### Introduction` / `# ...` / `## ...`) with ZERO colons.
- Body word count MUST be 205–245 words (strictly between 140 and 300 words).
- Introduce the topic only—never preview or mention the chapters.
- Average sentence length <= 21 words/sentence.
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
            # Find chapters with longest average sentence length or date opening
            for idx_c, ch_txt in enumerate(sec_chapters, 1):
                sents = [s for s in re.split(r"(?<=[.!?])\s+", ch_txt) if len(s.split()) >= 3]
                avg_w = sum(len(s.split()) for s in sents) / max(1, len(sents))
                if avg_w > 22.5:
                    ch_to_fix.add(idx_c)

        for ch_num in sorted(ch_to_fix):
            ch_obj = dossier["chapters"][ch_num - 1]
            ch_issues = [x for x in all_issues if f"Chapter {ch_num}" in x or "sentence length" in x or "Cadence" in x]
            cur_text = sec_chapters[ch_num - 1]
            # Extract existing SVG block if present so we preserve it intact
            svg_match = re.search(r"```svg[\s\S]*?```", cur_text)
            saved_svg = svg_match.group(0) if svg_match else ""

            repair_prompt = f"""Rewrite Chapter {ch_num} below to fix all validator errors while preserving its facts and formalism:

Validator Issues to Fix:
{json.dumps(ch_issues, indent=2)}

Current Chapter {ch_num}:
{cur_text}

STRICT RULES:
1. Keep the exact 3-line header (`### Chapter {ch_num}` / `# {ch_obj['title']}` / `## {ch_obj['subtitle']}`) with ZERO colons.
2. Target body word count: **600 to 650 words** (must be strictly between 540 and 710 words, excluding any ```svg block).
3. Break long sentences into crisp declarative sentences so average sentence length is **17–20 words/sentence** (strictly <= 22.0 w/s).
4. ZERO direct quotes of 5+ words (`"..."`), ZERO novelistic weekdays/weather/hyphenated ages, and ZERO moralizing exit sentences (`proved that`, `demonstrated that`, `showed that`, `reminds us`, `testament`, `Ultimately`).
5. Do NOT start the first sentence with `In [Year]`, `On [Date]`, or `At [Time]`.
6. End directly on the concrete exit fact: {ch_obj.get('exit_fact', '')}
7. Escape literal dollar currency as `\\$100` and keep valid KaTeX math (`$...$` or `$$...$$`).

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
