import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from google import genai
from google.genai import types
import chatbot_config as config

load_dotenv()

app = Flask(__name__)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key or api_key == "your_gemini_api_key_here":
    print("WARNING: GEMINI_API_KEY not set properly in .env")
client = genai.Client(api_key=api_key) if api_key and api_key != "your_gemini_api_key_here" else None

conversation_history = []

@app.route("/")
def index():
    return render_template(
        "index.html",
        topic=config.TOPIC,
        brand=config.BRAND_NAME,
        tagline=config.TAGLINE,
        assistant=config.ASSISTANT_NAME,
        welcome=config.WELCOME_MESSAGE,
        quick_actions=config.QUICK_ACTIONS,
        nav_items=config.NAV_ITEMS,
    )

@app.route("/chat", methods=["POST"])
def chat():
    global conversation_history
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()
        if not user_message:
            return jsonify({"error": "Empty message"}), 400

        if not client:
            return jsonify({
                "reply": "API key is not configured. Please set GEMINI_API_KEY in the .env file and restart the server."
            }), 500

        contents = []
        for msg in conversation_history[-8:]:
            contents.append(msg)

        contents.append(
            types.Content(
                role="user",
                parts=[types.Part(text=user_message)]
            )
        )

        response = client.models.generate_content(
            model=config.MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=config.SYSTEM_PROMPT,
                temperature=0.7,
                max_output_tokens=2048,
            ),
        )

        reply = response.text if response and response.text else "I'm having trouble generating a response right now. Please try again."

        conversation_history.append(
            types.Content(role="user", parts=[types.Part(text=user_message)])
        )
        conversation_history.append(
            types.Content(role="model", parts=[types.Part(text=reply)])
        )

        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]

        return jsonify({"reply": reply})

    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({
            "reply": "Something went wrong while contacting the AI. Please check your API key and try again in a moment."
        }), 500

@app.route("/reset", methods=["POST"])
def reset():
    global conversation_history
    conversation_history = []
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
