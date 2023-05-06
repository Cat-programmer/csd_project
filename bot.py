import logging
import random
import time
import re
import json
import os
import poe
import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
from api import generate as kandinsky # api поменяйте на название файла `api.py` без `.py` в конце
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode
import requests
from bs4 import BeautifulSoup
import gpt4free
from gpt4free import Provider, quora, forefront

from threading import Thread
from flask import Flask

logging.basicConfig(level=logging.INFO)

API_TOKEN = '6234799559:AAHzPPQMZ9nYJQK7J-AHJlSJB5piv8xWUF4'

msgListFileName = "data.json"
userListFileName = "users.json"

msgInterval = 120

keys = ["ZVpkBDnV6UWNgaUTbJGDcg%3D%3D",
           "gf140jGZu99iPd5Ks90-eQ%3D%3D",
           "r76ZAmNq5CJ4uXOzOVpPKw%3D%3D",
           "Luvn6HxS7L8Z49uREGv99g%3D%3D",
           "7Yv65KDYli6tNqOBdgqIGg%3D%3D",
           "DXCRtHOUOk4kh5UByuz88A%3D%3D",
           "36dNlliSvX4AVvdwnXmVIA%3D%3D",
           "T3Xr1SxaSFXkyNJ9Zb8UpA%3D%3D",
           "1HUbT7yrc6_cRtda909JyA%3D%3D",
           "Q5xIpCCmCsVoCmV23vf-hw%3D%3D"]

clients = []


def serv():
    app = Flask('dev')

    @app.route('/')
    def helloworld():
        return "Hello, world"

    app.run(port=7860)

X = Thread(target=serv)
X.daemon = True
X.start()

def load_key(i):
    #print(i)
    try:
        client = poe.Client(keys[i])
        print(f"Key {keys[i]} loaded.")
        return client
    except Exception as e:
        print(f"Failed loading key {keys[i]}.")
        return None
    




usedAI = "csdproj"
usedAcc = 0
chosenAcc = 0

# usage forefront
#token = forefront.Account.create(logging=False)
#response = gpt4free.Completion.create(
#    Provider.ForeFront, prompt='Hi', model='gpt-4', token=token
#)
#print(response)


# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
Bot.set_current(bot)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("Привет. Я бот на нейросети Claude. Она быстрее, чем ChatGPT, а в чём-то и умнее.")

@dp.message_handler(commands=['claude'])
async def claude(message: types.Message):
    print("Bot called by /claude...")
    chosenAcc = choose_Acc(queues)
    queues[chosenAcc].append(message)

    lengths = [len(arr) for arr in queues]
    print(", ".join(map(str, lengths)))

@dp.message_handler(commands=['csd'])
async def csd(message: types.Message):
    print("Bot called by /csd...")
    chosenAcc = choose_Acc(queues)
    queues[chosenAcc].append(message)
    lengths = [len(arr) for arr in queues]
    print(", ".join(map(str, lengths)))

"""
@dp.message_handler()
async def echo(message: types.Message):
    chosenAcc = choose_Acc(queues)
    print(chosenAcc)
    queues[chosenAcc].append(message)
    lengths = [len(arr) for arr in queues]
    print(", ".join(map(str, lengths)))
"""

async def manageQueue(Acc):
    if ((datetime.now()-lastMessageTime[Acc]).total_seconds()>msgInterval) & (len(queues[Acc])>0):
        await msg_process(queues[Acc][0], Acc)
        queues[Acc].pop(0)
        lengths = [len(arr) for arr in queues]
        print(", ".join(map(str, lengths)))
    

async def task():
    while True:
        for i in range(clientsCount):
            await manageQueue(i)
        await asyncio.sleep(0.1) # wait for 0.1 seconds


async def msg_process(message: types.Message, usedAcc):
    #answer = await gpt4_process(message)
    #print (f"{message.text} -> {answer}")
    query = re.sub(r'/(csd |claude) ', '', message.text)
    print (query)
    try:
        answer = await claude_process(query, usedAcc)
        await message.reply(answer)
    except Exception as e:
        answer = "ERROR: Failed to give response."
        await message.reply("ERROR: Failed to give response.")
        print (f"ERROR: Failed to give response. Request: {message.text}")
    imgPrompts = find_and_remove_draw_strings(answer)
    #print(imgPrompts)
    
    #kandinsky ("Cat", './img/')
    #for prompt in imgPrompts:
    #    kandinsky (prompt, './img/')
    lastMessageTime[usedAcc] = datetime.now()
    #log_message(message, answer)  # Log the message
    #log_user(message.from_user)

async def claude_process(message, usedAcc):
    clients[usedAcc].send_chat_break(usedAI)
    answer = ""
    for chunk in clients[usedAcc].send_message(usedAI, message):
        #print(chunk["text_new"], end="", flush=True)
        answer+= chunk["text_new"]
    return answer

async def gpt4_process(message, token = None):
    # usage forefront
    print (f"New session... Prompt: {message}")
    token = forefront.Account.create(logging=False)
    answer = gpt4free.Completion.create(
        Provider.ForeFront, prompt=message, model='gpt-4', token=token
    )
    print(answer)
    return answer

async def fake_process(message: types.Message, usedAcc):
    print (f"Calling Claude with {message.text}")


def find_and_remove_draw_strings(big_string):
    draw_strings = []
    
    # Find all strings starting from >DRAW until \n
    draw_strings = re.findall(r'>DRAW.*\n', big_string)
    new_draw_strings = []
    for str in draw_strings:
        str = re.sub(r'>DRAW ', '', str)
        str = re.sub(r'\n', '', str)
        new_draw_strings.append(str)

    # Save the strings to a list and remove them from the big string
    big_string = re.sub(r'>DRAW.*\n', '', big_string)
    
    return new_draw_strings, big_string

def choose_Acc(queues):
    minI = 0
    minTime = float('inf')
    for i in range(clientsCount):
        if  len(queues[i])*msgInterval+max(0,msgInterval-(datetime.now()-lastMessageTime[i]).total_seconds())<minTime:
            minI = i
            minTime = len(queues[i])*msgInterval+max(0, msgInterval-(datetime.now()-lastMessageTime[i]).total_seconds())
            print(f"{len(queues[i])*msgInterval} {max(0, msgInterval-(datetime.now()-lastMessageTime[i]).total_seconds())}")
    return minI

def log_message(message: types.Message, answer):
    if os.path.isfile(msgListFileName):
        with open(msgListFileName, "r", encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = []

    message_data = {
        "username": message.from_user.username,
        "userid": message.from_id,
        "date": message.date.strftime("%Y-%m-%d %H:%M:%S"),
        "text": message.text,
        "answer": answer,
        "gener_time":(datetime.now()-message.date).total_seconds()
    }

    data.append(message_data)

    with open(msgListFileName, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def log_user(user: types.User):
    if os.path.isfile(userListFileName):
        with open(userListFileName, "r", encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = []

    if any(usr["userid"] == user.id for usr in data):
        pass
    else:
        user_data = {
            "name": user.full_name,
            "username": user.username,
            "userid": user.id,
        }

        data.append(user_data)

        with open(userListFileName, "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def get_latest_news_tass_ru():
    url = "https://tass.ru/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    soup_text = soup.prettify()
    #text2 = soup_text[247:247 + 1000]

    # Find the "title": "example title" pattern using regex
    pattern = re.compile(r'"title":"(.+?)"')
    titles = pattern.findall(soup_text)

     # Create an empty string to store the formatted titles
    formatted_titles = ""

    # Add each title followed by a newline character
    for title in titles[:10]:
        formatted_titles += title + "\n"+ "\n"

    return formatted_titles

async def send_messages():
    if os.path.isfile(userListFileName):
        with open(userListFileName, "r", encoding='utf-8') as f:
            data = json.load(f)
    for user in data:
        
        print (user['userid'])
        await bot.send_message(chat_id=user['userid'], text="Привет, я живой!")

async def on_start(dp):
    await send_messages()

async def main():
    # start the task as a background task
    asyncio.create_task(task())

if __name__ == '__main__':
    with ThreadPoolExecutor() as executor:
        clients = list(executor.map(load_key, range(len(keys))))
    clients = [client for client in clients if client is not None]

    clientsCount = len(clients)
    queues = [[] for i in range(clientsCount)]
    lastMessageTime = [datetime.now()-timedelta(seconds=msgInterval) for i in range(clientsCount)]
    
    print(clients[usedAcc].bot_names)
    print(f"Using {clientsCount} accounts.")
      # create a new event loop
    loop = asyncio.get_event_loop()
    # set the event loop as the default event loop for the main thread
    asyncio.set_event_loop(loop)
    # start the event loop
    loop.run_until_complete(main())
    # start the bot
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
    