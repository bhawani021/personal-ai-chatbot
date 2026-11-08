import ollama

from ollama import Client

from app.config import (
    OLLAMA_MODEL,
    OLLAMA_HOST,
    SYSTEM_PROMPT
)


class PersonalChatbot:

    def __init__(self):
        self.model = OLLAMA_MODEL

        self.client = Client(
            host=OLLAMA_HOST
        )

        self.conversation_history = []

        print(f"Loaded model: {self.model}")

    def chat(self, user_message: str) -> str:
        # Prepare conversation context
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            *self.conversation_history,
            {
                "role": "user",
                "content": user_message
            }
        ]

        try:
            print("\nDEBUG: Sending request to Ollama...")

            # Send request to Ollama
            response = self.client.chat(
                model=self.model,
                messages=messages
            )

            # Extract AI response
            assistant_message = (
                response.message.content
            )

            print("DEBUG: Extracted message:",
                  repr(assistant_message))

            if not assistant_message:
                return "ERROR: Ollama returned an empty response."

            # update conversation history after getting a successful response
            self.conversation_history.extend([
                {
                    "role": "user",
                    "content": user_message
                },
                {
                    "role": "assistant",
                    "content": assistant_message
                }
            ])

            return assistant_message

        except Exception as error:

            print(f"\nChatbot error: {error}")

            return "Sorry, I could not process your request, Please try again"

    def reset_conversation(self):

        self.conversation_history.clear()
        print("Conversation history cleared")

    def get_history(self):
        return self.conversation_history
