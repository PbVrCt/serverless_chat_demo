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
                  "{GraphQLEndpointName}": {
                      "endpointType": "GraphQL",
                      "endpoint": "{GraphQLUrl}",
                      "region": "eu-west-1",
                      "authorizationType": "AMAZON_COGNITO_USER_POOLS"
                  }
              }
          }
      },
      "auth": {
          "plugins": {
              "awsCognitoAuthPlugin": {
                  "IdentityManager": {
                      "Default": {}
                  },
                  "CognitoUserPool": {
                      "Default": {
                          "PoolId": "{CognitoPoolId}",
                          "AppClientId": "{CognitoAppClientId}",
                          "Region": "eu-west-1"
                      }
                  },
                  "Auth": {
                    "Default": {
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
  amplifyconfig = amplifyconfig.replaceAll('{GraphQLUrl}', graphQLUrl);
  amplifyconfig =
      amplifyconfig.replaceAll('{GraphQLEndpointName}', graphQLEndpointName);
  amplifyconfig = amplifyconfig.replaceAll('{CognitoPoolId}', userPoolId);
  amplifyconfig =
      amplifyconfig.replaceAll('{CognitoAppClientId}', userPoolClientId);
  return amplifyconfig;
}
