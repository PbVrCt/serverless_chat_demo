import os

from constructs import Construct
from aws_cdk import aws_iam as iam, Duration

from aws_lambda_shared.aws_lambda_construct import LambdaPython


class LambdaFunctions(Construct):
    @property
    def query_messages_fn(self):
        return self._query_messages.fn

    @property
    def send_message_fn(self):
        return self._send_message.fn

    @property
    def request_ai_response_fn(self):
        return self._request_ai_response.fn

    @property
    def delete_all_messages_fn(self):
        return self._delete_all_messages.fn

    def __init__(
        self,
        scope: Construct,
        id: str,
        openai_token_secret_name: str,
        openai_token_secret_arn: str,
        user_pool_arn: str,
        user_pool_client_id: str,
        messages_table_name: str,
        messages_table_arn: str,
        **kwargs
    ):
        super().__init__(scope, id, **kwargs)

        current_path = os.path.dirname(os.path.realpath(__file__))

        self._query_messages = LambdaPython(
            self,
            "QueryMessages",
            code_path=current_path + "/runtime/query_messages",
            env_vars={"MESSAGES_TABLE_NAME": messages_table_name},
        ).add_policy(["dynamodb:Scan"], [messages_table_arn])

        self._send_message = LambdaPython(
            self,
            "SendMessage",
            code_path=current_path + "/runtime/send_message",
            env_vars={"MESSAGES_TABLE_NAME": messages_table_name},
        ).add_policy(["dynamodb:PutItem"], [messages_table_arn])

        self._request_ai_response = (
            LambdaPython(
                self,
                "RequestAIResponse",
                code_path=current_path + "/runtime/request_ai_response",
                layers=["openai"],
                env_vars={
                    "MESSAGES_TABLE_NAME": messages_table_name,
                    "OPENAI_TOKEN_SECRET_NAME": openai_token_secret_name,
                },
                timeout=Duration.seconds(27),
            )
            .add_policy(["dynamodb:PutItem"], [messages_table_arn])
            .add_policy(["secretsmanager:GetSecretValue"], [openai_token_secret_arn])
        )

        self._delete_all_messages = LambdaPython(
            self,
            "DeleteAllMessages",
            code_path=current_path + "/runtime/delete_all_messages",
            env_vars={
                "MESSAGES_TABLE_NAME": messages_table_name,
            },
        ).add_policy(["dynamodb:Scan", "dynamodb:BatchWriteItem"], [messages_table_arn])
