import random

def chatbot_response(user_input):
    responses = {
        "hello": "Hi there! Ready to learn about calculus?",
        "what is calculus": "Calculus is a branch of mathematics that studies continuous change.",
        "bye": "Goodbye! Stay safe online!"
    }
    return responses.get(user_input.lower(), "I'm not sure about that. Let's look it up together!")

while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        break
    print("Bot:", chatbot_response(user_input))
