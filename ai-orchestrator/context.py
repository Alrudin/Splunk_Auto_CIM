import httpx
import litellm
from config import *

def gather_context():
    """
    Fetches the highest priority sourcetype from the KV store,
    fetches raw events via MCP, and uses litellm to classify the CIM Data Model.
    """
    print("Fetching highest priority sourcetype from KV store...")
    # TODO: Implement Splunk REST API call
    
    print("Fetching sample raw events via MCP...")
    # TODO: Implement MCP tool call
    
    print("Classifying Data Model using Ollama...")
    # TODO: Implement litellm classification with OLLAMA_BASE_URL and LLM_MODEL
    # e.g., response = litellm.completion(model=LLM_MODEL, messages=[...], api_base=OLLAMA_BASE_URL)
    
    target_dm = input("Confirm Target Data Model (press Enter to accept or type an override): ")
    return target_dm
