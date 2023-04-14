from os import environ
from uuid import uuid4
from copy import deepcopy
from datetime import datetime, timezone

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
    message_id = str(uuid4())
    creation_date = datetime.now(timezone.utc).isoformat(timespec="seconds")
    message = {
        "PK": message_id,
        "SK": creation_date,
        "Text": event["arguments"]["message"]["text"],
        "AiGenerated": False,
        "Username": "TestUser",
        "TenantId": event["identity"]["claims"]["sub"],
    }
    response = table.put_item(Item=message)
    return {
        "text": event["arguments"]["message"]["text"],
        "aiGenerated": False,
        "tenantId": event["identity"]["claims"]["sub"],
        "username": "TestUser",
    }
