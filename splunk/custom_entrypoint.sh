#!/bin/bash
echo "Copying BOTSv3 dataset to /opt/splunk/etc/apps/..."
cp -a /tmp/botsv3/* /opt/splunk/etc/apps/
chown -R splunk:splunk /opt/splunk/etc/apps/botsv3_data_set

echo "Installing Splunk MCP Server app..."
tar -xzf /tmp/mcp-server.tgz -C /opt/splunk/etc/apps/
chown -R splunk:splunk /opt/splunk/etc/apps/Splunk_MCP_Server

echo "Creating generated_tas directory..."
mkdir -p /opt/splunk/etc/apps/generated_tas
chown -R splunk:splunk /opt/splunk/etc/apps/generated_tas

echo "Starting Splunk..."
exec /sbin/entrypoint.sh "$@"
