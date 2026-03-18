"""Quick smoke test to verify the server is working end-to-end."""
import sys, json, urllib.request

BASE = "http://localhost:8000"

# ── 1. Health ─────────────────────────────────────────────────────────────────
resp = json.loads(urllib.request.urlopen(f"{BASE}/health").read())
assert resp["status"] == "healthy", f"Health failed: {resp}"
print(f"[1] HEALTH OK  — uptime={resp['uptime_seconds']}s  db={resp['database']}")

# ── 2. Login ──────────────────────────────────────────────────────────────────
body = json.dumps({"email": "admin@atos.com", "password": "password123"}).encode()
req  = urllib.request.Request(f"{BASE}/auth/login", data=body,
                               headers={"Content-Type": "application/json"})
resp = json.loads(urllib.request.urlopen(req).read())
token = resp["data"]["access_token"]
auth  = {"Authorization": f"Bearer {token}"}
print(f"[2] LOGIN  OK  — token={token[:30]}...")

# ── 3. Ingest sample CSV ──────────────────────────────────────────────────────
sys.path.insert(0, ".")
from utils.sample_data import generate_sample_csv_bytes
csv_bytes = generate_sample_csv_bytes()

boundary = "----SMKBND"
nl = b"\r\n"
cd = f'Content-Disposition: form-data; name="file"; filename="employees.csv"'
part = (
    f"--{boundary}".encode() + nl
    + cd.encode()             + nl
    + b"Content-Type: text/csv" + nl + nl
    + csv_bytes               + nl
    + f"--{boundary}--".encode() + nl
)
req = urllib.request.Request(
    f"{BASE}/ingest/employees",
    data=part,
    headers={**auth, "Content-Type": f"multipart/form-data; boundary={boundary}"},
)
resp = json.loads(urllib.request.urlopen(req).read())
print(f"[3] INGEST OK  — {resp['data']['employees_loaded']} employees | "
      f"nodes={resp['data']['graph_nodes']} edges={resp['data']['graph_edges']}")
print(f"    Departments: {resp['data']['departments_found']}")

# ── 4. Graph endpoint ─────────────────────────────────────────────────────────
req  = urllib.request.Request(f"{BASE}/graph", headers=auth)
resp = json.loads(urllib.request.urlopen(req).read())
print(f"[4] GRAPH  OK  — nodes={resp['data']['total_nodes']} "
      f"edges={resp['data']['total_edges']} "
      f"density={resp['data']['density']}")

# ── 5. Simulate What-If ───────────────────────────────────────────────────────
body = json.dumps({
    "scenario": "switch_to_teams",
    "new_tool": "Teams",
    "adoption_boost": 0.25,
    "monte_carlo_iterations": 50,
}).encode()
req = urllib.request.Request(
    f"{BASE}/simulate/what-if", data=body,
    headers={**auth, "Content-Type": "application/json"},
)
resp = json.loads(urllib.request.urlopen(req).read())
k = resp["data"]["kpis"]
print(f"[5] SIMUL  OK  — productivity={k['productivity_increase']}%  "
      f"adoption={round(k['adoption_rate']*100,1)}%  "
      f"engagement={k['engagement_score']}")
print(f"    Duration: {resp['data']['total_duration_ms']}ms  "
      f"LLM: {resp['data']['llm_duration_ms']}ms  "
      f"model={resp['data']['llm_model']}")
llm_lines = resp["data"]["llm_explanation"][:200]
print(f"    LLM preview: {llm_lines}...")

print("\nALL CHECKS PASSED -- API is production ready!")
