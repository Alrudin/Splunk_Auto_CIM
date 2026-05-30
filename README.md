# Splunk Auto CIM Orchestrator

This repository contains the `ai-orchestrator` for the AI-Driven Splunk CIM Normalizer. Below are the instructions to set up your environment and run the project locally.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- [Python 3.8+](https://www.python.org/downloads/) (if running the orchestrator locally instead of via Docker)

## 1. Environment Configuration

The application uses environment variables for configuration. A sample file is provided.

1. Copy the mock environment file to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in any specific values you need. The default values are pre-configured to work with the local Docker setup.

## 2. Running with Docker Compose

The easiest way to get started is by using Docker Compose, which will spin up a local Splunk instance and an `ai-orchestrator` container.

1. Start the services:
   ```bash
   docker compose up -d
   ```
2. The Splunk web interface will be available at `http://localhost:8000`. You can log in with the credentials defined in your `.env` file (default: `admin` / `abcd1234`).

*Note: The `ai-orchestrator` container is set to tail `/dev/null` by default, keeping it alive so you can execute commands inside it if needed.*

## 3. Local Python Environment (Optional)

If you prefer to run the `ai-orchestrator` Python code directly on your local machine instead of inside Docker, you can set up a virtual environment:

1. Create a Python virtual environment:
   ```bash
   python3 -m venv .myvenv
   ```
2. Activate the virtual environment:
   - On macOS/Linux: `source .myvenv/bin/activate`
   - On Windows: `.myvenv\Scripts\activate`
3. Install the required Python packages:
   ```bash
   pip install -r ai-orchestrator/requirements.txt
   ```

## Usage

The orchestrator is built using Click and provides a Command Line Interface (CLI). 

To see available commands, run:
```bash
python ai-orchestrator/main.py --help
```

### Available Commands:

- **`discovery`**: Phase 1 - Run differential searches and populate the Remediation Queue.
  ```bash
  python ai-orchestrator/main.py discovery
  ```
- **`context`**: Phase 2 - Fetch priority sourcetype, fetch events, and classify Data Model.
  ```bash
  python ai-orchestrator/main.py context
  ```
- **`generate`**: Phase 3 - Map fields and generate Splunk configurations.
  ```bash
  python ai-orchestrator/main.py generate
  ```
