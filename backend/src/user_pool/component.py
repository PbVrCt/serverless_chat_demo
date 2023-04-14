from constructs import Construct
from aws_cdk import Stack, Environment, CfnOutput

from src.user_pool.cognito.infrastructure import UserPool as UserPool_


class UserPool(Stack):
    @property
    def user_pool_arn(self):
        return self._user_pool.user_pool_arn

    @property
    def user_pool_client_id(self):
        return self._user_pool.user_pool_client_id

    def __init__(
        self,
        scope: Construct,
        id: str,
        env: Environment,
        props: dict,
        user_pool_id_output_key: str,
        user_pool_client_id_output_key: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, env=env, **kwargs)

        self._user_pool = UserPool_(self, "UserPool", props)

        pool_id_output = CfnOutput(
            self, "PoolIdOutput", value=self._user_pool.user_pool_id
        )
        pool_id_output.override_logical_id(new_logical_id=user_pool_id_output_key)

        pool_client_id_output = CfnOutput(
            self, "PoolClientIdOutput", value=self._user_pool.user_pool_client_id
        )
        pool_client_id_output.override_logical_id(
            new_logical_id=user_pool_client_id_output_key
        )
