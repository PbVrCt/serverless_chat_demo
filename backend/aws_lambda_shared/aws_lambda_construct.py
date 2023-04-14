import os
from typing import Union

from constructs import Construct
from aws_cdk import aws_lambda, aws_iam as iam, Duration


# Generic helper construct. Consider replacing it by the CDK 'PythonFunction' L2 construct when it comes out
class LambdaPython(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        code_path: str,
        env_vars: Union[dict[str, str], None] = None,
        memory_size=128,
        timeout=Duration.seconds(3),
        layers: list[str] = [],
        **kwargs
    ):
        super().__init__(scope, id, **kwargs)

        # Layers

        powertools_layer = aws_lambda.LayerVersion.from_layer_version_arn(
            self,
            "PowertoolsLayer",
            "arn:aws:lambda:eu-west-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:26",
        )

        jose_layer = aws_lambda.LayerVersion(
            self,
            "JoseLayer",
            code=aws_lambda.Code.from_asset(
                os.path.join("aws_lambda_shared/layers/python_jose/", "python_jose.zip")
            ),
            compatible_runtimes=[
                aws_lambda.Runtime.PYTHON_3_8,
                aws_lambda.Runtime.PYTHON_3_9,
            ],
            license="BSD 3",
            description="Verifies JWT tokens",
        )

        openai_layer = aws_lambda.LayerVersion(
            self,
            "OpenAILayer",
            code=aws_lambda.Code.from_asset(
                os.path.join("aws_lambda_shared/layers/openai/", "openai.zip")
            ),
            compatible_runtimes=[
                aws_lambda.Runtime.PYTHON_3_8,
                aws_lambda.Runtime.PYTHON_3_9,
            ],
            license="BSD 3",
            description="Libraries to call the OpenAI API",
        )

        assert set(layers).issubset(
            ["lambda_powertools", "jose", "openai"]
        ), "Error: Invalid layer. Valid layers are: 'lambda_powertools', 'jose', 'openai. See aws_lambda_constructs.py for more details."
        layers_ = [powertools_layer]
        if "jose" in layers:
            layers_.append(jose_layer)
        if "openai" in layers:
            layers_.append(openai_layer)

        # Lambda definition

        self._id = id
        self.fn = aws_lambda.Function(
            self,
            self._id,
            function_name=self._id.replace("_", "-"),
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            code=aws_lambda.Code.from_asset(code_path),
            handler="lambda_function.handler",
            memory_size=memory_size,
            timeout=timeout,
            layers=layers_,
            environment=env_vars,
        )

    # Add policy method

    def add_policy(self, actions: list[str], resources: list[str], managed=False):
        policy_name = self._id + "-".join(
            actions
        )  # + "-".join(resources) ## "-".join(resources) does not work because the resouce arns are defined at deployment time
        policy_name = (
            policy_name.replace(":", "-").replace("/", "-").replace("*", "_")[:128]
        )
        self.fn.role.attach_inline_policy(
            iam.Policy(
                self,
                policy_name,
                policy_name=policy_name,
                statements=[
                    iam.PolicyStatement(
                        actions=actions,
                        resources=resources,
                    )
                ],
            )
        )
        return self
