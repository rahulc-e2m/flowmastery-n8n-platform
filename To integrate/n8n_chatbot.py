import requests
import openai
import json
import re
import google.generativeai as genai
from datetime import datetime, timezone
from config import N8N_API_URL, N8N_API_KEY, GEMINI_API_KEY
import time # Added for timing logs

# --- LLM Clients Setup ---

# OpenRouter Client (commented out - credits finished)
# client = openai.OpenAI(
#     api_key=OPENROUTER_API_KEY,
#     base_url="https://openrouter.ai/api/v1"
# )

# Gemini Client (primary)
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.5-flash-lite-preview-06-17')
else:
    print("Warning: GEMINI_API_KEY not set. Please add your Gemini API key to config.py")
    gemini_model = None

# --- API Call to n8n ---
def call_n8n_api(method, path, params=None, data=None):
    headers = {
        "accept": "application/json",
        "X-N8N-API-KEY": N8N_API_KEY,
        "Content-Type": "application/json",
    }
    url = f"{N8N_API_URL}{path}"
    print(f"\n[LOG] --- Sending API Request ---")
    print(f"Method: {method}")
    print(f"URL: {url}")
    print(f"Params: {params}")
    print(f"Data: {json.dumps(data) if data else None}")
    
    start_time = time.time()
    resp = requests.request(method, url, headers=headers, params=params, json=data)
    end_time = time.time()
    print(f"[LOG] Status: {resp.status_code}")
    print(f"[LOG] API Call Duration: {end_time - start_time:.2f} seconds")
    try:
        response_data = resp.json()
    except Exception:
        response_data = resp.text

    try:
        preview = json.dumps(response_data)[:500] + "..."
    except Exception:
        preview = str(response_data)[:500] + "..."
    print(f"[LOG] --- Raw API Response Preview ---\n{preview}\n")

    return response_data

# --- Supported GET Endpoints Spec ---
GET_ENDPOINTS_SPEC = {
    "/users": {
        "path": "/users",
        "path_params": {},
        "query_params": {
            "limit": {"type": "int", "max": 250, "default": 100},
            "cursor": {"type": "string"},
            "includeRole": {"type": "bool", "default": False},
            "projectId": {"type": "string"},
        },
    },
    "/users/{id}": {
        "path": "/users/{id}",
        "path_params": {"id": {"type": "string"}},
        "query_params": {
            "includeRole": {"type": "bool", "default": False},
        },
    },
    "/executions": {
        "path": "/executions",
        "path_params": {},
        "query_params": {
            "includeData": {"type": "bool"},
            "status": {"type": "enum", "values": ["error", "success", "waiting"]},
            "workflowId": {"type": "string"},
            "projectId": {"type": "string"},
            "limit": {"type": "int", "max": 250, "default": 100},
            "cursor": {"type": "string"},
        },
    },
    "/executions/{id}": {
        "path": "/executions/{id}",
        "path_params": {"id": {"type": "number"}},
        "query_params": {
            "includeData": {"type": "bool"},
        },
    },
    "/workflows": {
        "path": "/workflows",
        "path_params": {},
        "query_params": {
            "active": {"type": "bool"},
            "tags": {"type": "string"},
            "name": {"type": "string"},
            "projectId": {"type": "string"},
            "excludePinnedData": {"type": "bool"},
            "limit": {"type": "int", "max": 250, "default": 100},
            "cursor": {"type": "string"},
        },
    },
    "/workflows/{id}": {
        "path": "/workflows/{id}",
        "path_params": {"id": {"type": "string"}},
        "query_params": {
            "excludePinnedData": {"type": "bool"},
        },
    },
    "/workflows/{id}/tags": {
        "path": "/workflows/{id}/tags",
        "path_params": {"id": {"type": "string"}},
        "query_params": {},
    },
    "/credentials/schema/{credentialTypeName}": {
        "path": "/credentials/schema/{credentialTypeName}",
        "path_params": {"credentialTypeName": {"type": "string"}},
        "query_params": {},
    },
    "/tags": {
        "path": "/tags",
        "path_params": {},
        "query_params": {
            "limit": {"type": "int", "max": 250, "default": 100},
            "cursor": {"type": "string"},
        },
    },
    "/tags/{id}": {
        "path": "/tags/{id}",
        "path_params": {"id": {"type": "string"}},
        "query_params": {},
    },
    "/variables": {
        "path": "/variables",
        "path_params": {},
        "query_params": {
            "limit": {"type": "int", "max": 250, "default": 100},
            "cursor": {"type": "string"},
        },
    },
    "/projects": {
        "path": "/projects",
        "path_params": {},
        "query_params": {
            "limit": {"type": "int", "max": 250, "default": 100},
            "cursor": {"type": "string"},
        },
    },
}

n8n_ENDPOINTS_DOC = """
n8n Public API endpoints (derived from the provided OpenAPI file). Use only these.

GET:
- /users (params: limit<=250, cursor, includeRole, projectId)
- /users/{id} (params: includeRole)
- /executions (params: includeData, status in [error, success, waiting], workflowId, projectId, limit<=250, cursor)
- /executions/{id} (params: includeData)
- /workflows (params: active, tags, name, projectId, excludePinnedData, limit<=250, cursor)
- /workflows/{id} (params: excludePinnedData)
- /workflows/{id}/tags
- /credentials/schema/{credentialTypeName}
- /tags (params: limit<=250, cursor)
- /tags/{id}
- /variables (params: limit<=250, cursor)
- /projects (params: limit<=250, cursor)

POST:
- /audit (body: audit options object)
- /credentials (body: credential)
- /tags (body: tag)
- /variables (body: variable)
- /projects (body: project)
- /users (body: array of {email, role})
- /login (body: {email, password})
- /logout (no body)
- /source-control/pull (body: pull options)
- /workflows (body: workflow)
- /workflows/{id}/activate (no body)
- /workflows/{id}/deactivate (no body)
- /projects/{projectId}/users (body: {relations: [{userId, role}]})

PUT:
- /workflows/{id} (body: workflow)
- /variables/{id} (body: variable)
- /projects/{projectId} (body: project)
- /workflows/{id}/transfer (body: {destinationProjectId})
- /credentials/{id}/transfer (body: {destinationProjectId})
- /workflows/{id}/tags (body: tagIds)
- /tags/{id} (body: tag)

PATCH:
- /users/{id}/role (body: {newRoleName in [global:admin, global:member]})
- /projects/{projectId}/users/{userId} (body: {role})

DELETE:
- /workflows/{id}
- /executions/{id}
- /credentials/{id}
- /tags/{id}
- /variables/{id}
- /projects/{projectId}
- /projects/{projectId}/users/{userId}
- /users/{id}

Rules:
- Output JSON with keys: method, path, params, data.
- Do not include query strings in path; put query params in params, body in data.
- Omit unknown fields. Cap limit at 250.
"""

# --- Non-GET Endpoint Specifications ---
POST_ENDPOINTS_SPEC = {
    "/audit": {
        "path": "/audit",
        "path_params": {},
        "query_params": {},
        "raw_body": True,
    },
    "/workflows": {
        "path": "/workflows",
        "path_params": {},
        "query_params": {},
        "body_params": {
            "name": {"type": "string", "required": True},
            "nodes": {"type": "array", "required": True},
            "connections": {"type": "object", "required": True},
            "settings": {"type": "object"},
            "tags": {"type": "array_string"},
            "active": {"type": "bool"},
        },
    },
    "/credentials": {
        "path": "/credentials",
        "path_params": {},
        "query_params": {},
        "body_params": {
            "name": {"type": "string", "required": True},
            "type": {"type": "string", "required": True},
            "data": {"type": "object", "required": True},
            "nodesAccess": {"type": "array"},
        },
    },
    "/tags": {
        "path": "/tags",
        "path_params": {},
        "query_params": {},
        "body_params": {
            "name": {"type": "string", "required": True},
        },
    },
    "/variables": {
        "path": "/variables",
        "path_params": {},
        "query_params": {},
        "body_params": {
            "key": {"type": "string", "required": True},
            "value": {"type": "string", "required": True},
        },
    },
    "/projects": {
        "path": "/projects",
        "path_params": {},
        "query_params": {},
        "body_params": {
            "name": {"type": "string", "required": True},
        },
    },
    "/users": {
        "path": "/users",
        "path_params": {},
        "query_params": {},
        "raw_body": True,
    },
    "/login": {
        "path": "/login",
        "path_params": {},
        "query_params": {},
        "body_params": {
            "email": {"type": "string", "required": True},
            "password": {"type": "string", "required": True},
        },
    },
    "/logout": {
        "path": "/logout",
        "path_params": {},
        "query_params": {},
        "body_params": {},
    },
    "/source-control/pull": {
        "path": "/source-control/pull",
        "path_params": {},
        "query_params": {},
        "raw_body": True,
    },
    "/workflows/{id}/activate": {
        "path": "/workflows/{id}/activate",
        "path_params": {"id": {"type": "string"}},
        "query_params": {},
        "body_params": {},
    },
    "/workflows/{id}/deactivate": {
        "path": "/workflows/{id}/deactivate",
        "path_params": {"id": {"type": "string"}},
        "query_params": {},
        "body_params": {},
    },
    "/projects/{projectId}/users": {
        "path": "/projects/{projectId}/users",
        "path_params": {"projectId": {"type": "string"}},
        "query_params": {},
        "raw_body": True,
    },
}

PATCH_ENDPOINTS_SPEC = {
    "/users/{id}/role": {
        "path": "/users/{id}/role",
        "path_params": {"id": {"type": "string"}},
        "query_params": {},
        "body_params": {
            "newRoleName": {"type": "enum", "values": ["global:admin", "global:member"], "required": True},
        },
    },
    "/projects/{projectId}/users/{userId}": {
        "path": "/projects/{projectId}/users/{userId}",
        "path_params": {"projectId": {"type": "string"}, "userId": {"type": "string"}},
        "query_params": {},
        "body_params": {
            "role": {"type": "string", "required": True},
        },
    },
}

PUT_ENDPOINTS_SPEC = {
    "/workflows/{id}": {
        "path": "/workflows/{id}",
        "path_params": {"id": {"type": "string"}},
        "query_params": {},
        "body_params": {
            "name": {"type": "string"},
            "nodes": {"type": "array"},
            "connections": {"type": "object"},
            "settings": {"type": "object"},
            "tags": {"type": "array_string"},
        },
    },
    "/variables/{id}": {
        "path": "/variables/{id}",
        "path_params": {"id": {"type": "string"}},
        "query_params": {},
        "body_params": {
            "key": {"type": "string"},
            "value": {"type": "string"},
        },
    },
    "/projects/{projectId}": {
        "path": "/projects/{projectId}",
        "path_params": {"projectId": {"type": "string"}},
        "query_params": {},
        "body_params": {
            "name": {"type": "string"},
        },
    },
    "/workflows/{id}/transfer": {
        "path": "/workflows/{id}/transfer",
        "path_params": {"id": {"type": "string"}},
        "query_params": {},
        "body_params": {
            "destinationProjectId": {"type": "string", "required": True},
        },
    },
    "/credentials/{id}/transfer": {
        "path": "/credentials/{id}/transfer",
        "path_params": {"id": {"type": "string"}},
        "query_params": {},
        "body_params": {
            "destinationProjectId": {"type": "string", "required": True},
        },
    },
    "/workflows/{id}/tags": {
        "path": "/workflows/{id}/tags",
        "path_params": {"id": {"type": "string"}},
        "query_params": {},
        "raw_body": True,
    },
    "/tags/{id}": {
        "path": "/tags/{id}",
        "path_params": {"id": {"type": "string"}},
        "query_params": {},
        "body_params": {
            "name": {"type": "string", "required": True},
        },
    },
}


DELETE_ENDPOINTS_SPEC = {
    "/workflows/{id}": {
        "path": "/workflows/{id}",
        "path_params": {"id": {"type": "string"}},
        "query_params": {},
    },
    "/executions/{id}": {
        "path": "/executions/{id}",
        "path_params": {"id": {"type": "number"}},
        "query_params": {},
    },
    "/projects/{projectId}/users/{userId}": {
        "path": "/projects/{projectId}/users/{userId}",
        "path_params": {"projectId": {"type": "string"}, "userId": {"type": "string"}},
        "query_params": {},
    },
    "/credentials/{id}": {
        "path": "/credentials/{id}",
        "path_params": {"id": {"type": "string"}},
        "query_params": {},
    },
    "/tags/{id}": {
        "path": "/tags/{id}",
        "path_params": {"id": {"type": "string"}},
        "query_params": {},
    },
    "/variables/{id}": {
        "path": "/variables/{id}",
        "path_params": {"id": {"type": "string"}},
        "query_params": {},
    },
    "/projects/{projectId}": {
        "path": "/projects/{projectId}",
        "path_params": {"projectId": {"type": "string"}},
        "query_params": {},
    },
    "/users/{id}": {
        "path": "/users/{id}",
        "path_params": {"id": {"type": "string"}},
        "query_params": {},
    },
}

ENDPOINTS_BY_METHOD = {
    "GET": GET_ENDPOINTS_SPEC,
    "POST": POST_ENDPOINTS_SPEC,
    "PATCH": PATCH_ENDPOINTS_SPEC,
    "PUT": PUT_ENDPOINTS_SPEC,
    "DELETE": DELETE_ENDPOINTS_SPEC,
}

# Removed duplicate ENDPOINTS_DOC (was an older guidance block)

# --- Param Coercion Helpers ---
def _coerce_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    s = str(value).strip().lower()
    if s in {"true", "1", "yes", "y"}:
        return True
    if s in {"false", "0", "no", "n"}:
        return False
    return None

def _coerce_int(value):
    try:
        return int(value)
    except Exception:
        return None

def _coerce_number(value):
    try:
        return int(value)
    except Exception:
        try:
            return float(value)
        except Exception:
            return None

def _normalize_params_for_endpoint(spec, params):
    normalized = {}
    params = params or {}
    for key, meta in spec.get("query_params", {}).items():
        if key in params:
            raw = params[key]
        else:
            raw = meta.get("default")
        if raw is None:
            continue
        t = meta.get("type")
        if t == "bool":
            b = _coerce_bool(raw)
            if b is None:
                continue
            normalized[key] = str(b).lower()
        elif t == "int":
            iv = _coerce_int(raw)
            if iv is None:
                continue
            if "max" in meta and iv > meta["max"]:
                iv = meta["max"]
            normalized[key] = iv
        elif t == "enum":
            s = str(raw)
            if s in meta.get("values", []):
                normalized[key] = s
        else:
            normalized[key] = str(raw)
    return normalized

def _coerce_array_string(value):
    if value is None:
        return None
    if isinstance(value, list):
        return [str(v) for v in value]
    return [s.strip() for s in str(value).split(',') if s.strip()]

def _normalize_body_for_endpoint(spec, body):
    body = body or {}
    normalized = {}
    for key, meta in spec.get("body_params", {}).items():
        present = key in body
        raw = body.get(key)
        if not present and not meta.get("required"):
            continue
        t = meta.get("type")
        if t == "bool":
            b = _coerce_bool(raw)
            if b is None:
                continue
            normalized[key] = b
        elif t == "int":
            iv = _coerce_int(raw)
            if iv is None:
                continue
            normalized[key] = iv
        elif t == "number":
            nv = _coerce_number(raw)
            if nv is None:
                continue
            normalized[key] = nv
        elif t == "enum":
            s = str(raw)
            if s in meta.get("values", []):
                normalized[key] = s
        elif t == "object":
            if isinstance(raw, dict):
                normalized[key] = raw
        elif t == "array":
            if isinstance(raw, list):
                normalized[key] = raw
        elif t == "array_string":
            arr = _coerce_array_string(raw)
            if arr is not None:
                normalized[key] = arr
        else:
            if raw is not None:
                normalized[key] = str(raw)
    return normalized

def _match_endpoint_spec(path):
    if path in GET_ENDPOINTS_SPEC:
        return GET_ENDPOINTS_SPEC[path], {}
    for template, spec in GET_ENDPOINTS_SPEC.items():
        if "{" not in template:
            continue
        regex = re.escape(template)
        regex = regex.replace(re.escape("{id}"), r"(?P<id>[^/]+)")
        regex = regex.replace(re.escape("{credentialTypeName}"), r"(?P<credentialTypeName>[^/]+)")
        pattern = f"^{regex}$"
        m = re.match(pattern, path)
        if m:
            return spec, m.groupdict()
    return None, None
# --- Trim Workflows to Only Needed Fields ---
def extract_workflow_summary(workflows, active_filter=None, limit=None):
    summary = []
    if isinstance(workflows, list):
        for wf in workflows:
            if active_filter is None or wf.get("active") == active_filter:
                summary.append({
                    "id": wf.get("id"),
                    "name": wf.get("name"),
                    "active": wf.get("active")
                })
        if limit:
            summary = summary[:limit]
    return summary

# --- Token-Safe String Prep ---
def prepare_api_response_for_prompt(api_response, max_chars=15000):
    try:
        s = json.dumps(api_response, ensure_ascii=False)
    except Exception:
        s = str(api_response)
    if len(s) > max_chars:
        return s[:max_chars] + "\n\n[TRUNCATED]"
    return s

# --- Normalize Keys from LLM Output ---
def normalize_action_keys(action):
    if "endpoint" in action and "path" not in action:
        action["path"] = action.pop("endpoint")
    if "parameters" in action and "params" not in action:
        action["params"] = action.pop("parameters")
    if "params" not in action:
        action["params"] = {}
    if "data" not in action:
        action["data"] = None
    return action

# --- Get API Action from LLM ---
def get_llm_action(user_query):
    system = f"""
You are an agent that helps users interact with their n8n instance via the n8n REST API.
Choose the correct method (GET, POST, PATCH, PUT, DELETE), endpoint, and parameters/body from the allowed lists and output the API call as JSON.

{n8n_ENDPOINTS_DOC}

Output requirements:
- Output valid JSON only, no commentary.
- JSON keys: "method", "path", "params", "data".
- "path" must be one of the allowed endpoints with any required path parameters filled in (e.g. /users/john@example.com or /executions/123).
- Never include a query string in the path; put all query parameters into "params" and the request body into "data".
- If the user asks for a limit, cap it at 250.

Examples:
{{"method": "GET", "path": "/workflows", "params": {{"active": "true"}}, "data": null}}
{{"method": "POST", "path": "/executions", "params": {{}}, "data": {{"workflowId": "abc123", "executionMode": "manual"}}}}
"""
    
    if gemini_model:
        # Use Gemini
        prompt = f"{system}\n\nUser query: {user_query}\n\nOutput only valid JSON:"
        try:
            llm_start_time = time.time()
            response = gemini_model.generate_content(prompt)
            llm_end_time = time.time()
            print(f"[LOG] LLM Action Generation Duration: {llm_end_time - llm_start_time:.2f} seconds")
            result = response.text.strip()
            print(f"\n[LOG] --- LLM Action JSON ---\n{result}\n")
            action = json.loads(result)
            action = normalize_action_keys(action)
            return action
        except Exception as e:
            print("Error parsing LLM action:", e)
            return None
    else:
        # Fallback to OpenRouter (commented out)
        # response = client.chat.completions.create(
        #     model="openai/gpt-3.5-turbo",
        #     messages=[
        #         {"role": "system", "content": system},
        #         {"role": "user", "content": user_query}
        #     ],
        #     temperature=0
        # )
        # try:
        #     result = response.choices[0].message.content
        #     print(f"\n[LOG] --- LLM Action JSON ---\n{result}\n")
        #     action = json.loads(result)
        #     action = normalize_action_keys(action)
        #     return action
        # except Exception as e:
        #     print("Error parsing LLM action:", e)
        #     return None
        print("Error: No LLM client available. Please set GEMINI_API_KEY in config.py")
        return None

# --- Format Responses Per Endpoint ---
def _format_list(items, item_formatter):
    if not items:
        return "No results found."
    lines = []
    for idx, it in enumerate(items, start=1):
        lines.append(f"{idx}. {item_formatter(it)}")
    return "\n".join(lines)

def _fmt_user(u):
    full_name = " ".join([p for p in [u.get('firstName'), u.get('lastName')] if p])
    label = u.get('email') or full_name or 'User'
    return f"{label} | ID: {u.get('id','')}"

def _safe_parse_iso(ts: str):
    try:
        if not ts:
            return None
        # Handle ISO with Z suffix
        ts2 = str(ts).replace('Z', '+00:00')
        return datetime.fromisoformat(ts2)
    except Exception:
        return None

def _fmt_dt(ts: str):
    dt = _safe_parse_iso(ts)
    if not dt:
        return ts or ''
    # Compact human-readable: YYYY-MM-DD HH:MM:SS UTC
    try:
        return dt.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    except Exception:
        return ts or ''

def _fmt_duration_ms(start_ts: str, end_ts: str):
    start = _safe_parse_iso(start_ts)
    end = _safe_parse_iso(end_ts)
    if not start or not end:
        return None
    ms = int((end - start).total_seconds() * 1000)
    if ms < 0:
        return None
    # Format as s.ms
    seconds = ms / 1000.0
    return f"{seconds:.3f}s"

def _fmt_execution(x):
    status = x.get('status')
    # Some responses may not include status; infer using documented statuses
    if not status:
        finished = x.get('finished')
        if finished is True:
            status = 'success'
        elif finished is False:
            status = 'waiting'
        else:
            status = ''
    started = _fmt_dt(x.get('startedAt'))
    stopped = _fmt_dt(x.get('stoppedAt'))
    duration = _fmt_duration_ms(x.get('startedAt'), x.get('stoppedAt'))
    duration_part = f" | duration: {duration}" if duration else ""
    return (
        f"ID: {x.get('id','')} | status: {status} | workflowId: {x.get('workflowId','')}"
        f" | started: {started} | stopped: {stopped}{duration_part}"
    )

def _fmt_workflow(w):
    name = w.get('name', 'Unnamed')
    active = w.get('active')
    created = _fmt_dt(w.get('createdAt')) if 'createdAt' in w else ''
    updated = _fmt_dt(w.get('updatedAt')) if 'updatedAt' in w else ''
    parts = [f"Name: {name}", f"ID: {w.get('id','')}", f"active: {active}"]
    if created:
        parts.append(f"created: {created}")
    if updated:
        parts.append(f"updated: {updated}")
    return " | ".join(parts)

def _fmt_tag(t):
    return f"{t.get('name','')} | ID: {t.get('id','')}"

def _fmt_variable(v):
    return f"{v.get('key','')} = {v.get('value','')}"

def _fmt_project(p):
    return f"{p.get('name','')} | ID: {p.get('id','')}"

def format_api_result_for_user(path, raw_response):
    data_payload = raw_response
    if isinstance(raw_response, dict) and "data" in raw_response:
        data_payload = raw_response["data"]

    if re.match(r"^/users/[^/]+$", path):
        u = data_payload if isinstance(data_payload, dict) else raw_response
        if not isinstance(u, dict):
            return "No user found."
        full_name = " ".join([p for p in [u.get('firstName'), u.get('lastName')] if p])
        parts = [f"ID: {u.get('id','')}"]
        if full_name:
            parts.append(f"Name: {full_name}")
        if u.get('email'):
            parts.append(f"Email: {u.get('email')}")
        role = u.get('role', {}).get('name') if isinstance(u.get('role'), dict) else None
        if role:
            parts.append(f"Role: {role}")
        return " | ".join(parts)

    if re.match(r"^/executions/[^/]+$", path):
        x = data_payload if isinstance(data_payload, dict) else raw_response
        if not isinstance(x, dict):
            return "No execution found."
        return f"Execution {x.get('id','')}: status={x.get('status','')}, workflowId={x.get('workflowId','')}"

    if re.match(r"^/workflows/[^/]+/tags$", path):
        items = data_payload if isinstance(data_payload, list) else []
        return _format_list(items, _fmt_tag)

    if re.match(r"^/workflows/[^/]+$", path):
        w = data_payload if isinstance(data_payload, dict) else raw_response
        if not isinstance(w, dict):
            return "No workflow found."
        return f"Workflow {w.get('name','')} | ID: {w.get('id','')} | active: {w.get('active')}"

    if path == "/users":
        items = data_payload if isinstance(data_payload, list) else []
        return _format_list(items, _fmt_user)
    if path == "/executions":
        items = data_payload if isinstance(data_payload, list) else []
        return _format_list(items, _fmt_execution)
    if path == "/workflows":
        items = data_payload if isinstance(data_payload, list) else []
        return _format_list(items, _fmt_workflow)
    if path == "/tags":
        items = data_payload if isinstance(data_payload, list) else []
        return _format_list(items, _fmt_tag)
    if path == "/variables":
        items = data_payload if isinstance(data_payload, list) else []
        return _format_list(items, _fmt_variable)
    if path == "/projects":
        items = data_payload if isinstance(data_payload, list) else []
        return _format_list(items, _fmt_project)
    if re.match(r"^/tags/[^/]+$", path):
        t = data_payload if isinstance(data_payload, dict) else raw_response
        if not isinstance(t, dict):
            return "No tag found."
        return f"Tag {t.get('name','')} | ID: {t.get('id','')}"
    if re.match(r"^/credentials/schema/[^/]+$", path):
        schema = data_payload if isinstance(data_payload, dict) else raw_response
        if not isinstance(schema, dict):
            return "No schema found."
        keys = ", ".join(list(schema.keys())[:10])
        return f"Credential schema keys: {keys}" if keys else "Empty schema."

    try:
        return json.dumps(data_payload, ensure_ascii=False)[:1500]
    except Exception:
        return str(data_payload)[:1500]

# --- Action Validation & Normalization ---
def _match_endpoint_spec_with_method(method, path):
    method = method.upper()
    spec_map = ENDPOINTS_BY_METHOD.get(method)
    if not spec_map:
        return None, None
    if path in spec_map:
        return spec_map[path], {}
    for template, spec in spec_map.items():
        if "{" not in template:
            continue
        regex = re.escape(template)
        regex = regex.replace(re.escape("{id}"), r"(?P<id>[^/]+)")
        regex = regex.replace(re.escape("{credentialTypeName}"), r"(?P<credentialTypeName>[^/]+)")
        pattern = f"^{regex}$"
        m = re.match(pattern, path)
        if m:
            return spec, m.groupdict()
    return None, None

def validate_and_normalize_action(action):
    if not action:
        return None, "Missing action."
    method = action.get("method", "").upper()
    if method not in ENDPOINTS_BY_METHOD:
        return None, "Unsupported method."
    raw_path = action.get("path")
    if not raw_path or not raw_path.startswith("/"):
        return None, "Path must start with '/'."
    if "?" in raw_path:
        base_path, _ = raw_path.split("?", 1)
    else:
        base_path = raw_path
    spec, templated_values = _match_endpoint_spec_with_method(method, base_path)
    if not spec:
        return None, "Unsupported endpoint."
    path_params = {}
    for k, meta in spec.get("path_params", {}).items():
        v = templated_values.get(k) if templated_values else None
        if v is None:
            return None, f"Missing path parameter: {k}"
        t = meta.get("type")
        if t == "number":
            nv = _coerce_number(v)
            if nv is None:
                return None, f"Invalid number for {k}"
            path_params[k] = str(int(nv)) if isinstance(nv, (int, float)) else str(nv)
        else:
            path_params[k] = str(v)
    normalized_params = _normalize_params_for_endpoint(spec, action.get("params", {}))
    normalized_body = None
    if method in {"POST", "PATCH", "PUT"}:
        normalized_body = _normalize_body_for_endpoint(spec, action.get("data", {}))
        # Ensure required fields are present for POST
        for key, meta in spec.get("body_params", {}).items():
            if meta.get("required") and key not in normalized_body:
                return None, f"Missing required body field: {key}"
    normalized_path = spec["path"]
    for k, v in path_params.items():
        normalized_path = normalized_path.replace("{" + k + "}", v)
    normalized_action = {
        "method": method,
        "path": normalized_path,
        "params": normalized_params,
        "data": normalized_body,
    }
    return normalized_action, None

# --- Main Answer Function ---
def answer_user(user_query):
    print(f"\n[LOG] --- User Query ---\n{user_query}\n")

    # Step 1: Ask LLM what to call
    action = get_llm_action(user_query)
    if not action or "method" not in action or "path" not in action:
        return "Sorry, I could not determine the correct n8n API action for your request."

    # Step 2: Validate & normalize action
    normalized_action, err = validate_and_normalize_action(action)
    if err:
        return f"Sorry, your request maps to an unsupported call: {err}"

    # Step 3: Call n8n API
    raw_response = call_n8n_api(
        normalized_action['method'],
        normalized_action['path'],
        normalized_action.get('params'),
        normalized_action.get('data'),
    )

    # Step 4: Format result for user
    format_start_time = time.time()
    formatted = format_api_result_for_user(normalized_action['path'], raw_response)
    format_end_time = time.time()
    print(f"[LOG] Response Formatting Duration: {format_end_time - format_start_time:.2f} seconds")
    return formatted

