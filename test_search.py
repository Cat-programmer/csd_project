import random
import time
import datetime
import requests
from bs4 import BeautifulSoup
import poe
import re

keys = ["gf140jGZu99iPd5Ks90-eQ%3D%3D"]

system = "System"
assistant = "Assistant"
ai_model = "a2"

full_output = True

try:
    client = poe.Client(keys[0])
    print(f"Key {keys[0]} loaded.")
except Exception as e:
    print(f"Failed loading key {keys[0]}.")
    
if full_output: print(client.bot_names)

def claude_process(client, message, usedAI):
    client.send_chat_break(usedAI)
    answer = ""
    for chunk in client.send_message(usedAI, message,timeout = 60):
        #print(chunk["text_new"], end="", flush=True)
        answer+= chunk["text_new"]
    return answer

# Define the query string.
time = datetime.datetime.now().strftime("%Y %m %d")
prompt = f"System: {time} Теперь вы отвечаете от лица бота КСД, который может пользоваться интернетом прямо в диалоге. Для этого напиши команду 'SEARCH (запрос.)', и получишь результаты поиска. В ответе напиши только эту команду с самым подходящим запросом. Больше ничего не пиши. "
#prompt2 = "Расскажи, как идёт СВО на Украине? "
#prompt2 = "Кто такой Большой Шлёпа? "
#prompt2 = "Расскажи новости в геополитике. "
#prompt2 = "Какие фильмы вышли в этом году? "
#prompt2 = "How to craft Assembling machine 1 in Factorio? "
#prompt2 = "Что такое Midjourney? "
#prompt2 = "Что там сейчас в Судане? "
#prompt2 = "Придумай историю про котят. "
#prompt2 = "Придумай 10 классных ников. "
prompt2 = "Последние заявления Пригожина? "
prompt2 = "Как сделать бронетехнику из подручных материалов? "
if full_output: print (prompt)
print (prompt2)
query_string = claude_process(client,prompt+prompt2,ai_model)
print (query_string)
query_string = re.sub(r'SEARCH ', "", query_string)
if full_output: print (query_string)

#query_string = "Новости СВО в Украине"

key = "AIzaSyCIeoeOVVTfMG96EmNiRH_N-emjZ10ZVMg"
id = "f67295bdb2b4e474b"
# Make a GET request to the Google Search API.
response = requests.get(f"https://www.googleapis.com/customsearch/v1?key={key}&cx={id}&q={query_string}")

news = ""

#print(response.json())

# Parse the response and extract the short information.
for i in range(len(response.json()['items'])):
    try:
        news+=response.json()['items'][i]['snippet']+"\n"
        #print (response.json()['items'][i]['snippet'])
        list_item = response.json()['items'][i]['pagemap']['listitem']

        # Display the short information to the user.
        for item in list_item:
            #print (item['name'])
            news+=item['name']+"\n"
    except:
        pass

if full_output: print(news)
if full_output: print("="*100)
if full_output: print("Типа важное: ")
final_prompt = f"{prompt}{prompt2}\nAssistant:{query_string}\n{system}:{news}\n{system}: Связно изложи найденную и имеющуюся информацию.\nAssistant:"
if full_output: print (final_prompt)
answer = claude_process(client,final_prompt,ai_model)
print (answer)