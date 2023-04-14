from constructs import Construct
from aws_cdk import (
    aws_cognito as cognito,
    aws_certificatemanager as certificatemanager,
    Duration,
)


class UserPool(Construct):
    @property
    def user_pool_arn(self):
        return self._user_pool.user_pool_arn

    @property
    def user_pool_id(self):
        return self._user_pool.user_pool_id

    @property
    def user_pool_client_id(self):
        return self._user_pool_client.user_pool_client_id

    def __init__(
        self,
        scope: Construct,
        id: str,
        props: dict,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        # POOL

        self._user_pool = cognito.UserPool(
            self,
            "Pool",
            user_pool_name=props["user_pool_name"],
            sign_in_aliases=cognito.SignInAliases(
                username=False, email=True, phone=False
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=9,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=False,
                temp_password_validity=Duration.days(3),
            ),
            mfa=cognito.Mfa.OFF,
            # mfa_second_factor=cognito.MfaSecondFactor(sms=True, otp=False),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            self_sign_up_enabled=True,
            auto_verify=cognito.AutoVerifiedAttrs(email=True, phone=False),
            standard_attributes=cognito.StandardAttributes(
                preferred_username=cognito.StandardAttribute(
                    required=True, mutable=True
                ),
                email=cognito.StandardAttribute(required=True, mutable=True),
            ),
            custom_attributes={
                "username": cognito.StringAttribute(
                    mutable=True, max_len=20, min_len=1
                ),
                # "tier": cognito.StringAttribute(mutable=True, max_len=20, min_len=1)
            },
            # # Have the user verify both email and phone changes before they happen
            # keep_original=cognito.KeepOriginalAttrs(email=true, phone=true),
            # email=cognito.UserPoolEmail.with_ses(
            #     ses_region=props["notifications_email_ses_region"],
            #     from_email=props["notifications_email"],
            #     # from_name="Piotr Kowalski",
            # ),
            # # By default a new iam role is created for sending sms messages. But sending sms requires additional config
        )
        # APP-CLIENT

        client_write_attributes = (
            (cognito.ClientAttributes()).with_standard_attributes(
                email=True,
                preferred_username=True,
            )
            # .with_custom_attributes("tier")
        )
        client_read_attributes = (
            (cognito.ClientAttributes()).with_standard_attributes(
                email=True,
                email_verified=True,
                preferred_username=True,
            )
            # .with_custom_attributes("tier")
        )
        self._user_pool_client = self._user_pool.add_client(
            "UserPoolAppClientCDKId",
            generate_secret=False,
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                    implicit_code_grant=False,
                ),
                scopes=[
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.PHONE,
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.COGNITO_ADMIN,
                ],
                callback_urls=[
                    "https://google.com",
                    "http://localhost:3000/auth/signin/callback",
                    # props["amplify_callback_url"],
                ],
                logout_urls=[
                    "https://google.com",
                    "http://localhost:3000/auth/signin",
                    # props["amplify_logout_url"],
                ],
            ),
            auth_flows=cognito.AuthFlow(custom=True, user_srp=True, user_password=True),
            enable_token_revocation=True,
            prevent_user_existence_errors=True,
            supported_identity_providers=[
                cognito.UserPoolClientIdentityProvider.COGNITO
            ],
            access_token_validity=Duration.minutes(60),
            id_token_validity=Duration.minutes(60),
            refresh_token_validity=Duration.days(30),
            read_attributes=client_read_attributes,
            write_attributes=client_write_attributes,
        )

        # # # HOSTED UI DOMAIN

        # # option a: custom domain
        # certificate_arn = props["custom_domain_certificate_arn"]
        # domain_cert = certificatemanager.Certificate.from_certificate_arn(
        #     self, "DomainCdkId", certificate_arn
        # )
        # domain = self.pool.add_domain(
        #     "CustomDomainCdkId",
        #     custom_domain=cognito.CustomDomainOptions(
        #         domain_name="auth.domain.com", certificate=domain_cert
        #     ),
        # )
        # sign_in_url = domain.sign_in_url(client, redirect_uri=props["auth_url"])

        # # option b: aws domain
        # domain = self.pool.add_domain(
        #     "CognitoDomainCdkId",
        #     cognito_domain=cognito.CognitoDomainOptions(domain_prefix="auth-dev"),
        # )
