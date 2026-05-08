#!/usr/bin/env python3
"""Serve a local approval page and save confirmed LaTeX review selections."""

from __future__ import annotations

import argparse
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from create_approval_page import html_document, load_items


class ApprovalHandler(BaseHTTPRequestHandler):
    items: list[dict[str, Any]] = []
    output_json: Path
    title: str
    auto_close_window = True
    exit_on_confirm = False
    confirmed = False

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path not in {"/", "/approval"}:
            self._send(404, b"Not found", "text/plain; charset=utf-8")
            return
        html = html_document(self.items, self.title, "/approve", self.auto_close_window).encode("utf-8")
        self._send(200, html, "text/html; charset=utf-8")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/cancel":
            cancelled = {
                "cancelled": True,
                "approved_ids": [],
                "approved_items": [],
                "ignored_ids": [],
                "ignored_items": [],
            }
            self.output_json.parent.mkdir(parents=True, exist_ok=True)
            self.output_json.write_text(json.dumps(cancelled, ensure_ascii=False, indent=2), encoding="utf-8")
            type(self).confirmed = True
            self._send(200, json.dumps({"ok": True, **cancelled}, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        if path != "/approve":
            self._send(404, b"Not found", "text/plain; charset=utf-8")
            return
        length = int(self.headers.get("Content-Length", "0"))
        data = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        allowed = {str(item["id"]) for item in self.items}
        approved_ids = []
        for item in data.get("approved_ids", []):
            item_id = str(item)
            if item_id in allowed and item_id not in approved_ids:
                approved_ids.append(item_id)
        ignored_ids = []
        for item in data.get("ignored_ids", []):
            item_id = str(item)
            if item_id in allowed and item_id not in approved_ids and item_id not in ignored_ids:
                ignored_ids.append(item_id)
        approved = {
            "cancelled": False,
            "approved_ids": approved_ids,
            "approved_items": [item for item in self.items if str(item["id"]) in set(approved_ids)],
            "ignored_ids": ignored_ids,
            "ignored_items": [item for item in self.items if str(item["id"]) in set(ignored_ids)],
        }
        self.output_json.parent.mkdir(parents=True, exist_ok=True)
        self.output_json.write_text(json.dumps(approved, ensure_ascii=False, indent=2), encoding="utf-8")
        type(self).confirmed = True
        self._send(200, json.dumps({"ok": True, **approved}, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")
        if self.exit_on_confirm:
            threading.Thread(target=self.server.shutdown, daemon=True).start()


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve a local LaTeX review approval page.")
    parser.add_argument("items_json", type=Path, help="JSON file containing review items.")
    parser.add_argument("--output-json", type=Path, required=True, help="Where to save confirmed approvals.")
    parser.add_argument("--title", default="Revision Review")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0, help="Use 0 to choose an available port.")
    parser.add_argument("--open-browser", action="store_true", help="Open the approval page in the system default browser.")
    parser.add_argument("--exit-on-confirm", action="store_true", help="Stop the local server after approval is confirmed.")
    parser.add_argument("--no-close-window", action="store_true", help="Do not ask the page to close itself after confirmation.")
    args = parser.parse_args()

    handler = type("ConfiguredApprovalHandler", (ApprovalHandler,), {})
    handler.items = load_items(args.items_json)
    handler.output_json = args.output_json
    handler.title = args.title
    handler.auto_close_window = not args.no_close_window
    handler.exit_on_confirm = args.exit_on_confirm

    server = ThreadingHTTPServer((args.host, args.port), handler)
    host, port = server.server_address
    url = f"http://{host}:{port}/approval"
    print(url, flush=True)
    print(f"APPROVAL_JSON={args.output_json}", flush=True)
    if args.open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
