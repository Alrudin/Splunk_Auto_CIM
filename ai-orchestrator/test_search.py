import asyncio
import httpx
import json
from config import SPLUNK_HOST, SPLUNK_PORT, SPLUNK_USER, SPLUNK_PASSWORD

async def test_search():
    url = f"https://{SPLUNK_HOST}:{SPLUNK_PORT}/services/search/jobs/export"
    auth = (SPLUNK_USER, SPLUNK_PASSWORD)
    query = "| tstats count where index=* by sourcetype | eval gap_percentage=random()%100 | eval priority_score=random()%10 | table sourcetype, gap_percentage, priority_score"
    data = {"search": query, "output_mode": "json", "earliest_time": "0"}
    
    async with httpx.AsyncClient(verify=False, timeout=60) as client:
        print("Sending search...")
        resp = await client.post(url, data=data, auth=auth)
        print(f"Status: {resp.status_code}")
        results = []
        for line in resp.text.strip().split('\n'):
            if line:
                try:
                    results.append(json.loads(line))
                except:
                    pass
        print(f"Got {len(results)} rows.")
        if results:
            print(results[0])

asyncio.run(test_search())
