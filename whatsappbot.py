
from flask import Flask, request
import requests
import os
from dotenv import load_dotenv
import openai
import queue

#followed this link to build the bot app
#https://www.pragnakalp.com/automate-messages-using-whatsapp-business-api-flask-part-1/
#https://www.pragnakalp.com/build-an-automated-ai-powered-whatsapp-chatbot-with-chatgpt-using-flask/
#HTTPS for flask: https://www.educba.com/flask-https/
# snap install ngrok (this one seemed to add ngrok)
# pip3 install ngrok (this one probably install ngrok lib for python)
# ngrok http 5020 --log=stdout > ngrok.log &

load_dotenv()

APP_SELF_TOKEN = os.getenv('APP_SELF_TOKEN')

MAX_QUEUE_SIZE = int(os.getenv('MAX_QUEUE_SIZE'))
OPENAI_KEY = os.getenv('OPENAI_KEY')

BOT_NAME = os.getenv('BOT_NAME')

# Set up the OpenAI API client
openai.api_key = OPENAI_KEY

conversations = queue.Queue()

msg_id_queue = queue.Queue()

def check_msg_id(msg_id):
    for x in range(int(msg_id_queue.qsize())):
        if(msg_id_queue.queue[x] == msg_id):
            return True
        
    msg_id_queue.put(msg_id)

    if(msg_id_queue.qsize() > 20):
        msg_id_queue.get()

    return False

app = Flask(__name__)

@app.route('/')
def index():
   return "Hello"
 
def send_msg(phonenum, msg):
   headers = {
       'Authorization': 'Bearer EAACJhIajgZAMBAM2NcLksBr0LJpN8s4YB7ZB4mXiF7di0bQg0IZBtyLGSV6kGGO5ia97uTUa37302x5D19uBEWxSXglC9iYGaKXHZCXHDzrrT0zAsjBYx2MSXkaZClNjs2gE21ZCg0p5PnDySWuvNzS3oAtFtsMsVZCrBLIZAi8ZCrUqTJSbcm9OVDR7kz3zqmPXZAxNcfFTWP4AZDZD',
   }
   json_data = {
       'messaging_product': 'whatsapp',
       'to': phonenum,
       'type': 'text',
       "text": {
           "body": msg
       }
   }
   response = requests.post('https://graph.facebook.com/v13.0/120622404311891/messages', headers=headers, json=json_data)
   print(response.text)

#@app.route('/receive_msg', methods=['POST','GET'])
#def webhook():
#   print("webhook is called")
#   if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
#       if not request.args.get("hub.verify_token")== APP_SELF_TOKEN:
#           return "Verification token missmatch", 403
#       return request.args['hub.challenge'], 200
#   return "Hello world", 200

@app.route('/receive_msg', methods=['POST','GET'])
def webhook():

    #print("webhook 1")

    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token")== APP_SELF_TOKEN:
            #print("webhook 2")
            return "Verification token missmatch", 403
        
        #print("webhook 3")
        return request.args['hub.challenge'], 200

    
    #print("webhook 4")

    #print(request)
    res = request.get_json()
    print(res)    

    try:
        if res['entry'][0]['changes'][0]['value']['messages'][0]['id']:
            #print(res['entry'][0]['changes'][0]['value']['messages'][0]['id'])

            new_msg = res['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']
            print("Incoming Message:",  new_msg, flush=True)
            
            model_engine = "gpt-3.5-turbo"
            openapi_prompt = new_msg + " Please answer within 20 words."

            if check_msg_id(res['entry'][0]['changes'][0]['value']['messages'][0]['id']): #already processed
                return '200 OK HTTPS.'
            
            messages = [
            #system message first, it helps set the behavior of the assistant
            {"role": "system", "content": "You are a helpful assistant."}, 
            ]
        
            for x in range(int(conversations.qsize()/2)):
                messages.append({"role": "user", "content": conversations.queue[2*x]})
                messages.append({"role": "assistant", "content": conversations.queue[2*x + 1]})
        
        
            messages.append({"role": "user", "content": openapi_prompt})
        
            #print(messages, flush=True)

            response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            #messages=[{"role": "user", "content": openapi_prompt}],
            messages=messages,
            max_tokens=200,
            n=1,
            stop=None,
            temperature=0.7,
            timeout=20
            )
        
            #reply = response.choices[0].text.strip()
            reply = response.choices[0].message.content.strip()
        
            #print(response, flush=True)
            print(reply, flush=True)
        
            #send_msg(res['entry'][0]['changes'][0]['value']['messages'][0]['from'], res['entry'][0]['changes'][0]['value']['messages'][0]['text']['body'])
            if(len(reply) == 0):
                send_msg(res['entry'][0]['changes'][0]['value']['messages'][0]['from'], "Sorry I don't have an answer")
            else:
                send_msg(res['entry'][0]['changes'][0]['value']['messages'][0]['from'], reply)  

            #rebuild converstions
            conversations.put(openapi_prompt)
            conversations.put(reply)

            if(conversations.qsize() >= MAX_QUEUE_SIZE):
                conversations.get()
                conversations.get()

    except:
        pass

    return '200 OK HTTPS.'
 
if __name__ == "__main__":
   app.run(debug=True, host='127.0.0.1', port=5020) #, ssl_context='adhoc'



####Message Sample###########
#####Outgoing 
#<Request 'http://5f88-64-26-135-6.ngrok.io/receive_msg' [POST]>
#{'object': 'whatsapp_business_account', 'entry': [{'id': '118417864508500', 'changes': [{'value': {'messaging_product': 'whatsapp', 'metadata': {'display_phone_number': '15550676851', 'phone_number_id': '120622404311891'}, 'statuses': [{'id': 'wamid.HBgLMTYxMzI2NTIyODYVAgARGBJCMUJFMkQwMTk2QUZDMUU4NTQA', 'status': 'sent', 'timestamp': '1679283074', 'recipient_id': '16132652286', 'conversation': {'id': '0e86bb622433b564e03ecdf918bb58c2', 'expiration_timestamp': '1679359440', 'origin': {'type': 'business_initiated'}}, 'pricing': {'billable': True, 'pricing_model': 'CBP', 'category': 'business_initiated'}}]}, 'field': 'messages'}]}]}
#127.0.0.1 - - [20/Mar/2023 03:31:14] "POST /receive_msg HTTP/1.1" 200 -
#<Request 'http://5f88-64-26-135-6.ngrok.io/receive_msg' [POST]>
#{'object': 'whatsapp_business_account', 'entry': [{'id': '118417864508500', 'changes': [{'value': {'messaging_product': 'whatsapp', 'metadata': {'display_phone_number': '15550676851', 'phone_number_id': '120622404311891'}, 'statuses': [{'id': 'wamid.HBgLMTYxMzI2NTIyODYVAgARGBJCMUJFMkQwMTk2QUZDMUU4NTQA', 'status': 'delivered', 'timestamp': '1679283074', 'recipient_id': '16132652286', 'conversation': {'id': '0e86bb622433b564e03ecdf918bb58c2', 'origin': {'type': 'business_initiated'}}, 'pricing': {'billable': True, 'pricing_model': 'CBP', 'category': 'business_initiated'}}]}, 'field': 'messages'}]}]}
#127.0.0.1 - - [20/Mar/2023 03:31:15] "POST /receive_msg HTTP/1.1" 200 -
#<Request 'http://5f88-64-26-135-6.ngrok.io/receive_msg' [POST]>
#{'object': 'whatsapp_business_account', 'entry': [{'id': '118417864508500', 'changes': [{'value': {'messaging_product': 'whatsapp', 'metadata': {'display_phone_number': '15550676851', 'phone_number_id': '120622404311891'}, 'statuses': [{'id': 'wamid.HBgLMTYxMzI2NTIyODYVAgARGBJCMUJFMkQwMTk2QUZDMUU4NTQA', 'status': 'read', 'timestamp': '1679283081', 'recipient_id': '16132652286'}]}, 'field': 'messages'}]}]}
#127.0.0.1 - - [20/Mar/2023 03:31:22] "POST /receive_msg HTTP/1.1" 200 -


#inbound text

#{'object': 'whatsapp_business_account', 
# 'entry': [{'id': '118417864508500', 
#            'changes': [
#                    {'value': 
#                        {'messaging_product': 'whatsapp', 
#                        'metadata': {'display_phone_number': '15550676851', 'phone_number_id': '120622404311891'}, 
#                        'contacts': [{'profile': {'name': 'Yonge'}, 'wa_id': '16132652286'}], 
#                        'messages': [{'from': '16132652286', 
#                                        'id': 'wamid.HBgLMTYxMzI2NTIyODYVAgASGBQzQUNFNDgwQzJFQTExM0VERjQ1OQA=', 
#                                        'timestamp': '1679283525', 
#                                        'text': {'body': 'Test text from Yonge'}, 
#                                        'type': 'text'
#                                    }]
#                        }, 
#                     'field': 'messages'
#                    }
#                    ]
#            }
#        ]
#}
#127.0.0.1 - - [20/Mar/2023 03:38:46] "POST /receive_msg HTTP/1.1" 200 -