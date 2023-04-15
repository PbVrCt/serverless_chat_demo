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
    # Prepare the AI inputs
    ## Prompt
    ai_prompt = [
        {
            "role": "system",
            "content": """You are {}, the orator/statesman from the time of the greeks, and you are debating against other greek orator(s).
            You will be provided the chat history of the debate between yourself and the others. With that, you will also receive one user message/prompt,
            that you have to turn into a convincing argument in the style of {}, to be added to the conversation.
            The argument must be expressed in one short sentence ending with a point.
            The argument must be in favor of whatever the user has prompted you to support.""".format(
                preferred_username, preferred_username, preferred_username
            ),
        }
    ]
    ## Chat history
    response = table.scan()
    chat_history = []
    logger.info(response)
    for item in response["Items"]:
        if (
            item["AiGenerated"]
            and item["TenantId"] == event["identity"]["claims"]["sub"]
        ):
            chat_history.append({"role": "assistant", "content": item["Text"]})
        elif item["AiGenerated"]:
            chat_history.append({"role": "user", "content": item["Text"]})
    ## User message
    user_message = [
        {
            "role": "user",
            "content": "User prompt: " + event["arguments"]["message"]["text"],
        }
    ]
    # Get a completion from OpenAI
    chat_inputs = []
    chat_inputs.extend(ai_prompt)
    chat_inputs.extend(chat_history)
    chat_inputs.extend(user_message)
    openai.api_key = secret
    try:
        ai_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=chat_inputs,
            max_tokens=25,
            n=1,
            stop=[".", "?", "!", "\n"],
            temperature=0.5,
        )
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
