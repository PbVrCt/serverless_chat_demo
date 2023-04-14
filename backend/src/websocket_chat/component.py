from constructs import Construct
from aws_cdk import Stack, Environment, CfnOutput

from src.websocket_chat.dynamodb.infrastructure import Tables
from src.websocket_chat.aws_lambda.infrastructure import LambdaFunctions
from src.websocket_chat.appsync.infrastructure import WebsocketsApi


class WebsocketChat(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        env: Environment,
        props: dict,
        stage_name: dict,
        user_pool_arn: str,
        user_pool_client_id: str,
        graphql_url_output_key: str,
        graphql_endpoint_name_output_key: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, env=env, **kwargs)

        dynamo_tables = Tables(self, "Dynamo")
        lambda_functions = LambdaFunctions(
            self,
            "LambdaFunctions",
            props["openai_token_secret_name"],
            props["openai_token_secret_arn"],
            user_pool_arn,
            user_pool_client_id,
            dynamo_tables.messages_table_name,
            dynamo_tables.messages_table_arn,
        )
        appsync_api = WebsocketsApi(
            self,
            "WebsocketApi",
            user_pool_arn,
            user_pool_client_id,
            lambda_functions.query_messages_fn,
            lambda_functions.send_message_fn,
            lambda_functions.request_ai_response_fn,
            lambda_functions.delete_all_messages_fn,
        )

        graphql_url_output = CfnOutput(
            self, "GraphQLUrlOutput", value=appsync_api.graphql_url
        )
        graphql_url_output.override_logical_id(new_logical_id=graphql_url_output_key)

        graphql_endpoint_name_output = CfnOutput(
            self,
            "GraphQLEndpointNameOutput",
            value=appsync_api.graphql_endpoint_name,
        )
        graphql_endpoint_name_output.override_logical_id(
            new_logical_id=graphql_endpoint_name_output_key
        )
