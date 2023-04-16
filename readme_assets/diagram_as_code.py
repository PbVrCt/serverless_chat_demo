from diagrams import Diagram, Cluster, Edge, Node
from diagrams.aws.compute import Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.integration import Appsync
from diagrams.aws.security import SecretsManager
from diagrams.aws.security import Cognito
from diagrams.onprem.client import User
from diagrams.programming.framework import Flutter
from diagrams.custom import Custom
from diagrams.aws.general import General

graph_attr = {
    "layout": "dot",
    "ordering": "out",
    "ranksep": "0.75",
    "nodesep": "1.0",
}

node_attrs = {}

with Diagram("", show=False, filename="diagram_as_code", graph_attr=graph_attr):
    user = User("", **node_attrs)
    mobile = Flutter("Mobile app", **node_attrs)
    api = Appsync("GraphQL API", **node_attrs)
    user_pool = Cognito("User Pool", **node_attrs)
    lambda1 = Lambda("Get messages", **node_attrs)
    lambda2 = Lambda("Delete messages", **node_attrs)
    lambda3 = Lambda("Post message", **node_attrs)
    db = Dynamodb("Messages Table", **node_attrs)
    openai = Custom("OpenAI Api", "./openai_logo.png", **node_attrs)
    api_key = SecretsManager("Api Key", **node_attrs)

    # Invisible alighment

    edge_attrs = {}
    inv = Edge(style="invis", **edge_attrs)

    user - inv - mobile - inv - api - inv - lambda1 - inv - db
    user - inv - mobile - inv - api - inv - lambda2 - inv - db
    user - inv - mobile - inv - api - inv - lambda3 - inv - db

    # Diagram

    user - mobile - api - [lambda1, lambda2, lambda3] - db
    api - user_pool
    lambda3 - [openai, api_key]
