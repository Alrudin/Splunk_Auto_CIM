# Product Specification: AI-Driven Splunk CIM Normalizer

## 1. Executive Summary
Automate the mapping of unstructured log data to the Splunk Common Information Model (CIM). This tool generates valid Splunk configurations (props.conf, transforms.conf, tags.conf) at design-time, deploying them as custom Technology Add-ons (TAs). 

## 2. System Architecture
* **Splunk Platform:** Source of truth for raw logs, schemas, and state management (Remediation Queue in KV Store).
* **Splunk MCP Server:** Bridge for the LLM to execute Splunk REST APIs.
* **AI Orchestrator:** A Python-based CLI application. It uses a local LLM running on Ollama with an abstraction layer (like LiteLLM) to allow future provider switching. It coordinates gap analysis, classifies Data Models, processes MCP context, and generates configurations using Pydantic structured schemas to ensure syntax safety.
* **Deployment (MVP):** Writes directly to a local mounted volume (`./apps`).
* **Deployment (Future):** GitLab CI/CD for version control, splunk-appinspect validation, and deployment.

## 3. Core Workflows

### Phase 1: Discovery and Prioritization
1. Analyst triggers the Orchestrator via CLI (e.g., `--run-phase discovery`).
2. Agent queries MCP to run tstats differential searches.
3. Calculates Gap Percentage and Priority Score.
4. Updates the Remediation Queue stored centrally in the **Splunk KV Store**.

### Phase 2: Context Gathering
1. Analyst triggers the Orchestrator via CLI.
2. Agent selects highest priority unmapped sourcetype from the KV Store.
3. **Data Model Classification**: Agent fetches sample events and uses the LLM to classify the target CIM Data Model. Low-confidence matches fallback to CLI prompt for human confirmation.
4. Agent fetches target Data Model schema.
5. Agent fetches sample raw events.

### Phase 3: Generation and Orchestration
1. Agent maps raw fields to schema.
2. Agent forces the LLM to output structured JSON matching Splunk conf schemas (via Pydantic). 
3. Python layer compiles the JSON into strictly formatted `.conf` files.
4. (MVP) Agent writes TA directory to local `./apps` folder for immediate testing.
5. (Future) Agent commits TA directory via GitLab API to trigger a Merge Request.

### Phase 4: Validation and Deployment (Future / GitLab)
1. GitLab pipeline triggers on MR.
2. Runs splunk-appinspect to block invalid regex.
3. Analyst reviews and merges MR.
4. CI/CD deploys TA to Splunk.

## 4. Constraints and Security
* **Design-Time Only:** LLM will never be used for run-time log parsing.
* **RBAC:** MCP server requires read-only access to search and datamodel APIs.
* **Human-in-the-Loop:** MVP relies on analyst triggering CLI phases and confirming low-confidence Data Model classifications. All future outputs require AppInspect validation and MR approval.