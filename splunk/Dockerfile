FROM --platform=linux/amd64 splunk/splunk:latest

USER root
# Prepare BOTSv3 dataset in a temporary directory
COPY resources/botsv3_data_set.tgz /tmp/botsv3.tgz
RUN mkdir -p /tmp/botsv3 && \
    tar -xzf /tmp/botsv3.tgz -C /tmp/botsv3 && \
    rm /tmp/botsv3.tgz && \
    chown -R splunk:splunk /tmp/botsv3

# Copy Splunk MCP Server app
COPY resources/splunk-mcp-server_120.tgz /tmp/mcp-server.tgz

COPY resources/splunk-common-information-model-cim_850.tgz /tmp/splunk-common-information-model-cim_850.tgz

COPY splunk/custom_entrypoint.sh /custom_entrypoint.sh
RUN chmod +x /custom_entrypoint.sh

ENTRYPOINT ["/custom_entrypoint.sh"]
CMD ["start-service"]
