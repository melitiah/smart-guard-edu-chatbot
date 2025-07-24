# chatbot.py

import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

# Resource recommendations
resource_map = {
    "math": [
        "https://www.khanacademy.org/math",
        "https://www.youtube.com/watch?v=Z0kGAz6HYM8"
    ],
    "science": [
        "https://www.sciencekids.co.nz/",
        "https://www.youtube.com/watch?v=VbM0J3j4bXg"
    ],
    "history": [
        "https://www.historyforkids.net/",
        "https://www.youtube.com/watch?v=Y3f9KX1F7mA"
    ],
    "literature": [
        "https://www.litcharts.com/",
        "https://www.youtube.com/watch?v=Y3f9KX1F7mA"
    ]
}

def get_bot_response(message):
    message_clean = message.lower().strip().rstrip(".!?")

    # Direct response to known questions
    if message_clean == "what is 1 + 1":
        return "The answer is 2"
    elif message_clean == "explain photosynthesis":
        return "Photosynthesis is the process by which plants make their own food using sunlight."
    elif message_clean == "who was albert einstein":
        return "Albert Einstein was a famous physicist known for the theory of relativity."

    # Check for resource topic match
    for topic, links in resource_map.items():
        if topic in message_clean:
            links_html = "<br>".join(f'<a href="{link}" target="_blank">{link}</a>' for link in links)
            return f"Here are some great {topic} resources you can check out:<br>{links_html}"

    # Fallback: use OpenAI GPT
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful school assistant chatbot."},
                {"role": "user", "content": message}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI error: {e}")
        return "Sorry, I couldn't fetch a response at the moment."
