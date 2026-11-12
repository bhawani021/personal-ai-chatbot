import logging

from app.config import LOG_LEVEL, validate_config
from app.database import Database
from app.exceptions import ChatbotError
from app.logging_config import configure_logging
from app.repositories.conversation_repository import ConversationRepository
from app.services.persistent_chatbot import PersistentChatbot


def print_help():
    print("""
    ================================================
                 PERSISTENT AI CHATBOT
    ================================================

    Conversation commands:

      /new                  Create a new conversation
      /list                 List all conversations
      /open <id>            Open an existing conversation
      /rename <title>       Rename the active conversation
      /delete [id]          Delete active or specified conversation
      /search <keyword>     Search conversations

    Information commands:

      /history              Display conversation history
      /info                 Display active conversation information
      /help                 Display available commands
      /exit                 Exit the application

    ================================================
    """)


def print_conversations(conversations):
    if not conversations:
        print("No saved conversations.")
        return

    print("\nSaved conversations:")
    print("-" * 90)

    for index, conversation in enumerate(conversations, start=1):
        print(f"{index}. {conversation['title']}")
        print(f"    ID: {conversation['id']}")
        print(f"    Updated: {conversation['updated_at']}")
        print("-" * 90)


def print_history(messages):
    if not messages:
        print("No messages in this conversation.")
        return

    print("\nConversation history:")
    print("-" * 70)

    for message in messages:
        role = message["role"].upper()

        print(f"\n{role}")
        print(message["content"])
        print(f"Time: {message['created_at']}")

    print("-" * 70)


def print_info(chatbot):
    conversation = chatbot.get_current_conversation()

    if conversation is None:
        print("\nNo active conversation")
        return

    messages = chatbot.get_history()

    user_messages = sum(1 for message in messages if message["role"] == "user")

    assistant_messages = sum(
        1 for message in messages if message["role"] == "assistant"
    )

    print("\nActive Conversation Information")
    print("-" * 50)
    print(f"Title: {conversation['title']}")
    print(f"ID: {conversation['id']}")
    print(f"Created: {conversation['created_at']}")
    print(f"Updated: {conversation['updated_at']}")
    print(f"Total messages: {len(messages)}")
    print(f"User messages: {user_messages}")
    print(f"Assistant messages: {assistant_messages}")
    print("-" * 50)


def main():
    configure_logging(level=getattr(logging, LOG_LEVEL))

    validate_config()

    logger = logging.getLogger(__name__)

    logger.info("Starting Persistent AI chatbot")

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
    print("=====================================")
    print(f"Active chat: {conversation['title']}")
    print(f"Conversation ID: {conversation['id']}")
    print("\nType /help for available commands")

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
                print(f"New conversation created: \nID: {conversation['id']}")

            elif user_input == "/list":
                print_conversations(chatbot.list_conversations())

            elif user_input.startswith("/open "):
                conversation_id = user_input[6:].strip()

                try:
                    conversation = chatbot.switch_conversation(conversation_id)
                    print(f"Opened: {conversation['title']}")
                except ValueError as error:
                    print(error)

            elif user_input.startswith("/rename"):
                parts = user_input.split(maxsplit=1)

                if len(parts) < 2 or not parts[1].strip():
                    print("Usage: /rename <new title>")
                    continue

                title = parts[1].strip()

                active_conversation = chatbot.get_current_conversation()

                if active_conversation is None:
                    print("No active conversation")
                    continue

                chatbot.rename_conversation(active_conversation["id"], title)

                print(f"Conversation renamed to: {title}")

            elif user_input == "/delete" or user_input.startswith("/delete "):
                parts = user_input.split(maxsplit=1)

                if len(parts) == 2:
                    conversation_id = parts[1].strip()
                else:
                    active_conversation = chatbot.get_current_conversation()

                    if active_conversation is None:
                        print("No active conversation.")
                        continue

                    conversation_id = active_conversation["id"]

                confirmation = (
                    input(f"Delete conversation {conversation_id}? (y/n): ")
                    .strip()
                    .lower()
                )

                if confirmation != "y":
                    print("Delete cancelled")
                    continue

                if chatbot.delete_conversation(conversation_id):
                    print("Conversation deleted")

                    # If the active conversation was deleted
                    # resume another conversation or create one
                    if chatbot.get_current_conversation() is None:
                        conversation = chatbot.resume_latest_conversation()
                        print(f"Active chat: {conversation['title']}")
                else:
                    print("Conversation not found.")

            elif user_input == "/search":
                print("Usage: /search <keyword>")

            elif user_input.startswith("/search "):
                keyword = user_input.split(maxsplit=1)[1].strip()

                if not keyword:
                    print("Usage: /search <keyword>")
                    continue

                results = chatbot.search_conversations(keyword)

                print_conversations(results)

            elif user_input == "/history":
                print_history(chatbot.get_history())

            elif user_input == "/info":
                print_info(chatbot)

            elif user_input.startswith("/"):
                print("Unknown command. Type /help for commands.")

            else:
                response = chatbot.chat(user_input)
                print(f"\nAssistant: {response}")

        except ChatbotError as error:
            print(f"\nApplication error: {error}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

        except Exception:
            logger.exception("Unexpected CLI error")
            print("\nAn unexpected error occurred. Check logs/chatbot.log.")


if __name__ == "__main__":
    main()
