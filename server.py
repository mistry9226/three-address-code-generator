"""
Lightweight Built-in HTTP Server & API for TAC Generator Web Visualizer.
Uses Python standard library (no Flask/FastAPI required).
"""
import http.server
import json
import os
import sys
import urllib.parse
from typing import Dict, Any

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from tac import compile_to_tac, simulate_tac


class TACRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.join(BASE_DIR, "web"), **kwargs)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)

        if url.path == "/api/examples":
            self._handle_get_examples()
        elif url.path.startswith("/api/examples/"):
            example_name = os.path.basename(url.path)
            self._handle_get_single_example(example_name)
        else:
            # Fallback to serving web/ directory files
            super().do_GET()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)

        if url.path == "/api/compile":
            self._handle_compile()
        elif url.path == "/api/simulate":
            self._handle_simulate()
        else:
            self.send_error(404, "Endpoint not found")

    def _send_json(self, status_code: int, data: Dict[str, Any]):
        response = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(response)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _read_body_json(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        return json.loads(body) if body else {}

    def _handle_get_examples(self):
        examples_dir = os.path.join(BASE_DIR, "examples")
        examples = []
        if os.path.exists(examples_dir):
            for fname in sorted(os.listdir(examples_dir)):
                if fname.endswith(".c") or fname.endswith(".txt"):
                    fpath = os.path.join(examples_dir, fname)
                    with open(fpath, "r", encoding="utf-8") as f:
                        content = f.read()
                    examples.append({
                        "name": fname,
                        "title": fname.replace("_", " ").replace(".c", "").title(),
                        "content": content
                    })
        self._send_json(200, {"examples": examples})

    def _handle_get_single_example(self, name: str):
        examples_dir = os.path.join(BASE_DIR, "examples")
        fpath = os.path.join(examples_dir, name)
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            self._send_json(200, {"name": name, "content": content})
        else:
            self._send_json(404, {"error": "Example not found"})

    def _handle_compile(self):
        try:
            req = self._read_body_json()
            source = req.get("code", "")
            optimize = req.get("optimize", True)

            if not source.strip():
                self._send_json(400, {"error": "Source code cannot be empty"})
                return

            res = compile_to_tac(source, optimize=optimize)
            self._send_json(200, {
                "success": True,
                "linear_tac": res.linear_tac,
                "quadruples": res.quadruples,
                "triples": res.triples,
                "indirect_triples": res.indirect_triples,
                "ast": res.ast.to_dict(),
                "cfg": res.cfg.to_dict(),
                "optimized_linear_tac": res.optimized_linear_tac,
                "optimizer_stats": res.optimizer_stats
            })
        except Exception as e:
            self._send_json(400, {"success": False, "error": str(e)})

    def _handle_simulate(self):
        try:
            req = self._read_body_json()
            source = req.get("code", "")
            optimize = req.get("optimize", False)

            if not source.strip():
                self._send_json(400, {"error": "Source code cannot be empty"})
                return

            res = compile_to_tac(source, optimize=optimize)
            target_instrs = res.optimized_instructions if (optimize and res.optimized_instructions) else res.tac_instructions
            user_vars, logs, trace = simulate_tac(target_instrs)

            self._send_json(200, {
                "success": True,
                "variables": user_vars,
                "logs": logs,
                "trace": trace,
                "total_steps": len(trace)
            })
        except Exception as e:
            self._send_json(400, {"success": False, "error": str(e)})


def run_server(port: int = 8000):
    server_address = ("127.0.0.1", port)
    httpd = http.server.HTTPServer(server_address, TACRequestHandler)
    print(f"TAC Generator Web Server running at http://127.0.0.1:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()


if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
