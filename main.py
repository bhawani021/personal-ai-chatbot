from app.chatbot import PersonalChatbot

def print_welcome():

    print("\n" + "=" * 50)
    print("       PERSONAL AI CHATBOT")
    print("=" * 50)

    print("\nCommands:")
    print(" /reset - Clear conversation")
    print(" /history - Show conversation history")
    print(" /help - Show help")
    print(" /exit - Exit Chatbot")

def main():

    chatbot = PersonalChatbot()

    print_welcome()

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            command = user_input.lower()

            if command == "/exit":
                print("/nGood bye")
                break
            elif command == "/reset":
                chatbot.conversation_history()
            elif command == "/history":
                for message in chatbot.get_history():
                    print(
                        f"\n{message['role'].upper()}: "
                        f"{message['content']}")

                continue
            elif command == "/help":
                print_welcome()
                continue

            response = chatbot.chat(user_input)
            print(f"\n\nAI: {response}")

        except KeyboardInterrupt:
            print("\n\nChatbot Stopped")
            break

if __name__ == "__main__":
    main()
