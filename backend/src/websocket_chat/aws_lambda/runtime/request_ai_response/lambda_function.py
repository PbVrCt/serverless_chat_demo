from os import environ
from json import loads
from uuid import uuid4
from datetime import datetime, timezone

from boto3 import resource, client, session
from botocore.exceptions import ClientError

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
import openai

metrics = Metrics(service="websocket_chat", namespace="serverless_demo")
tracer = Tracer(service="websocket_chat")
logger = Logger(service="websocket_chat")

region_name = environ["AWS_REGION"]
user_pool_arn = environ["USER_POOL_ARN"]
user_pool_id = user_pool_arn.split("/")[1]
messages_table_name = environ["MESSAGES_TABLE_NAME"]
openai_token_secret_name = environ[
    "OPENAI_TOKEN_SECRET_NAME"
]  # Same as the key for the key-value pair in Secrets Manager

db_client = resource("dynamodb")
cognito_client = client("cognito-idp")


@metrics.log_metrics(capture_cold_start_metric=True)
@tracer.capture_lambda_handler
@logger.inject_lambda_context
def handler(event, context):
    table = db_client.Table(messages_table_name)
    # Get the Cognito user prefered_username attribute from the sub id
    user = cognito_client.admin_get_user(
        UserPoolId=user_pool_id, Username=event["identity"]["claims"]["sub"]
    )
    preferred_username = None
    for attribute in user["UserAttributes"]:
        if attribute["Name"] == "preferred_username":
            preferred_username = attribute["Value"]
            break
    # Get the OpenAI token from Secrets Manager
    session_ = session.Session()
    client = session_.client(service_name="secretsmanager", region_name=region_name)
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=openai_token_secret_name
        )
    except ClientError as e:
        logger.exception(
            "Error retrieving secret from secrets manager: {}".format(str(e))
        )
        raise e
    secret = loads(get_secret_value_response["SecretString"])
    secret = secret[openai_token_secret_name]
    # Get a response from OpenAI
    openai.api_key = secret
    chat_inputs = [
        {
            "role": "system",
            "content": "You are the greek orator {} and will argument in favor of whatever the user prompts you to, in the style of {}".format(
                preferred_username, preferred_username
            ),
        },
        {"role": "user", "content": event["arguments"]["message"]["text"]},
    ]
    try:
        ai_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=chat_inputs,
            max_tokens=100,
            n=1,
            stop=None,
            temperature=0.5,
        )
        logger.info(ai_response)
        # metrics.add_metric(name="Put item worked", unit=MetricUnit.Count, value=1)
    except Exception as e:
        logger.exception("Error calling OpenAI: {}".format(str(e)))
        raise
    # Save the response to DynamoDB and return it to the client
    message_id = str(uuid4())
    creation_date = datetime.now(timezone.utc).isoformat(timespec="seconds")
    ai_response = ai_response["choices"][0]["message"]["content"]
    message = {
        "PK": message_id,
        "SK": creation_date,
        "Text": ai_response,
        "AiGenerated": True,
        "Username": preferred_username,
        "TenantId": event["identity"]["claims"]["sub"],
    }
    response = table.put_item(Item=message)
    return {
        "text": ai_response,
        "aiGenerated": True,
        "tenantId": event["identity"]["claims"]["sub"],
        "username": preferred_username,
    }
