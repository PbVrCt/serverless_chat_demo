import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';
import 'dart:convert';
import 'dart:async';

import 'package:amplify_auth_cognito/amplify_auth_cognito.dart';
import 'package:amplify_authenticator/amplify_authenticator.dart';
import 'package:amplify_flutter/amplify_flutter.dart';
import 'package:amplify_api/amplify_api.dart';
import 'auth_config.dart';
import 'package:rxdart/rxdart.dart';

void main() => runApp(const MyApp());

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    const title = 'Serverless chat demo';
    return const MaterialApp(
      title: title,
      home: MyHomePage(
        title: title,
      ),
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({
    super.key,
    required this.title,
  });

  final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  final TextEditingController _controller = TextEditingController();
  List<dynamic> _messages = [];
  final StreamController<List<dynamic>> _streamController =
      StreamController<List<dynamic>>.broadcast();
  StreamSubscription<GraphQLResponse<dynamic>>? subscription;
  final ScrollController _scrollController = ScrollController();
  String? tenantId;

  @override
  void initState() {
    super.initState();
    _configureAmplify();
  }

  Future<void> _configureAmplify() async {
    Amplify.addPlugins([AmplifyAuthCognito(), AmplifyAPI()]);
    final amplifyconfig = await amplifyConfig();
    try {
      await Amplify.configure(amplifyconfig);
      safePrint('Successfully configured Amplify');
    } on Exception catch (e) {
      safePrint('Error configuring Amplify: $e');
    }
    final AuthUser currentUser = await Amplify.Auth.getCurrentUser();
    setState(() {
      tenantId = currentUser.userId;
    });
    _receiveMessages();
    _subscribeToMessageMutations(tenantId!);
  }

  @override
  Widget build(BuildContext context) {
    return Authenticator(
      signUpForm: SignUpForm.custom(
        fields: [
          SignUpFormField.email(required: true),
          SignUpFormField.preferredUsername(required: true),
          SignUpFormField.password(),
          SignUpFormField.passwordConfirmation(),
        ],
      ),
      child: MaterialApp(
        builder: Authenticator.builder(),
        home: Scaffold(
          appBar: AppBar(
            title: Text(widget.title),
          ),
          body: Padding(
            padding: const EdgeInsets.all(20.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: StreamBuilder<List<dynamic>>(
                    stream: _streamController.stream,
                    initialData: _messages,
                    builder: (context, snapshot) {
                      if (snapshot.hasData) {
                        return ListView.builder(
                          controller: _scrollController,
                          itemCount: snapshot.data!.length,
                          itemBuilder: (context, index) {
                            final message = snapshot.data![index];
                            final isCurrentUser =
                                message['tenantId'] == tenantId;
                            final username = message['username'];
                            final displayName =
                                isCurrentUser && message['aiGenerated']
                                    ? "$username's wAIfu"
                                    : username;

                            return Row(
                              mainAxisAlignment: isCurrentUser
                                  ? MainAxisAlignment.end
                                  : MainAxisAlignment.start,
                              children: [
                                Flexible(
                                  child: Container(
                                    margin: const EdgeInsets.symmetric(
                                        vertical: 8.0),
                                    padding: const EdgeInsets.all(8.0),
                                    decoration: BoxDecoration(
                                      color: isCurrentUser
                                          ? Colors.blue[100]
                                          : Colors.grey[200],
                                      borderRadius: BorderRadius.circular(8.0),
                                    ),
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          message['text'],
                                          style:
                                              const TextStyle(fontSize: 16.0),
                                        ),
                                        const SizedBox(height: 4.0),
                                        Text(
                                          displayName,
                                          style: TextStyle(
                                              fontSize: 12.0,
                                              color: Colors.grey[700]),
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              ],
                            );
                          },
                        );
                      } else {
                        return const Center(child: CircularProgressIndicator());
                      }
                    },
                  ),
                ),
                Form(
                  child: TextFormField(
                    controller: _controller,
                    decoration: const InputDecoration(
                      labelText: 'Send a message',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    FloatingActionButton(
                      onPressed: () async {
                        if (_controller.text.isNotEmpty) {
                          await _deleteAllMessages();
                        }
                      },
                      tooltip: 'Delete messages',
                      child: const Icon(Icons.delete),
                    ),
                    const SizedBox(width: 16),
                    FloatingActionButton(
                      onPressed: () async {
                        if (_controller.text.isNotEmpty) {
                          await _sendMessage(text: _controller.text);
                        }
                      },
                      tooltip: 'Send message',
                      child: const Icon(Icons.send),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Future<String> fetchUserId() async {
    final currentUser = await Amplify.Auth.getCurrentUser();
    return currentUser.userId;
  }

  Future<void> _receiveMessages() async {
    String graphQLDocument =
        """
    query GetMessages {
      messages {
        text
        tenantId
        username
        aiGenerated
      } 
    }
    """;
    try {
      final response = await Amplify.API
          .query(request: GraphQLRequest<String>(document: graphQLDocument))
          .response;
      safePrint('Query messages data received: ${response.data}');
      safePrint('Query messages error received: ${response.errors}');
      if (response.data != null) {
        setState(() {
          _messages = json.decode(response.data!)['messages'];
          _streamController.add(_messages);
        });
        SchedulerBinding.instance.addPostFrameCallback((_) {
          _scrollToBottom();
        });
      }
    } on Exception catch (e) {
      safePrint(e);
    }
  }

  // NOTE: Having 2 different api calls for an unified behavior is not ideal because you are affording the api user to do something that the api was not designed to, but I do not wish to spend more time on this demo
  Future<void> _sendMessage({required String text}) async {
    String graphQLDocument =
        '''
    mutation SendMessage(\$message: SendMessageInput!) {
      sendMessage(message: \$message) {
        text
        tenantId
        username
        aiGenerated
      }
    }
  ''';
    try {
      final response = await Amplify.API
          .mutate(
              request:
                  GraphQLRequest<String>(document: graphQLDocument, variables: {
            'message': {'text': text}
          }))
          .response;
      safePrint('Send message data received: ${response.data}');
      safePrint('Send message data error: ${response.errors}');
    } on Exception catch (e) {
      safePrint(e);
    }

    // Add the requestAiResponse mutation
    String aiResponseDocument =
        '''
    mutation RequestAiResponse(\$message: SendMessageInput!) {
      requestAiResponse(message: \$message) {
        text
        tenantId
        username
        aiGenerated
      }
    }
  ''';
    try {
      final aiResponse = await Amplify.API
          .mutate(
              request: GraphQLRequest<String>(
                  document: aiResponseDocument,
                  variables: {
                'message': {'text': text}
              }))
          .response;
      safePrint('AI response data received: ${aiResponse.data}');
      safePrint('AI response data error: ${aiResponse.errors}');
    } on Exception catch (e) {
      safePrint(e);
    }
  }

  Future<void> _deleteAllMessages() async {
    String graphQLDocument =
        '''
    mutation DeleteAllMessages {
      deleteAllMessages
    }
  ''';

    try {
      final response = await Amplify.API
          .mutate(request: GraphQLRequest<String>(document: graphQLDocument))
          .response;
      safePrint('Delete all messages data received: ${response.data}');
      safePrint('Delete all messages data error: ${response.errors}');
    } on Exception catch (e) {
      safePrint(e);
    }
  }

  // NOTE: Nothing prevents the api user from subscribing to another tenant's messages, but I'm not going to spend more time on this demo
  Future<void> _subscribeToMessageMutations(String tenantId) async {
    String onSendMessageDocument =
        '''
    subscription OnSendMessage(\$tenantId: ID!) {
      onSendMessage(tenantId: \$tenantId) {
        text
        tenantId
        username
        aiGenerated
      }
    }
    ''';

    String onRequestAiResponseDocument =
        '''
    subscription OnRequestAiResponse {
      onRequestAiResponse {
        text
        aiGenerated
        tenantId
        username
      }
    }
    ''';

    // Add the onDeleteAllMessages subscription
    String onDeleteAllMessagesDocument =
        '''
    subscription OnDeleteAllMessages {
      onDeleteAllMessages
    }
    ''';

    // tenantId = await fetchUserId();
    // Subscribe to onSendMessage
    final Stream<GraphQLResponse<dynamic>> onSendMessageOperation =
        Amplify.API.subscribe(
            GraphQLRequest<String>(
              document: onSendMessageDocument,
              variables: {'tenantId': tenantId},
            ), onEstablished: () {
      safePrint('OnSendMessage subscription established');
    });

    // Subscribe to onRequestAiResponse
    final Stream<GraphQLResponse<dynamic>> onRequestAiResponseOperation =
        Amplify.API.subscribe(
            GraphQLRequest<String>(
              document: onRequestAiResponseDocument,
            ), onEstablished: () {
      safePrint('OnRequestAiResponse subscription established');
    });

    final Stream<GraphQLResponse<dynamic>> onDeleteAllMessagesOperation =
        Amplify.API.subscribe(
            GraphQLRequest<String>(
              document: onDeleteAllMessagesDocument,
            ), onEstablished: () {
      safePrint('OnDeleteAllMessages subscription established');
    });

    // Combine the subscription streams using Rx.merge
    final allSubscriptions = Rx.merge([
      onSendMessageOperation,
      onRequestAiResponseOperation,
      onDeleteAllMessagesOperation,
    ]);

    subscription = allSubscriptions.listen(
      (event) {
        safePrint('Subscription event data received: ${event.data}');
        safePrint('Subscription event data error: ${event.errors}');
        final messageData = json.decode(event.data!);

        if (messageData['onSendMessage'] != null) {
          setState(() {
            _messages.add(messageData['onSendMessage']);
            _streamController.add(_messages);
          });
        } else if (messageData['onRequestAiResponse'] != null) {
          setState(() {
            _messages.add(messageData['onRequestAiResponse']);
            _streamController.add(_messages);
          });
        } else if (messageData['onDeleteAllMessages'] != null) {
          setState(() {
            _messages.clear();
            _streamController.add(_messages);
          });
        }
        SchedulerBinding.instance.addPostFrameCallback((_) {
          _scrollToBottom();
        });
      },
      onError: (Object e) => safePrint('Error in subscription stream: $e'),
    );
  }

  void _scrollToBottom() {
    _scrollController.animateTo(
      _scrollController.position.maxScrollExtent,
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
    );
  }

  @override
  void dispose() {
    subscription?.cancel();
    _streamController.close();
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }
}
