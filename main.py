from app.database import Database
from app.repositories.conversation_repository import ConversationRepository
from app.services.persistent_chatbot import PersistentChatbot


def print_help():
    print("""
Available commands:

    /new              Create a new conversation
    /list             List saved conversations
    /open <id>        Open an existing conversation
    /history          Display current conversation history
    /help             Display available commands
    /exit             Exit the application
    """)


def print_conversations(conversations):
    if not conversations:
        print("No saved conversations.")
        return

    print("\nSaved conversations:")

    for conversation in conversations:
        print(
            f"\nTitle: {conversation['title']}"
            f"\nID: {conversation['id']}"
            f"\nUpdated: {conversation['updated_at']}"
        )


def print_history(messages):
    if not messages:
        print("No messages in this conversation.")
        return

    print("\nConversation history:")

    for message in messages:
        role = message["role"].upper()
        print(f"\n{role}: {message['content']}")


def main():
    # Initialize database.
    database = Database()
    database.initialize()

    # Initialize repository and chatbot.
    repository = ConversationRepository(database)
    chatbot = PersistentChatbot(repository)

    # Start a new conversation.
    conversation = chatbot.create_new_conversation()

    print("\n===================================")
    print("      Persistent AI Chatbot")
    print("===================================")
    print(f"Active conversation: {conversation['id']}")
    print("Type /help to see available commands.\n")

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            if user_input == "/exit":
                print("Goodbye!")
                break

            elif user_input == "/help":
                print_help()

            elif user_input == "/new":
                conversation = chatbot.create_new_conversation()
                print(
                    f"New conversation created: {conversation['id']}"
                )

            elif user_input == "/list":
                print_conversations(chatbot.list_conversations())

            elif user_input.startswith("/open "):
                conversation_id = user_input[6:].strip()

                try:
                    conversation = chatbot.switch_conversation(
                        conversation_id
                    )
                    print(f"Opened: {conversation['title']}")
                except ValueError as error:
                    print(error)

            elif user_input == "/history":
                print_history(chatbot.get_history())

            elif user_input.startswith("/"):
                print("Unknown command. Type /help for commands.")

            else:
                response = chatbot.chat(user_input)
                print(f"\nAssistant: {response}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

        except Exception as error:
            print(f"\nError: {error}")


if __name__ == "__main__":
    main()