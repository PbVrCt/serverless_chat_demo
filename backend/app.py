#!/usr/bin/env python3

import os
import json

from constructs import Construct
from aws_cdk import App, Environment, Stage, Tags

from src.user_pool.component import UserPool
from src.websocket_chat.component import WebsocketChat

app = App()

# Load config

with open("./src/config.json", "r") as f:
    props = json.load(f)

with open("../shared/cdk_output_keys_specified.json", "r") as f:
    output_keys = json.load(f)

# Specify stacks


class AppStage(Stage):
    def __init__(
        self, scope: Construct, id: str, env: Environment, outdir=None, **kwargs
    ):
        super().__init__(scope, id, env=env, outdir=outdir, **kwargs)
        user_pool = UserPool(
            self,
            output_keys["user_pool_stack"]["stack_name"],
            env=env,
            props=props["user_pool_stack"],
            user_pool_id_output_key=output_keys["user_pool_stack"][
                "pool_id_output_key"
            ],
            user_pool_client_id_output_key=output_keys["user_pool_stack"][
                "pool_client_id_output_key"
            ],
        )
        WebsocketChat(
            self,
            output_keys["websocket_chat_stack"]["stack_name"],
            env=env,
            props=props["websocket_chat_stack"],
            stage_name=id,
            user_pool_arn=user_pool.user_pool_arn,
            user_pool_client_id=user_pool.user_pool_client_id,
            graphql_url_output_key=output_keys["websocket_chat_stack"][
                "graphql_url_output_key"
            ],
            graphql_endpoint_name_output_key=output_keys["websocket_chat_stack"][
                "graphql_endpoint_name_output_key"
            ],
        )


# Specify where to deploy to

dev_env = Environment(
    account=props["aws_dev_account_id"], region=props["aws_deploy_region"]
)
prod_env = Environment(
    account=props["aws_prod_account_id"], region=props["aws_deploy_region"]
)

AppStage(app, output_keys["dev_stage_name"], env=dev_env)
AppStage(app, output_keys["prod_stage_name"], env=prod_env)

# Add tags to all resources

for k, v in props["tags"].items():
    Tags.of(app).add(key=k, value=v)

app.synth()
