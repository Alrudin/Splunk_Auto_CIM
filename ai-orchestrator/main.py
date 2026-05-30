import click

from discovery import run_discovery
from context import gather_context
from generation import generate_configurations

@click.group()
def cli():
    """AI-Driven Splunk CIM Normalizer Orchestrator."""
    pass

@cli.command()
def discovery():
    """Phase 1: Run differential searches and populate the Remediation Queue."""
    click.echo("Running Discovery Phase...")
    run_discovery()

@cli.command()
def context():
    """Phase 2: Fetch priority sourcetype, fetch events, and classify Data Model."""
    click.echo("Running Context Gathering Phase...")
    gather_context()

@cli.command()
def generate():
    """Phase 3: Map fields and generate Splunk configurations."""
    click.echo("Running Generation Phase...")
    # Normally we would pass target_dm from the context step, here we'll assume it's known or stored
    # For MVP skeleton, we just pass a placeholder
    generate_configurations("Placeholder_DM")

if __name__ == "__main__":
    cli()
