import 'dart:convert';
import 'package:flutter/services.dart';

Future<String> amplifyConfig() async {
  final String response =
      await rootBundle.loadString('assets/cdk_output_pairs_generated.json');
  final backendExports = await json.decode(response);
  final String userPoolId = backendExports['prod-UserPool']["UserPoolId"];
  final String userPoolClientId =
      backendExports['prod-UserPool']["UserPoolClientId"];
  final String graphQLUrl = backendExports['prod-WebsocketChat']["GraphQLUrl"];
  final String graphQLEndpointName =
      backendExports['prod-WebsocketChat']["GraphQLEndpointName"];
  String amplifyconfig = ''' {
      "UserAgent": "aws-amplify-cli/2.0",
      "Version": "1.0",
      "api": {
          "plugins": {
              "awsAPIPlugin": {
                  "$graphQLEndpointName": {
                      "endpointType": "GraphQL",
                      "endpoint": "$graphQLUrl",
                      "region": "eu-west-1",
                      "authorizationType": "AMAZON_COGNITO_USER_POOLS"
                  }
              }
          }
      },
      "auth": {
          "plugins": {
              "awsCognitoAuthPlugin": {
                  "UserAgent": "aws-amplify/cli",
                  "Version": "0.1.0",
                  "IdentityManager": {
                    "Default": {}
                  },
                  "CognitoUserPool": {
                      "Default": {
                          "PoolId": "$userPoolId",
                          "AppClientId": "$userPoolClientId",
                          "Region": "eu-west-1"
                      }
                  },
                  "Auth": {
                    "Default": {
                        "OAuth": {
                          "WebDomain": "example.com",
                          "AppClientId": "$userPoolClientId",
                          "SignInRedirectURI": "myapp://",
                          "SignOutRedirectURI": "myapp://",
                          "Scopes": ["phone", "email", "openid", "profile", "aws.cognito.signin.user.admin"]
                        },
                        "authenticationFlowType": "USER_SRP_AUTH",
                        "loginMechanisms": [
                            "EMAIL"
                        ],
                        "signupAttributes": [
                            "EMAIL"
 
                        ],
                        "usernameAttributes": [
                            "EMAIL"
                        ],
                        "passwordProtectionSettings": {
                            "passwordPolicyMinLength": 8,
                            "passwordPolicyCharacters": []
                        },
                        "mfaConfiguration": "OFF",
                        "mfaTypes": [
                            "SMS"
                        ],
                        "verificationMechanisms": [
                            "EMAIL"
                        ]                    }
                  }
              }
          }
      }
  }''';
  return amplifyconfig;
}
