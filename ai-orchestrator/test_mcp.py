import asyncio
import httpx
from config import SPLUNK_MCP_URL, SPLUNK_MCP_TOKEN

async def test_mcp():
    print(f"Connecting to {SPLUNK_MCP_URL} via raw HTTP GET")
    headers = {"Authorization": f"Bearer {SPLUNK_MCP_TOKEN}"}
    
    async with httpx.AsyncClient(verify=False) as client:
        try:
            resp = await client.get(SPLUNK_MCP_URL, headers=headers)
            print(f"Status: {resp.status_code}")
            print(f"Body: {resp.text[:500]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp())


