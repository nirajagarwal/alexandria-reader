#!/usr/bin/env python3
"""
Alexandria Press — Local Web & Book Creator API Server (scripts/book_creator_server.py)

Serves the static Alexandria Press web application and exposes lightweight JSON endpoints
for the interactive Book Creator UI:
  - GET  /api/creator/pipeline         -> Queued topics from backlog.json & recent job receipts
  - POST /api/creator/start            -> Launches a Gemini 4 Argon Batch Book Creator job
  - GET  /api/creator/status?job_id=.. -> Returns live stage, batch IDs, token counts, searches & cost
"""

import argparse
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
import sys
import threading
import time
import urllib.parse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))

from create_book_pipeline import JOBS_DIR, run_book_creator_pipeline  # noqa: E402
from lib import slugify_text  # noqa: E402


class CreatorRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def log_message(self, format, *args):
        # Keep server logs concise
        pass

    def _send_json(self, status_code: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/creator/pipeline":
            backlog_path = os.path.join(BASE_DIR, "backlog.json")
            queued = []
            if os.path.exists(backlog_path):
                bdata = json.load(open(backlog_path, encoding="utf-8"))
                for batch in bdata.get("batches", []):
                    for bk in batch.get("books", []):
                        if bk.get("status") == "queued":
                            queued.append(bk)
            latest_job = None
            latest_path = os.path.join(JOBS_DIR, "latest.json")
            if os.path.exists(latest_path):
                try:
                    latest_job = json.load(open(latest_path, encoding="utf-8"))
                except Exception:
                    pass
            return self._send_json(200, {"queued_topics": queued, "latest_job": latest_job})

        if parsed.path == "/api/creator/status":
            qs = urllib.parse.parse_qs(parsed.query)
            job_id = (qs.get("job_id") or ["latest"])[0]
            target = (
                os.path.join(JOBS_DIR, "latest.json")
                if job_id == "latest"
                else os.path.join(JOBS_DIR, f"{ os.path.basename(job_id) }.json")
            )
            if not os.path.exists(target):
                return self._send_json(404, {"error": f"Job not found: {job_id}"})
            try:
                data = json.load(open(target, encoding="utf-8"))
                return self._send_json(200, data)
            except Exception as e:
                return self._send_json(500, {"error": str(e)})

        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/creator/start":
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            try:
                body = json.loads(raw)
            except Exception:
                return self._send_json(400, {"error": "Invalid JSON body"})

            title = (body.get("title") or "").strip().replace(":", "")
            subtitle = (body.get("subtitle") or "").strip().replace(":", "")
            category = (body.get("category") or "Systems & Science").strip()
            mode = (body.get("mode") or "landscape").strip()
            fmt = (body.get("format") or "landscape").strip()
            profile = (body.get("profile") or "B").strip()
            email = (body.get("email") or "").strip()
            slug = (body.get("slug") or slugify_text(title)).strip()

            if not title or not subtitle or not email:
                return self._send_json(400, {"error": "Title, subtitle, and delivery email are required."})

            job_id = f"job-{slug}-{int(time.time())}"
            spec = {
                "slug": slug,
                "title": title,
                "subtitle": subtitle,
                "category": category,
                "mode": "facet" if mode in ("mechanisms", "biography") else mode,
                "format": fmt,
                "profile": profile,
                "email": email,
            }

            def _worker():
                try:
                    run_book_creator_pipeline(spec, job_id=job_id)
                except Exception as exc:
                    print(f"[Creator Worker Error] {exc}", flush=True)

            t = threading.Thread(target=_worker, daemon=True)
            t.start()
            return self._send_json(
                200,
                {
                    "ok": True,
                    "job_id": job_id,
                    "slug": slug,
                    "status": "initializing",
                },
            )

        return self._send_json(404, {"error": "Unknown endpoint"})


def main():
    parser = argparse.ArgumentParser(description="Start the Alexandria Press Book Creator server.")
    parser.add_argument("--port", type=int, default=8090, help="Port to listen on (default: 8090)")
    args = parser.parse_args()
    server = HTTPServer(("127.0.0.1", args.port), CreatorRequestHandler)
    print(f"Alexandria Press & Book Creator Server listening on http://127.0.0.1:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
