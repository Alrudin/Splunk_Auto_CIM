# Implementation Plan: AI-Driven Splunk CIM Normalizer

This document outlines the technical implementation steps to realize the architecture agreed upon in the Product Specification (`Docs/PRD.md`).

## 1. Goal Description
Build out the `ai-orchestrator` Python CLI and configure the local `splunk` container to support the end-to-end MVP workflow. This MVP will map unstructured log data to the Splunk CIM using a local LLM via Ollama and store its state in Splunk's KV Store.

## 2. Environment Configuration
- **Splunk MCP Token:** The analyst will generate an encrypted MCP token via the Splunk UI manually. This token will be stored in a local `.env` file and loaded by the Orchestrator CLI to authenticate MCP tool calls.
- **Ollama Setup:** Ollama is running locally on the Mac host. The containerized `ai-orchestrator` will connect to it via `http://host.docker.internal:11434`.

## 3. Proposed Changes

### Splunk State Management (KV Store)
We need to define a Splunk KV Store collection to hold the "Remediation Queue". We will create a small foundational Splunk app that defines this schema.

#### [NEW] `apps/Splunk_Auto_CIM_State/default/collections.conf`
Defines the `remediation_queue` KV Store collection.

#### [NEW] `apps/Splunk_Auto_CIM_State/default/transforms.conf`
Defines the external lookup for the KV Store collection so it can be queried easily via SPL (`| inputlookup remediation_queue`).

---

### AI Orchestrator Base Framework
Set up the Python CLI skeleton and dependencies.

#### [MODIFY] `ai-orchestrator/requirements.txt`
Add `litellm`, `pydantic`, `click` (for CLI), and `python-dotenv`.

#### [NEW] `ai-orchestrator/main.py`
The main CLI entrypoint using `click`. Will load variables from `.env` and have subcommands:
- `python main.py discovery`
- `python main.py context`
- `python main.py generate`

#### [NEW] `ai-orchestrator/config.py`
Settings and environment variable loading (Splunk credentials, MCP token, Ollama URL at `http://host.docker.internal:11434`).

---

### Phase 1: Discovery Module
#### [NEW] `ai-orchestrator/discovery.py`
- Connects to Splunk MCP server using the token from `.env`.
- Uses MCP tool to execute a differential `tstats` search to find unmapped sourcetypes.
- Uses Splunk REST API to write results (Gap Percentage, Priority Score) to the `remediation_queue` KV Store.

---

### Phase 2: Context Gathering & Classification Module
#### [NEW] `ai-orchestrator/context.py`
- Fetches the highest priority sourcetype from the `remediation_queue`.
- Uses MCP tool to fetch sample raw events.
- Uses `litellm` (calling Ollama) to classify the events into a target CIM Data Model.
- Includes a CLI `input()` fallback to confirm low-confidence classifications with the analyst.

---

### Phase 3: Generation Module
#### [NEW] `ai-orchestrator/models.py`
- Defines strict Pydantic schemas (e.g. `PropsConf`, `TransformsConf`, `TagsConf`).

#### [NEW] `ai-orchestrator/generation.py`
- Maps raw fields to the confirmed schema using the LLM.
- Forces output into the Pydantic schema using Structured Outputs.
- Renders the JSON into `.conf` text files using a simple Python string template.
- Writes the generated TA directly to `/app/apps/generated_tas/` (which mounts to `./apps` on the host).

## 4. Verification Plan

### Automated/Unit Tests
- We can write local Python `pytest` functions to verify the Pydantic models correctly render `.conf` syntax.

### Manual Verification
1. `docker compose up -d` to start Splunk and Orchestrator.
2. Manually generate an MCP token in Splunk UI and save it to `ai-orchestrator/.env`.
3. Run `docker exec -it ai-orchestrator python main.py discovery` and verify the KV store is populated.
4. Run `docker exec -it ai-orchestrator python main.py context` and verify the CLI prompts for Data Model confirmation.
5. Run `docker exec -it ai-orchestrator python main.py generate` and verify the `.conf` files appear in `./apps/`.
