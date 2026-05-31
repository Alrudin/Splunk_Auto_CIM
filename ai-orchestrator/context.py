import asyncio
import httpx
import json
import litellm
from config import (
    SPLUNK_HOST,
    SPLUNK_PORT,
    SPLUNK_USER,
    SPLUNK_PASSWORD,
    OLLAMA_BASE_URL,
    LLM_MODEL
)

SPLUNK_REST_BASE = f"https://{SPLUNK_HOST}:{SPLUNK_PORT}"

# Monkey-patch httpx.AsyncClient to disable SSL verification
original_init = httpx.AsyncClient.__init__
def patched_init(self, *args, **kwargs):
    kwargs["verify"] = False
    original_init(self, *args, **kwargs)
httpx.AsyncClient.__init__ = patched_init

async def _gather_context(prompt_user=False):
    print("Fetching highest priority sourcetype from KV store...")
    kv_url = f"{SPLUNK_REST_BASE}/servicesNS/nobody/Splunk_Auto_CIM_State/storage/collections/data/remediation_queue"
    auth = (SPLUNK_USER, SPLUNK_PASSWORD)
    
    target_item = None
    async with httpx.AsyncClient(verify=False) as client:
        resp = await client.get(kv_url, auth=auth)
        if resp.status_code == 200:
            items = resp.json()
            pending_items = [i for i in items if i.get("status") == "pending"]
            if not pending_items:
                print("No pending items in the remediation queue.")
                return None
            
            # Sort by priority_score descending
            pending_items.sort(key=lambda x: float(x.get("priority_score", 0)), reverse=True)
            target_item = pending_items[0]
            print(f"Highest priority sourcetype: {target_item['sourcetype']} (Score: {target_item.get('priority_score')})")
        else:
            print(f"Failed to fetch from KV store: {resp.status_code} - {resp.text}")
            return None

    sourcetype = target_item['sourcetype']
    source = target_item.get('source', '*')
    print(f"Fetching sample raw events for sourcetype={sourcetype} and source={source} via REST API...")
    search_query = f'search index=* sourcetype="{sourcetype}" source="{source}" | head 5'
    data = {"search": search_query, "output_mode": "json", "earliest_time": "0"}
    search_url = f"{SPLUNK_REST_BASE}/services/search/jobs/export"
    
    raw_events = []
    async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
        resp = await client.post(search_url, data=data, auth=auth)
        if resp.status_code == 200:
            for line in resp.text.strip().split('\n'):
                if line:
                    try:
                        row = json.loads(line)
                        if "result" in row and "_raw" in row["result"]:
                            raw_events.append(row["result"]["_raw"])
                    except Exception as e:
                        pass
        else:
            print(f"Failed to fetch sample events: {resp.status_code} - {resp.text}")

    if not raw_events:
        print(f"No sample events found for sourcetype: {sourcetype} and source: {source}")
        return None

    print(f"Found {len(raw_events)} sample events.")
    print("Classifying Data Model using Ollama...")
    
    events_text = "\n".join(raw_events)
    prompt = f"""
Analyze the following Splunk raw events for the sourcetype '{sourcetype}' and source '{source}'.
Determine the most appropriate Splunk Common Information Model (CIM) Data Model for these events.
Common Data Models include: Authentication, Network Traffic, Intrusion Detection, Web, Endpoint, etc.

Raw Events:
{events_text}

Reply ONLY with the exact name of the CIM Data Model (e.g., "Network Traffic" or "Authentication").
"""
    
    try:
        response = litellm.completion(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            api_base=OLLAMA_BASE_URL,
            timeout=60.0
        )
        suggested_dm = response.choices[0].message.content.strip()
        print(f"\nLLM Suggested Data Model: {suggested_dm}")
    except Exception as e:
        print(f"Error calling LLM: {e}")
        suggested_dm = "Unknown"

    target_dm = suggested_dm
    if prompt_user:
        user_input = input(f"Confirm Target Data Model (press Enter to accept '{suggested_dm}' or type an override): ")
        if user_input.strip():
            target_dm = user_input

    print(f"Confirmed Target Data Model: {target_dm}")
    
    # Optionally update the KV store to mark it as classified/in_progress with the target_dm
    update_url = f"{kv_url}/{target_item['_key']}"
    target_item['target_dm'] = target_dm
    target_item['status'] = 'in_progress'
    
    payload = target_item.copy()
    payload.pop('_key', None)
    payload.pop('_user', None)
    
    async with httpx.AsyncClient(verify=False) as client:
        resp = await client.post(
            update_url,
            json=payload,
            auth=auth,
            headers={"Content-Type": "application/json"}
        )
        if resp.status_code in [200, 201]:
            print(f"Updated KV store status for {sourcetype} to 'in_progress'.")
        else:
            print(f"Failed to update KV store: {resp.status_code} - {resp.text}")

    return target_dm

def gather_context(prompt_user=False):
    """
    Fetches the highest priority sourcetype from the KV store,
    fetches raw events via MCP, and uses litellm to classify the CIM Data Model.
    """
    return asyncio.run(_gather_context(prompt_user))
