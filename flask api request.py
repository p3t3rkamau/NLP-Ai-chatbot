from flask import Flask, render_template, request
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chatbot', methods=['POST'])
def chatbot():
    # Set the API endpoint URL
    url = "http://localhost:5000/api/chat"

    # Set the user input message from the form data
    user_message = request.form['user_message']

    # Set the payload as a JSON object
    payload = {"user_message": user_message}

    # Send the POST request and get the response
    response = requests.post(url, json=payload)
    

    # Get the chatbot's response and conversation history from the response JSON object
    chatbot_response = response.json()["chatbot_response"]
    conversation_history = response.json()["conversation_history"]

    # Render the chatbot response and conversation history on the page
    return render_template('index.html', chatbot_response=chatbot_response, conversation_history=conversation_history)

if __name__ == '__main__':
    app.run(debug=True, port=5001)

