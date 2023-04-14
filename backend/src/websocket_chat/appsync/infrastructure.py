import os
from typing import Union

from constructs import Construct
from aws_cdk import (
    Stack,
    aws_appsync as appsync,
    aws_iam as iam,
    Duration,
    aws_cognito as cognito,
    aws_dynamodb as dynamodb,
    aws_lambda,
)

# https://adrianhesketh.com/2021/02/22/setting-up-appsync-graphql-subscriptions-with-typescript-and-cdk/


class WebsocketsApi(Construct):
    @property
    def graphql_url(self):
        return self._api.graphql_url

    @property
    def graphql_endpoint_name(self):
        return self._graphql_enpoint_name

    def __init__(
        self,
        scope: Construct,
        id: str,
        user_pool_arn: str,
        user_pool_client_id: str,
        query_messages_fn: aws_lambda.Function,
        send_message_fn: aws_lambda.Function,
        request_ai_response_fn: aws_lambda.Function,
        delete_all_messages_fn: aws_lambda.Function,
        **kwargs
    ):
        super().__init__(scope, id, **kwargs)

        self._graphql_enpoint_name = "ChatDemoApi"

        self._api = appsync.GraphqlApi(
            self,
            "Api",
            name=self._graphql_enpoint_name,
            schema=appsync.SchemaFile.from_asset("../shared/schema.graphql"),
            authorization_config=appsync.AuthorizationConfig(
                default_authorization=appsync.AuthorizationMode(
                    authorization_type=appsync.AuthorizationType.USER_POOL,
                    user_pool_config=appsync.UserPoolConfig(
                        user_pool=cognito.UserPool.from_user_pool_arn(
                            self, "UserPool", user_pool_arn
                        ),
                        default_action=appsync.UserPoolDefaultAction.ALLOW,
                    ),
                )
            ),
            xray_enabled=True,
        )

        query_messages_source = self._api.add_lambda_data_source(
            "QueryMessagesSource",
            query_messages_fn,
        )

        query_messages_source.create_resolver(
            "QueryMessageResolver",
            type_name="Query",
            field_name="messages",
        )

        send_message_source = self._api.add_lambda_data_source(
            "SendMessageSource",
            send_message_fn,
        )

        send_message_source.create_resolver(
            "SendMessageResolver",
            type_name="Mutation",
            field_name="sendMessage",
        )

        request_ai_response_source = self._api.add_lambda_data_source(
            "RequestAiResponseSource",
            request_ai_response_fn,
        )

        request_ai_response_source.create_resolver(
            "RequestAiResponseResolver",
            type_name="Mutation",
            field_name="requestAiResponse",
        )

        delete_all_messages_source = self._api.add_lambda_data_source(
            "DeleteAllMessagesSource",
            delete_all_messages_fn,
        )

        delete_all_messages_source.create_resolver(
            "DeleteAllMessagesResolver",
            type_name="Mutation",
            field_name="deleteAllMessages",
        )
