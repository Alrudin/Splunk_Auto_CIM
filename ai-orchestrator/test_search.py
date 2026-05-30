import asyncio
import httpx
import json
from config import SPLUNK_HOST, SPLUNK_PORT, SPLUNK_USER, SPLUNK_PASSWORD

async def test_search():
    url = f"https://{SPLUNK_HOST}:{SPLUNK_PORT}/services/search/jobs/export"
    auth = (SPLUNK_USER, SPLUNK_PASSWORD)
    query = "| tstats count as total_count where index=* by sourcetype | append [| tstats count as tagged_count where index=* tag=* by sourcetype] | stats sum(total_count) as total_count, sum(tagged_count) as tagged_count by sourcetype | fillnull value=0 total_count, tagged_count | eval gap_percentage=round(((total_count - tagged_count) / total_count) * 100, 2) | eval priority_score=if(total_count>0, min(round(log(total_count, 10) * 1.5, 1), 10.0), 0.0) | table sourcetype, gap_percentage, priority_score"
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
