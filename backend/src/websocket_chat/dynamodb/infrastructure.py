from constructs import Construct
from aws_cdk import RemovalPolicy, aws_dynamodb as db


class Tables(Construct):
    @property
    def messages_table_arn(self):
        return self._messages_table.table_arn

    @property
    def messages_table_name(self):
        return self._messages_table.table_name

    def __init__(
        self,
        scope: Construct,
        id: str,
        props: dict = None,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        self._messages_table = db.Table(
            self,
            "ChatMessagesTable",
            partition_key=db.Attribute(name="PK", type=db.AttributeType.STRING),
            sort_key=db.Attribute(name="SK", type=db.AttributeType.STRING),
            removal_policy=RemovalPolicy.DESTROY,
            billing_mode=db.BillingMode.PAY_PER_REQUEST,
            table_class=db.TableClass.STANDARD,
        )
