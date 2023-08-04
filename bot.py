from telebot import TeleBot
import openai
import os
from dotenv import load_dotenv
from db import User
import pydub
from telebot import types
from telebot.types import Message

load_dotenv() # load variables in .env to the environment

resp_message = ["⚙️ Set Limit","🤍 Like"]

def message_markup(resp=resp_message):
    markup = types.InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(*[types.InlineKeyboardButton(i, callback_data=i) for i in resp ])
    return markup

API   = os.environ.get("OPENAI_API")
TOKEN = os.environ.get("TELEGRAMBOT_TOKEN")
GENE = os.environ.get("GENE")
WAIT = "◦◦◦"

users = {}

system = {"role": "system", "content": GENE}

openai.api_key = API

bot = TeleBot(TOKEN)

class GPT:

    def __init__(self,m) -> None:
        self.m = m

    def response(self):
        bot.send_message(self.m.chat.id,WAIT)
        bot.send_chat_action(self.m.chat.id,action='typing')
        req = {'role':'user','content':self.m.text}
        users[self.m.chat.id].messages.append(req)
        promt = users[self.m.chat.id].messages[-users[self.m.chat.id].limit:]
        promt.insert(0,system)
        mes = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages = promt
        )
        response = mes.choices[0].message.content
        bot.delete_message(chat_id=self.m.chat.id,message_id=self.m.message_id + 1)
        bot.send_message(self.m.chat.id,response,parse_mode='markdown',reply_markup=message_markup())
        users[self.m.chat.id].append(mes.choices[0].message)

@bot.message_handler(commands=['start'])
def start(m):
    if m.chat.id not in users : users[m.chat.id] = User(m.chat.id)
    bot.send_message(m.chat.id,WAIT)
    bot.send_chat_action(m.chat.id,action='typing')
    msg = openai.ChatCompletion.create(
        model = "gpt-3.5-turbo",
        messages = [system],
    )
    response = msg.choices[0].message.content
    bot.delete_message(m.chat.id,m.message_id + 1)
    bot.send_message(m.chat.id,response,parse_mode='markdown')
    users[m.chat.id].append(msg.choices[0].message)

@bot.message_handler(func=lambda message: True)
def text(m):
    if m.chat.id not in users : users[m.chat.id] = User(m.chat.id)
    GPT(m).response()
    
@bot.message_handler(content_types=['voice'])
def voice_processing(m):
    if m.chat.id not in users : users[m.chat.id] = User(m.chat.id)
    file_info = bot.get_file(m.voice.file_id)
    bot.send_chat_action(m.chat.id,action="record_audio")
    downloaded_file = bot.download_file(file_info.file_path)
    with open(f'voices/{m.chat.id}.ogg', 'wb') as new_file:
        new_file.write(downloaded_file)
    o = pydub.AudioSegment.from_ogg(f'voices/{m.chat.id}.ogg')
    o.export(f"voices/{m.chat.id}.mp3",format='mp3')
    audiofile = open(f"voices/{m.chat.id}.mp3","rb")
    transcript = openai.Audio.transcribe("whisper-1",audiofile).text
    m.message_id += 1
    m.text = transcript
    bot.send_message(m.chat.id,"Replying for : {}".format(transcript),parse_mode='markdown')
    GPT(m).response()

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    res_mes = []
    for i in call.message.json["reply_markup"]['inline_keyboard']: 
        for j in i : res_mes.append(j["text"])
    if call.data == resp_message[1]:
        res_mes[1] = "❤️ Liked"
        bot.edit_message_text(call.message.json['text'],call.from_user.id,call.message.id,reply_markup=message_markup(res_mes))
    elif call.data == "❤️ Liked":
        res_mes[1] = resp_message[1]
        bot.edit_message_text(call.message.json['text'],call.from_user.id,call.message.id,reply_markup=message_markup(res_mes))
    elif call.data == resp_message[0]:
        markup = types.ForceReply(selective=True)
        mes = bot.send_message(call.from_user.id,f"Hello! Please set the limit for chat size. This is the maximum number of most recent chat messages that will be response from this bot, and it should be between 1 and 10. For example, if you set the limit to 5, the bot response based on the 5 most recent messages. \nCurrent Limit : {users[call.from_user.id].limit}\nWhat limit would you like to set? (Please enter a number ranges from 1 to 100.)",reply_markup=markup)
        bot.register_next_step_handler(mes,answer)

def answer(m):
    try:
        limit = int(m.text)
        if limit > 0 and limit <= 10:
            users[m.chat.id].set_limit(limit)
            bot.send_message(m.chat.id,"Your limit has been updated successfully!")
        else:
            bot.send_message(m.chat.id,"Sorry! unable to set limit because limit should ranges between 1 to 10")
    except Exception as e:
        bot.send_message(m.chat.id,"Invalid Number!\nUnable to set limit")

# Run Telegram bot
# You can also use webhook like flask.
bot.polling()