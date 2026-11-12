from app.database import Database
from app.repositories.conversation_repository import (
    ConversationRepository,
)


def main():
    database = Database()
    database.initialize()

    repository = ConversationRepository(database)

    # 1. Create conversation
    conversation = repository.create_conversation(title="Learning AI and Python")

    conversation_id = conversation["id"]

    print("\nCreated conversation:")
    print(conversation)

    # 2. Save user message
    repository.add_message(
        conversation_id,
        "user",
        "What is RAG?",
    )

    # 3. Save assistant message
    repository.add_message(
        conversation_id,
        "assistant",
        "RAG stands for Retrieval-Augmented Generation.",
    )

    # 4. Retrieve messages
    messages = repository.get_messages(conversation_id)

    print("\nConversation messages:")

    for message in messages:
        print(f'{message["role"]}: {message["content"]}')

    # 5. List conversations
    print("\nAll conversations:")

    for item in repository.list_conversations():
        print(item["id"], item["title"])

    # 6. Retrieve one conversation
    print("\nRetrieved conversation:")
    print(repository.get_conversation(conversation_id))


if __name__ == "__main__":
    main()
