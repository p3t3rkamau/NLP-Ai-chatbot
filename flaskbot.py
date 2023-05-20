from flask import Flask, render_template, request, jsonify, make_response,redirect, url_for,flash, Response
import json
from flask_cors import cross_origin
import random
import time
import webbrowser
import openai
import wikipedia
from bs4 import BeautifulSoup
import os
import datetime
import requests
from io import BytesIO
from PIL import Image
from flask_login import login_required,login_user
# import pyautogui
from urllib.parse import urlparse
from PIL import Image
import psutil
import json
import random
import json
import torch
from model import NeuralNet
from nltk_utils import bag_of_words, tokenize
# import tensorflow as tf
# from tensorflow.keras.preprocessing.text import Tokenizer
# from tensorflow.keras.preprocessing.sequence import pad_sequences

from flask_login import LoginManager, UserMixin

app = Flask(__name__)

app.secret_key = 'my secret key'
valid_api_keys = ['api_key_1','api_key_2', 'api_key_3']


login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin):
    def __init__(self, username, password):
        self.id = username
        self.password = password


# Define a dictionary of users
users = {'user1': User('user1', 'password1'),
         'user2': User('user2', 'password2')}


@login_manager.user_loader
def load_user(user_id):
    # Return the user object for the given user_id
    return users.get(user_id)

@app.route('/index')
def home():
    # Load conversation history from cookies
    conversation_history = request.cookies.get('conversation_history')
    if conversation_history:
        conversation_history = json.loads(conversation_history)
    else:
        conversation_history = []
    return render_template('index.html', conversation_history=conversation_history, show_game_input=False)

@app.route('/')
def main_page():
    return render_template('main_page.html')




@app.route('/chat', methods=['POST'])
@cross_origin()
def chat():
    try:
        user_message = request.form['user_message'] 
        
        last_query = read_last_query()  # Read the last executed query

        chatbot_response = generate_chatbot_response(user_message, last_query)

        # Update the last executed query
        write_last_query(user_message)
        # Get user input from the form
     # Generate chatbot response
        # Send feedback to server
        # feedback_type = request.form.get('feedbackType')
        # print(feedback_type)  # Get feedback type, default to 'none'

        # # Send feedback about the chatbot response to the server
        # sendFeedback(user_message, chatbot_response, feedback_type=feedback_type)

        # Load conversation history from cookies
        conversation_history = request.cookies.get('conversation_history')
        if conversation_history:
            conversation_history = json.loads(conversation_history)
        else:
            conversation_history = []

        # Append new message to conversation history
        conversation_history.append({'user': user_message, 'chatbot': chatbot_response})

        # Save conversation history to cookies
        response = make_response(render_template('index.html', chatbot_response=chatbot_response, conversation_history=conversation_history, show_game_input=False))
        response.set_cookie('conversation_history', json.dumps(conversation_history))

        # Append new messages to chatlog.txt
        with open('chatlog.txt', 'a', encoding='utf-8') as f:
          f.write(f'{datetime.datetime.now()} - User: {user_message}\n')
          f.write(f'{datetime.datetime.now()} - Chatbot: {chatbot_response}\n')
            
        # Return the chatbot response
        return response

    except KeyError:
        error_message = 'Invalid request, missing user input'
        with open('chatlog.txt', 'a', encoding='utf-8') as f:
            f.write(f'{datetime.datetime.now()} - error: {error_message}\n')
        chatbot_response = '' # set chatbot_response to empty string
        return render_template('index.html', chatbot_response=chatbot_response, error_message=error_message)
                
    except Exception as e:
        error_message = str(e)
        with open('chatlog.txt', 'a', encoding='utf-8') as f:
            f.write(f'{datetime.datetime.now()} - error: {error_message}\n')
        chatbot_response = '' # set chatbot_response to empty string
        return render_template('index.html', chatbot_response=chatbot_response, error_message=error_message)
@app.route('/intents')
def get_intents():
    with open('intents.json', 'r') as f:
        intents = json.load(f)
    return intents


@app.route('/api_usage')
def get_api_usage():
    with open('api_key_usage.json', 'r') as f:
        intents = json.load(f)
    return intents

@app.route('/users-feedback')
def chatbot_ratings():
    with open('feedback.json', 'r', encoding='utf-8') as f:
        feedback_data = f.read()
    return feedback_data



# Load API key usage data from file, or create a new empty dictionary if file does not exist
api_key_usage = {}
if os.path.isfile('api_key_usage.json'):
    with open('api_key_usage.json', 'r') as f:
        api_key_usage = json.load(f)
else:
    with open('api_key_usage.json', 'w') as f:
        json.dump(api_key_usage, f)


# Save the updated API key usage data to file
with open('api_key_usage.json', 'w') as f:
    json.dump(api_key_usage, f)


@app.route('/api/chat', methods=['POST'])
@cross_origin()
def chatbot_api():
    try:
    
        user_message = request.json['user_message']

        api_key = request.json.get('api_key')

        # Check if the API key is valid
        if api_key not in valid_api_keys:
            return jsonify({'error': 'Invalid API key'}), 401  # Unauthorized

        # Check if the API key has exceeded the maximum number of requests
        if api_key_usage.get(api_key, 0) >= 100:
            return jsonify({'error': 'API key has reached maximum number of requests. Please upgrade your plan.'}), 403  # Forbidden

        # Increment the number of requests made by the API key
        api_key_usage[api_key] = api_key_usage.get(api_key, 0) + 1

        with open('api_key_usage.json', 'w') as f:
            api_key_usage_data = {
                'api_key': api_key,
                'usage': api_key_usage[api_key],
                'browser': request.user_agent.browser or 'Unknown Browser'
            }
            json.dump(api_key_usage_data, f)
        # Generate chatbot response
        last_query = read_last_query()  # Read the last executed query

        chatbot_response = generate_chatbot_response(user_message, last_query)

        # Update the last executed query
        write_last_query(user_message)

        # Load conversation history from cookies
        conversation_history = request.cookies.get('conversation_history')
        if conversation_history:
            conversation_history = json.loads(conversation_history)
        else:
            conversation_history = []

        # Append new message to conversation history
        conversation_history.append({'user': user_message, 'chatbot': chatbot_response})

        # Save conversation history to cookies
        response = jsonify({
            'chatbot_response': chatbot_response,
            'conversation_history': conversation_history
        })
        response.set_cookie('conversation_history', json.dumps(conversation_history))

        # Append new messages to chatlog.txt
        with open('chatlog.txt', 'a', encoding='utf-8') as f:
            f.write(f'{datetime.datetime.now()} - User: {user_message}\n')
            f.write(f'{datetime.datetime.now()} - Chatbot: {chatbot_response}\n')

        # Return the chatbot response and conversation history
      
        return response
      



    except KeyError:
        error_message = 'Invalid request, missing user input'
        with open('chatlog.txt', 'a', encoding='utf-8') as f:
            f.write(f'{datetime.datetime.now()} - error: {error_message}\n')
        chatbot_response = '' # set chatbot_response to empty string
        return jsonify({'error': error_message}), 400
                
    except Exception as e:
        error_message = str(e)
        with open('chatlog.txt', 'a', encoding='utf-8') as f:
            f.write(f'{datetime.datetime.now()} - error: {error_message}\n')
        chatbot_response = '' # set chatbot_response to empty string
        return jsonify({'error': error_message}), 500


@app.route('/admin/chatlog')
@login_required
def view_chatlog():
    # Open chatlog.txt and loop through lines
    chatlog_lines = []
    with open("chatlog.txt", "r", encoding='utf-8') as f:
        for line in f:
            line = line.strip()  # Remove whitespace at beginning and end of line
            if "User:" in line:
                chatlog_lines.append((line, "user"))
            elif "Chatbot:" in line:
                chatlog_lines.append((line, "chatbot"))
            elif "error:" in line:
                chatlog_lines.append((line, "error"))
            else:
                chatlog_lines.append((line, ""))

    # Read feedback.json and create list of feedback data tuples
    

    # Combine chatlog and feedback data into a single list and sort by timestamp
    combined_data = chatlog_lines
  

    return render_template('chatlog.html', lines=combined_data)



@app.route('/chatpage')
def chatpage():
    return render_template('chat.html')



@app.route('/chatbot', methods=['POST'])
def chatbot():
    # Check if API key is valid
    # Set the API endpoint URL
    url = "http://localhost:5000/api/chat"

    # Set the user input message from the form data
    user_message = request.form['user_message']

    # Set the payload as a JSON object
    payload = {"user_message": user_message}

    # Send the POST request and get the response
    response = requests.post(url, headers={'api_key': valid_api_keys}, json=payload)

    # Get the chatbot's response from the response JSON object
    chatbot_response = response.json()["chatbot_response"]

    # Render the chatbot response on the page
    return render_template('chat.html', chatbot_response=chatbot_response)





@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.get(username)
        if user and user.password == password:
            login_user(user)
        
            # Authentication successful, redirect to chatlog page
            return redirect(url_for('view_chatlog'))
        else:
            # Authentication failed, show error message
            error = 'Invalid username or password'
            return render_template('login.html', error=error)
    else:
        # Show login form
        return render_template('login.html')


@app.route('/clear')
def clear():
    # Clear conversation history from cookies
    response = make_response(render_template('index.html', conversation_history=[]))
    response.set_cookie('conversation_history', '', expires=0)

    # Update conversation history variable
    conversation_history = []

    # Return the response with the cleared conversation history cookie
    return response

@app.route('/admin/clear_chatlog', methods=['POST'])
@login_required
def clear_chatlog():
    with open("chatlog.txt", "w", encoding='utf-8') as f:
        f.write("")
    flash("Chat log cleared.")
    return redirect(url_for('view_chatlog'))


@app.route('/embedded-code')
def embedded_code():
    return render_template('embedded_code.html')

@app.route('/game', methods=['GET', 'POST'])
def game():
    if request.method == 'POST':
        player_choice = request.form['player_choice']
        if player_choice in ['rock', 'paper', 'scissors']:
            moves = ["rock", "paper", "scissors"]
            computer_choice = random.choice(moves)
            if player_choice == computer_choice:
                result = "The match is a draw."
            elif player_choice == "rock" and computer_choice == "scissors":
                result = "You win!"
            elif player_choice == "rock" and computer_choice == "paper":
                result = "The computer wins."
            elif player_choice == "paper" and computer_choice == "rock":
                result = "You win!"
            elif player_choice == "paper" and computer_choice == "scissors":
                result = "The computer wins."
            elif player_choice == "scissors" and computer_choice == "paper":
                result = "You win!"
            elif player_choice == "scissors" and computer_choice == "rock":
                result = "The computer wins."
            return render_template('index.html', result=result, show_game_input=False)
        else:
            error_message = "Invalid choice. Please choose rock, paper, or scissors."
            return render_template('index.html', error_message=error_message, show_game_input=False)
    else:
        return render_template('index.html')

def sendFeedback(user_message, chatbot_response, feedback_type):
    """
    Sends feedback about the chatbot response to the server.
    """
    try:
        # Store the feedback in a JSON object and append it to a file for later review
        feedback = {
            'timestamp': str(datetime.datetime.now()),
            'user_message': user_message,
            'chatbot_response': chatbot_response,
            'feedback_type': feedback_type
        }
        with open('feedback.json', 'a', encoding='utf-8') as f:
            
            f.write(json.dumps(feedback) + ','+'\n')
    except Exception as e:
        error_message = str(e)
        with open('chatlog.txt', 'a', encoding='utf-8') as f:
            f.write(f'{datetime.datetime.now()} - error: {error_message}\n')
        return '', 204  # Return an empty response with status code 204 (no content)


@app.route('/feedback', methods=['POST'])
@cross_origin()
def feedback():
    try:
        feedback_data = request.get_json()  # Get feedback data as JSON

        user_message = feedback_data['userMessage']  # Get user message
        chat_response = feedback_data['chatbotResponse']  # Get chatbot response
        feedback_type = feedback_data['feedbackType']  # Get feedback type

        # Store the feedback in a JSON object and append it to a file for later review
        sendFeedback(user_message, chat_response, feedback_type)

        return '', 204  # Return an empty response with status code 204 (no content)
    except (KeyError, TypeError):
        return '', 400  # Return an empty response with status code 400 (bad request)
    except Exception as e:
        error_message = str(e)
        with open('chatlog.txt', 'a', encoding='utf-8') as f:
            f.write(f'{datetime.datetime.now()} - error: {error_message}\n')
        return '', 500  # Return an empty response with status code 500 (internal server error)




def website_content(user_message):
    # Extract website URL from user message
    url = user_message.replace('get website content', '').strip()
    # Make GET request to website and extract content
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    content = soup.get_text()
    # Return content to user
    return content
    
def remember_name(person_name):
    # Store the person's name in a file
    with open('names.txt', 'w') as f:
        f.write(person_name)
    return "Okay👍, I will remember that your name is " + person_name


def update_api_key(api_key):
    # Write the new API key to the text file
    with open("api_key.txt", "w") as f:
        f.write(api_key)
    # Update the API key variable
    openai.api_key = api_key
    return "API key updated successfully!"

def recall_name():
    # Read the person's name from the file and return it
    if os.path.exists('names.txt'):
        with open('names.txt', 'r') as f:
            person_name = f.read().strip()
        if 'matthew' in person_name:
            return "Your name is " + person_name + ' the same guy who fucks'
        elif 'patrick' in person_name:
            return 'pato the pianist....loading your files'    
        else:
            return 'sorry i didnt get your name quite well, please remind me'    
    return "I don't remember your name. Please remind me."
       


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

with open('intents.json', 'r') as json_data:
    intents = json.load(json_data)

FILE = "data.pth"
data = torch.load(FILE)

input_size = data["input_size"]
hidden_size = data["hidden_size"]
output_size = data["output_size"]
all_words = data['all_words']
tags = data['tags']
model_state = data["model_state"]

model = NeuralNet(input_size, hidden_size, output_size).to(device)
model.load_state_dict(model_state)
model.eval()

# Function to read the last executed query from the JSON file
def read_last_query():
    with open('query.json', 'r') as file:
        data = json.load(file)
    return data['last_query']

# Function to write the last executed query to the JSON file
def write_last_query(last_query):
    data = {'last_query': last_query}
    with open('query.json', 'w') as file:
        json.dump(data, file)    

def load_intents_from_file(file_path):
    with open(file_path, 'r') as file:
        intents = json.load(file)
    return intents




def generate_chatbot_response(user_message, last_query):
    intents = load_intents_from_file('intents.json')  # Load intents from a JSON file

    last_query_response = next((intent['responses'][0] for intent in intents['intents'] if last_query in intent['patterns']), None)

    if last_query_response:
        response = last_query_response
    else:
        user_words = user_message.lower().split()  # Define the user_words variable here

        for intent in intents['intents']:
            if intent['tag'] != 'Default':
                for pattern in intent['patterns']:
                    pattern_words = pattern.lower().split()

                    if all(word in user_words for word in pattern_words):
                        response = random.choice(intent['responses'])
                        return response

  

    # Process the user's current message and generate a response based on it
    # Add your code here to generate a response based on the user_message parameter


    sentence = tokenize(user_message)
    X = bag_of_words(sentence, all_words)
    X = X.reshape(1, X.shape[0])
    X = torch.from_numpy(X).to(device)

    output = model(X)
    _, predicted = torch.max(output, dim=1)

    tag = tags[predicted.item()]

    probs = torch.softmax(output, dim=1)
    prob = probs[0][predicted.item()]
    
    if prob.item() > 0.75:
        for intent in intents['intents']:
            if tag == intent["tag"]:
                return random.choice(intent['responses'])
    if ' ' not in user_message:
        return "I'm sorry, I didn't understand that. Can you please try again?"
        
    user_words = user_message.lower().split()
    # for intent in intents['intents']:
    #     for pattern in intent['patterns']:

    #         pattern_words = pattern.lower().split()

    #         if all(word in user_words for word in pattern_words):
    #             return random.choice(intent['responses'])

    #         return "I'm sorry, I didn't understand that. Can you please try again?"
    if 'google' in user_words:
        # Code to open google search in browser
        command = user_message.lower()
        f = command.replace('google', '')
        url = f"https://google.com/search?q=" + f
        webbrowser.get().open(url)
        return 'Here is what I found for ' + f + ' on Google:'

    elif 'beast mode' in user_message.lower():
        # Strip the words after "beast mode" and use OpenAI API to generate a response
        beast_mode_query = user_message.lower().split('beast mode')[1].strip()
         # Read the API key from a text file
        with open("api_key.txt", "r") as f:
            api_key = f.read().strip()
            openai.api_key = api_key
        model_engine = 'text-davinci-002'
        prompt = f'User: {beast_mode_query}\nChatbot:'
        response = openai.Completion.create(
            engine=model_engine,
            prompt=prompt,
            max_tokens=10
        )
        return response.choices[0].text.strip()


    elif user_message.startswith("update api") or user_message.startswith("change api"):
        # Update the API key
        new_api_key = user_message[11:]
        return update_api_key(new_api_key)

    elif 'get' in user_words and 'website' in user_words and 'content' in user_words:  
        return website_content(user_message)

    elif 'who is' in user_message:
        person_name = user_message.replace('who is', '').strip()
        try:
            # Try to get the summary of the Wikipedia page
            summary = wikipedia.summary(person_name, sentences=3)
            return summary
        except wikipedia.exceptions.DisambiguationError as e:
            # If the Wikipedia page is ambiguous, ask the user to clarify their search
            return f"I'm not sure which {e.title} you're referring to. Can you please be more specific?"
        except wikipedia.exceptions.PageError:
            # If no Wikipedia page is found, inform the user
            return f"Sorry, I couldn't find any information about {person_name}."
  
    elif 'battery' in user_message.lower():
        battery_percent = psutil.sensors_battery().percent
        if battery_percent != None:
            return f"Your current battery level is {battery_percent}%."
        else:
            return "Sorry, I couldn't retrieve the current battery level." 
    elif 'game' in user_words:
        game_choices = ['rock', 'paper', 'scissors']
        if any(word in game_choices for word in user_words):
            return render_template('index.html', show_game_input=True)
        else:
            return 'I\'m sorry, I don\'t know that game.😞'
            
    elif 'remember my name is' in user_message or 'no my name is' in user_message or 'thats not true my name is' in user_message or 'wrong my name is' in user_message:
        person_name = user_message.replace('remember my name is' or 'thats not true my name is' or 'no my name is' or 'wrong my name is', '').strip()
        return remember_name(person_name)
    elif 'time' in user_message.lower():
        current_time = datetime.datetime.now().strftime("%H:%M")
        return f"The current time is {current_time}.⌚"    
    elif 'what is my name' in user_message or 'whats my name' in user_message:
        return recall_name()
    elif 'fuck u' in user_message or 'fuck you' in user_message:
       return 'fuck u too mate😂'  
    elif 'what can you do' in user_message or 'your capabilities' in user_message:
       return """ Respond to user input with a chatbot response.
                    Keep track of conversation history and display it on the webpage.
                    Save the conversation history to a cookie for the user's browser.
                    Allow login with a pre-defined set of users.
                    Allow clearing of the conversation history and the chat log.
                    Redirect to different pages based on user input.
                    Access Wikipedia to search for information.
                    Access and parse HTML to extract information.
                    Access and interact with the operating system.
                    Access screenshots of the user's screen.
                    Access and interact with the computer's hardware.
                    Save and retrieve data from cookies.
                    Manage user sessions"""
    elif user_message.startswith("code for "):
        query = user_message[9:].lower()
        if "center" in query:
            html_code = '<div class="centered">Centered content</div>'
            css_code = '''.centered {
                            position: absolute;
                            top: 50%;
                            left: 50%;
                            transform: translate(-50%, -50%);
                        }'''
            return f"Here's the HTML code:\n\n```html\n{html_code}\n```\n\nAnd here's the CSS code:\n\n```css\n{css_code}\n```"
            


        elif "responsive navbar" in query:
            return "#navbar {\n    display: flex;\n    flex-wrap: wrap;\n    justify-content: space-between;\n    align-items: center;\n}\n\n#navbar ul {\n    display: flex;\n    flex-direction: column;\n    align-items: center;\n}\n\n#navbar li {\n    padding: 1rem;\n}"
        elif "slider" in query:
            return "/* CSS for a simple image slider */\n\n.slider {\n    max-width: 100%;\n    position: relative;\n}\n\n.slider img {\n    width: 100%;\n}\n\n.slider .prev, .slider .next {\n    position: absolute;\n    top: 50%;\n    transform: translateY(-50%);\n    font-size: 2rem;\n    font-weight: bold;\n    cursor: pointer;\n}\n\n.slider .prev {\n    left: 1rem;\n}\n\n.slider .next {\n    right: 1rem;\n}"
        else:
                return "No code snippet found for the query. Please try another query."

                #########################################
    elif 'activate code expert' in user_message.lower():
            return redirect(url_for('embedded_code'))
            # ########################################
    elif 'clear chat' in user_message.lower():
            return redirect(url_for('clear'))

    # elif 'screenshot' in user_message.lower:
    #     myscreenshot = pyautogui.screenshot()
    #     myscreenshot.save(r'screen.jpg')
    #     img = Image.open('screen.jpg')
    #     img.show()
    #     image_url = 'http://your-domain.com/screenshots/screen.jpg'
    #     return f"Screenshot saved. You can view it at {image_url}." 


    elif 'show me a picture' in user_message.lower():
        access_key = '1K6e0o13EJMLBbNVfyzwmzVCCA3Vxd5MBG3F5-PeHVE'
        # get a random search term based on the user's input
        search_term = user_message.lower().replace('show me a picture of ', '')
        # make a request to the Unsplash API to search for images
        url = 'https://api.unsplash.com/search/photos/'

        headers = {'Authorization': f'Client-ID {access_key}'}
        params = {'count':2, 'query': search_term}

        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        # extract the URLs from the API response
        image_urls = [item['urls']['regular'] for item in data['results']]

        # open each image using Pillow and append to a list
        images = []
        for url in image_urls:
            response = requests.get(url)
            img = Image.open(BytesIO(response.content))
            images.append(img)

        # save each image to a BytesIO object and append to a list of image data URLs
        data_urls = []
        for i, img in enumerate(images):
            img_data = BytesIO()
            img.save(img_data, format='PNG')
            data_url = f"data:image/png;base64,{img_data.getvalue().hex()}"
            data_urls.append(data_url)

        # create HTML for the images using the data URLs
        image_tags = [f'<img src="{url}"/>' for url in data_urls]

        # return a message with the HTML for the images
        message = {'content': f'Here are some pictures for you: {"".join(image_tags)}', 'type': 'text'}
        return image_tags



        # if response.status_code == 200:
        #     # Extract the photo URLs from the response
        #     photos = response.json()['results']
        #     for photo in photos:
        #         print(photo['urls']['regular'])
        # else:
        #     return(f'Request failed with status code {response.status_code}')

        # parse the JSON response to get a list of image URLs
        # data = json.loads(response.text)

        # # extract the URLs from the API response
        # image_urls = [item['urls']['regular'] for item in data]

        # # create HTML for the links to the images
        # link_tags = [f'<a href="{url}">Image {i+1}</a>' for i, url in enumerate(image_urls)]

        # return a message with the links to the images
        # message = {'content': f'Here are some pictures for you: {", ".join(response)}', 'type': 'text'}
        # return message
    else:
    # If no matching pattern is found, return a default response
        default_responses = [intent['responses'] for intent in intents['intents'] if intent['tag'] == 'Default']
        response = random.choice(default_responses[0]) if default_responses else "I'm sorry, I don't have the information about that question."
        return response

if __name__ == '__main__':
    app.run(debug=True, threaded=True)







# The load_intents_from_file function loads the intents from the "intents.json" file, which contains information about different intents, their patterns, and corresponding responses.

# The generate_chatbot_response function takes two parameters: user_message (the current user message) and last_query (the last executed query).

# It attempts to find a response based on the last_query by iterating through the intents and their patterns. If a pattern matches the last_query, it selects the corresponding response.

# If a response is found based on the last_query, it is returned as the chatbot's response.

# If no response is found based on the last_query, it processes the user_message to generate a response using a machine learning model. The code you provided uses tokenization, bag-of-words representation, and a trained model to predict a response based on the user's message.

# If the prediction from the machine learning model has a high probability (greater than 0.75), it selects a random response from the intents associated with the predicted tag.

# If the user message does not contain any spaces (i.e., it's a single word), it returns a default "I'm sorry, I didn't understand that. Can you please try again?" response.

# If the user message contains the word "google", it opens a web browser and performs a Google search using the remaining part of the message. The chatbot then returns a response indicating the search result.