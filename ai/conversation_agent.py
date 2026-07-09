from ai.conversation import Conversation


class ConversationAgent:

    def __init__(self, provider):

        self.provider = provider
        self.conversation = Conversation()

    def answer(self, user_text):

        self.conversation.add_user(user_text)

        response = ""

        stream = self.provider.stream_chat(
            self.conversation.get_messages()
        )

        for chunk in stream:

            token = chunk.choices[0].delta.content

            if token:
                response += token

        self.conversation.add_assistant(response)

        return response