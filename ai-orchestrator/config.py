import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Splunk credentials
SPLUNK_HOST = os.getenv("SPLUNK_HOST", "splunk")
SPLUNK_PORT = int(os.getenv("SPLUNK_PORT", 8089))
SPLUNK_USER = os.getenv("SPLUNK_USER", "admin")
SPLUNK_PASSWORD = os.getenv("SPLUNK_PASSWORD", "abcd1234")

# Splunk MCP settings
SPLUNK_MCP_URL = os.getenv("SPLUNK_MCP_URL", f"https://{SPLUNK_HOST}:{SPLUNK_PORT}/services/mcp")
SPLUNK_MCP_TOKEN = os.getenv("SPLUNK_MCP_TOKEN", "")

# Ollama settings
# When running inside docker on mac, host.docker.internal routes to the host
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "ollama/llama3")
LLM_CONTEXT_LENGTH = int(os.getenv("LLM_CONTEXT_LENGTH", 4000))
