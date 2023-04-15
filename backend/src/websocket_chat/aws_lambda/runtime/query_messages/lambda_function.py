from os import environ

from boto3 import resource, client

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit

metrics = Metrics(service="websocket_chat", namespace="serverless_demo")
tracer = Tracer(service="websocket_chat")
logger = Logger(service="websocket_chat")

messages_table_name = environ["MESSAGES_TABLE_NAME"]

db_client = resource("dynamodb")


@metrics.log_metrics(capture_cold_start_metric=True)
@tracer.capture_lambda_handler
@logger.inject_lambda_context
def handler(event, context):
    table = db_client.Table(messages_table_name)
    response = table.scan()
    graphql_response = []
    for item in response["Items"]:
        if (
            item["AiGenerated"]
            or item["TenantId"] == event["identity"]["claims"]["sub"]
        ):
            graphql_response.append(
                {
                    "text": item["Text"],
                    "aiGenerated": item["AiGenerated"],
                    "username": item["Username"],
                    "tenantId": item["TenantId"],
                }
            )
    return graphql_response
