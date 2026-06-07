import json
import asyncio
import httpx
import os
import litellm
from models import GenerationOutput
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

async def _generate_configurations():
    print("Fetching 'in_progress' sourcetypes from KV store...")
    kv_url = f"{SPLUNK_REST_BASE}/servicesNS/nobody/Splunk_Auto_CIM_State/storage/collections/data/remediation_queue"
    auth = (SPLUNK_USER, SPLUNK_PASSWORD)
    
    target_item = None
    async with httpx.AsyncClient(verify=False) as client:
        resp = await client.get(kv_url, auth=auth)
        if resp.status_code == 200:
            items = resp.json()
            in_progress_items = [i for i in items if i.get("status") == "in_progress"]
            if not in_progress_items:
                print("No 'in_progress' items found. Please run 'context' phase first.")
                return
            
            # Sort by priority_score descending just in case
            in_progress_items.sort(key=lambda x: float(x.get("priority_score", 0)), reverse=True)
            target_item = in_progress_items[0]
            print(f"Found target sourcetype: {target_item['sourcetype']} with Data Model: {target_item.get('target_dm')}")
        else:
            print(f"Failed to fetch from KV store: {resp.status_code} - {resp.text}")
            return

    sourcetype = target_item['sourcetype']
    target_dm = target_item.get('target_dm', 'Unknown')
    source = target_item.get('source', '*')

    print(f"Fetching sample raw events for sourcetype={sourcetype} and source={source} via REST API...")
    search_query = f'search index=* sourcetype="{sourcetype}" source="{source}" | head 3'
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
                    except Exception:
                        pass

    if not raw_events:
        print(f"No sample events found for sourcetype: {sourcetype} and source: {source}")
        return

    print(f"Found {len(raw_events)} sample events. Calling LLM for generation...")

    events_text = "\n".join(raw_events)
    schema = GenerationOutput.model_json_schema()
    
    prompt = f"""
You are a Splunk expert. Analyze the following raw events for the sourcetype '{sourcetype}' and source '{source}'.
The target CIM Data Model is '{target_dm}'.
Generate the necessary field extractions (regex), eval expressions, and field aliases to map these events to the '{target_dm}' Data Model.
Also provide the necessary tags.

Raw Events:
{events_text}

Output ONLY valid JSON matching this schema:
{json.dumps(schema, indent=2)}
"""
    print(prompt)
    content = None
    try:
        response = litellm.completion(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            api_base=OLLAMA_BASE_URL,
            timeout=180.0
        )
        content = response.choices[0].message.content.strip()
        print("Received LLM response. Parsing to Pydantic model...")
        
        # Clean up markdown formatting if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        output_data = GenerationOutput.model_validate_json(content)
    except Exception as e:
        print(f"Error during LLM generation or parsing: {e}")
        if content is not None:
            print("Raw content:")
            print(content)
        return

    print("Successfully parsed GenerationOutput. Rendering .conf files...")
    
    import re
    stanza_name = f"[{sourcetype}]" if source == '*' else f"[source::{source}]"
    clean_source = re.sub(r'[^a-zA-Z0-9]', '_', source)
    eventtype_name = f"{sourcetype}_{clean_source}".strip('_')

    ta_dir = f"/app/apps/TA-{sourcetype.replace(':', '_')}/default"
    os.makedirs(ta_dir, exist_ok=True)
    
    props_conf_path = os.path.join(ta_dir, "props.conf")
    tags_conf_path = os.path.join(ta_dir, "tags.conf")
    eventtypes_conf_path = os.path.join(ta_dir, "eventtypes.conf")
    
    # Render props.conf
    with open(props_conf_path, "a") as f:
        f.write(f"\n{stanza_name}\n")
        
        for ext in output_data.props.extractions:
            f.write(f"EXTRACT-{ext.name} = {ext.regex}\n")
            
        for ev in output_data.props.evals:
            f.write(f"EVAL-{ev.name} = {ev.expression}\n")
            
        for orig, cim in output_data.props.rename_fields.items():
            f.write(f"FIELDALIAS-{cim} = {orig} AS {cim}\n")
            
    print(f"Written: {props_conf_path}")
            
    # Render eventtypes.conf
    with open(eventtypes_conf_path, "a") as f:
        f.write(f"\n[{eventtype_name}]\n")
        if source == '*':
            f.write(f"search = sourcetype={sourcetype}\n")
        else:
            f.write(f"search = sourcetype={sourcetype} source=\"{source}\"\n")
    print(f"Written: {eventtypes_conf_path}")

    # Render tags.conf
    with open(tags_conf_path, "a") as f:
        f.write(f"\n[eventtype={eventtype_name}]\n")
        for tag in output_data.tags:
            f.write(f"{tag} = enabled\n")
            
    print(f"Written: {tags_conf_path}")
    
    # Update KV Store status to 'completed'
    print(f"Updating KV Store status for {sourcetype} to 'completed'...")
    update_url = f"{kv_url}/{target_item['_key']}"
    target_item['status'] = 'completed'
    
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
            print(f"Updated KV store status for {sourcetype} to 'completed'.")
        else:
            print(f"Failed to update KV store: {resp.status_code} - {resp.text}")

    print("Phase 3 Generation complete.")

def generate_configurations():
    """
    Fetches an 'in_progress' sourcetype from the KV store,
    fetches raw events, uses litellm to map to schema, and writes .conf files.
    """
    asyncio.run(_generate_configurations())
