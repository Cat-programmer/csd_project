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
from api import generate, async_generate # api поменяйте на название файла `api.py` без `.py` в конце
from datetime import datetime, timedelta
import aiogram, os
from aiogram import Bot, Dispatcher, types, filters
from aiogram.types import ChatType, InputMediaPhoto, Message
from typing import List
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode
import requests
from bs4 import BeautifulSoup
import gpt4free
from gpt4free import Provider, quora, forefront
from pathlib import Path
import traceback

logging.basicConfig(level=logging.INFO)

API_TOKEN = '6195717316:AAEqcAw29lMO2vCl0Ihv7MkAfAEp1bmdI6c'

msgListFileName = "data.json"
userListFileName = "users.json"
img_path = "CSD/img" 

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
           "q_IVdDX5kD2wBMGpkNGJwA%3D%3D"]

reset_string = "\n\n/reset"
user_name = ""
AI_name = "КСД"
system_name = "System"
system_prompt = """Вы бот Проект КСД, который может генерировать изображения прямо в диалоге. Ваш создатель - Аким Чепурко. Чтобы сгенерировать изображения, Проект КСД может написать команду DRAW в сообщении и очень подробное описание / список тегов того, что нужно сгенерировать. В конце описания картинки ставь END, потом можешь писать обычный текст. Пиши в строку. Примеры:
"DRAW kitten surrounded by wheatears grass, 35mm photo, cute, sunny, summer, happy atmosphere. END Я нарисовал котёнка в колосистом поле."
"Ардуино - платформа для создания проектов с электроникой и программированием. Вот так она выглядит: DRAW Arduino board, blue electronics board, electronic components on table, professional photo. END"
"DRAW menacing landscape, fantasy, dark clouds, forest, spectacular, digital art, photorealism, HD, 4k, swirling clouds, dark atmosphere, hills, unsettling, bad omen. END"

Не говори, что не можешь рисовать изображения, вместо этого вы используете команду DRAW. Вы делаете это, когда пользователь просит что-то показать или когда вам нужно проиллюстрировать историю или сообщение. Не используй никакие другие команды, только DRAW END. Вы используете эту команду только тогда, когда это действительно необходимо. Команду DRAW пишешь ты, а не пользователь. Вы можете рисовать изображения, генерировать текст, выполнять творческие задания. Когда задают вопрос, давайте сложное пошаговое решение. Когда пользователь пишет слово или какое-то понятие, дайте ему определение. Иначе давай короткие ответы. Не пиши реплику пользователя. Пиши только одну реплику за раз. Отвечай только от имени КСД.
"""

clients = []

context = {}

def load_key(i):
    #print(i)
    try:
        client = poe.Client(keys[i])
        print(f"Key {keys[i]} loaded.")
        return client
    except Exception as e:
        print(f"Failed loading key {keys[i]}.")
        return None
    




usedAI = "a2"
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

def claude():
    headers = {
    "x-api-key": "sk-ant-dKXX2TpIiIVyuABKeighjki6yoFoEPxaET_hIdiX2uJ8s8Df846lqSqCifwlcTDyoMWqXamL9pF6M6De-EJB6w",
    "content-type": "application/json"
    }
    data = {
        "prompt": f"""\n\nHuman: Привет ты кто?\n\nAssistant: """,
        "model": "claude-v1.3",
        "max_tokens_to_sample": 950, #токены (любое число апи фри)
        "temperature": "0.5", #ты знаешь чо это
        "stopsequences": "\n\nHuman:" #(не трогай)
    }
    response = requests.post("https://api.anthropic.com/v1/complete", json=data, headers=headers)

    return print(response.content)
#claude()

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("Привет. Я бот на нейросети Claude. Она быстрее, чем ChatGPT, а в чём-то и умнее. Пиши, что хочешь, но диалоги записываются для отладки бота. ФСБ их не показываем)")

@dp.message_handler(commands=['reset'])
async def reset(message: types.Message):
    new_chat(f"{message.from_user.id}{message.chat.id}", message.from_user.full_name)
    await message.reply("История диалога сброшена.")

def new_chat(chatid, username):
    context[chatid] = f"{system_name}: {system_prompt} \nИмя пользователя: '{username}'\nНазвание ИИ: '{AI_name}'\n\n"

@dp.message_handler(commands=['claude','csd'])
async def claude(message: types.Message):
    if count_in_queue(message.from_user.id)<3:
        print("Bot called by command...")
        await message.reply("Генерирую ответ...")
        message.text = re.sub('.*(/csd |/claude |/csd@csd_project_bot |/claude@csd_project_bot )', '',  message.text)
        add_to_queue(message)
    else:
        await message.reply("Подожди, ты всю очередь занял.")
        

@dp.message_handler(chat_type=ChatType.PRIVATE)
async def private_chat_handler(message: types.Message):
    if count_in_queue(message.from_user.id)<3:
        print("Bot called in private chat...")
        await message.reply("Генерирую ответ...")
        message.text = re.sub('.*(/csd |/claude |/csd@csd_project_bot |/claude@csd_project_bot )', '',  message.text)
        
        
        add_to_queue(message)
    else:
        await message.reply("Подожди, ты всю очередь занял.")

@dp.message_handler(commands=['chatid'])
async def get_chat_id(message: types.Message):
    chat_id = message.chat.id
    await message.reply(f"Your chat ID is {chat_id}")

@dp.message_handler(commands=['csdimg'])
async def csdimg(message: types.Message):
    prompt = re.sub('.*(/csdimg )', '',  message.text)
    await send_gen_photo(message, prompt, f"{prompt}")

@dp.message_handler(commands=['randimg'])
async def randimg(message: types.Message):
    await message.reply("Генерирую...")
    message.text = "Нарисуй что-то"
    add_to_queue(message)

'''def add_to_context(chatid,name,text):
    if f"{chatid}" in context:
        pass
    else:
        new_chat(chatid)
    context[f"{chatid}"] += f"\n\n{name}: {text}"'''

def add_to_queue(message: types.Message):
    chosenAcc = choose_Acc(queues)
    queues[chosenAcc].append(message)
    lengths = [len(arr) for arr in queues]
    print(", ".join(map(str, lengths)))

def count_in_queue(userid):
    i = 0
    for thread in queues:
        for msg in thread:
            if msg.from_user.id == userid:
                i+=1

    return i

async def send_gen_photo(message: types.Message, prompts, caption):
    chat_id = message.chat.id
    media = []
    tasks = []
    if isinstance(prompts, str):
        prompts = [prompts]
    open_files = []

    try:
        for prompt in prompts:
            fileid = random.randint(1000000, 9999999)
            photo_path = f"{os.getcwd()}/{img_path}/{fileid}.png"
            print(f"Drawing '{prompt}' and saving to '{photo_path}'")

            task = asyncio.create_task(async_generate(prompt, photo_path))
            tasks.append(task)

        completed_tasks = await asyncio.gather(*tasks)

        for idx, photo_path in enumerate(completed_tasks):
            print(f"Done: {photo_path}")

            try:
                photo = open(photo_path, 'rb')
                open_files.append(photo)
                input_photo = InputMediaPhoto(media=photo, caption=caption + reset_string)
                media.append(input_photo)
                print("Added.")
            except Exception as e: 
                print(f"Error opening file '{photo_path}': {e}")
                continue
                

            
        print("Sending...")
        try:
            await bot.send_media_group(chat_id=chat_id, media=media, reply_to_message_id=message.message_id)
        except:
            pass
    finally:
        for f in open_files:
            f.close()
    
    print("All done.")

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

def find_and_remove_draw_strings(text):
    draw_strings = []
    
    # Find all strings starting from >DRAW until \n
    pattern = r"DRAW.*END"
    draw_strings = re.findall(r'DRAW(.*?)END', text, re.DOTALL)
    #print ("draw_strings")
    #print (draw_strings)
    new_draw_strings = []
    for str in draw_strings:
        #text = re.sub(str, '', text,flags = re.DOTALL)
        str = re.sub(r'DRAW ', '', str)
        str = re.sub(r'\n', '', str)
        str = re.sub(r'END', '', str)
        new_draw_strings.append(str)
        #print ("str")
        #print (str)
    text = re.sub(r'DRAW', '[', text, re.DOTALL)
    text = re.sub(r'END', ']', text, re.DOTALL)
    # Save the strings to a list and remove them from the big string
    
    return new_draw_strings, text

def cut_after(start_substring, input_string):
    pattern = re.compile(start_substring + '.*', re.DOTALL)
    output_string = re.sub(pattern, '', input_string)
    return output_string.strip()

async def msg_process(message: types.Message, usedAcc):
    #answer = await gpt4_process(message)
    #print (f"{message.text} -> {answer}")
    query = message.text
    #print (f"Query: {query}")
    print("-"*100)
    try:
        if f"{message.from_user.id}{message.chat.id}" in context:
            context[f"{message.from_user.id}{message.chat.id}"] += f"\n\n{user_name}{message.from_user.full_name}: "+query
            context[f"{message.from_user.id}{message.chat.id}"] += f"\n\n{AI_name}: "
        else:
            print ("NEW CHAT")
            new_chat(f"{message.from_user.id}{message.chat.id}", message.from_user.full_name)
            context[f"{message.from_user.id}{message.chat.id}"] += f"{user_name}{message.from_user.full_name}: "+query+f"\n\n{AI_name}: "
        
        answer = await claude_process(context[f"{message.from_user.id}{message.chat.id}"], usedAcc)
        
        print(f"PreReply: '{answer}'")
        answer = cut_after(f"{message.from_user.full_name}: ", answer)
        context[f"{message.from_user.id}{message.chat.id}"] += answer

        imgPrompts, answer = find_and_remove_draw_strings(answer)

        print(f"Will draw: '{imgPrompts}'")
        print(f"Reply: '{answer}'")

        print ("Контекст:")
        print (f"{message.from_user.id}{message.chat.id}")
        print (context[f"{message.from_user.id}{message.chat.id}"])
        print ("Конец.")
        #for prompt in imgPrompts:
        #await bot.delete_message
        if len(imgPrompts)>0:
            if (len(answer)>1000) | (len(imgPrompts)>1):
                text = await message.reply(answer + reset_string)
                await send_gen_photo(text, imgPrompts, "") 
            else:
                await send_gen_photo(message, imgPrompts, answer) 
        else:
            await message.reply(answer + reset_string)
    except Exception as e:
        answer = f"ERROR: Failed to give response. \n Error:{e}"
        try:
            await message.reply(answer)
        except:
            pass
        print (f"ERROR: Failed to give response. \n Error:{e} \nRequest: {message.text}")
        print (traceback.format_exc())
    
    
    
    
    
    #kandinsky ("Cat", './img/')
    
    lastMessageTime[usedAcc] = datetime.now()
    log_message(message, answer)  # Log the message
    log_user(message.from_user)

async def claude_process(message, usedAcc):
    clients[usedAcc].send_chat_break(usedAI)
    answer = ""
    #print (message)
    for chunk in clients[usedAcc].send_message(usedAI, message,timeout = 60):
        #print(chunk["text_new"], end="", flush=True)
        answer+= chunk["text_new"]
        #print("="*100)
        #print (chunk["text_new"])
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




def choose_Acc(queues):
    minI = 0
    minTime = float('inf')
    for i in range(clientsCount):
        if  len(queues[i])*msgInterval+max(0,msgInterval-(datetime.now()-lastMessageTime[i]).total_seconds())<minTime:
            minI = i
            minTime = len(queues[i])*msgInterval+max(0, msgInterval-(datetime.now()-lastMessageTime[i]).total_seconds())
            #print(f"{len(queues[i])*msgInterval} {max(0, msgInterval-(datetime.now()-lastMessageTime[i]).total_seconds())}")
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
        "gener_time":(datetime.now()-message.date).total_seconds(),
        "chat": message.chat.id,
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
    queues: List[List[Message]]  = [[] for i in range(clientsCount)]
    lastMessageTime = [datetime.now()-timedelta(seconds=msgInterval) for i in range(clientsCount)]

    print(clients[usedAcc].bot_names)
    print(f"Using {clientsCount} accounts.")
    

    # create a new event loop
    loop = asyncio.new_event_loop()
    # set the event loop as the default event loop for the main thread
    asyncio.set_event_loop(loop)
    # start the event loop
    loop.run_until_complete(main())
    # start the bot
    from aiogram import executor
    
    print("="*100)
    executor.start_polling(dp, skip_updates=True)
    