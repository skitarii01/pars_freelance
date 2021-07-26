import threading
import time

import requests
import telebot
from bs4 import BeautifulSoup
from telebot import types

TOKEN = ''
with open('TOKEN.txt') as fl:
    for i in fl:
        TOKEN = i
        break
bot = telebot.TeleBot(TOKEN)

DANGEON_ID = 450543987


def get_descr(id):
    descr = []
    classq = 'task__description'

    id = '/tasks/' + id
    resp = requests.get('https://freelance.habr.com' + id)
    soup = BeautifulSoup(resp.text, 'lxml')

    aq = soup.find_all('div')

    for i in aq:
        if i.has_attr('class') and i['class'][0] == classq:
            for k in i.descendants:
                if k.string != None and not ([k.string, 0] in descr or [k.string, 1] in descr):
                    if k.name == 'li':
                        descr.append([k.string, 1])
                    else:
                        descr.append([k.string, 0])
    s = ''
    for i in descr:
        if i[1] == 0:
            s += i[0] + '\n'
        elif i[1] == 1:
            s += '- ' + i[0] + '\n\n'
    return s


# hello there rq

def send_new(id, task):
    keyboard = types.InlineKeyboardMarkup()
    callback_button = types.InlineKeyboardButton(text="описание", callback_data="test")
    keyboard.add(callback_button)
    s = 'title: ' + task[1] + '\n\nprice: %s\n\nid: %s\n\n' % (task[2], task[0].split('/')[2])
    bot.send_message(int(id), s, reply_markup=keyboard)


def check_updates(id):
    with open('tags_users.txt') as fl:
        for i in fl:
            par = i.split()
            if par[0] == id:
                url = par[1]
    tasqs = []

    with open('tasks/' + id + '.txt') as fl:
        for i in fl:
            tasqs.append(i)
    resp = requests.get(url)
    sp = BeautifulSoup(resp.content, 'lxml')

    divs = sp.find_all('article')

    news = []
    for i in divs:
        if i.has_attr('class') and i['class'] == ['task', 'task_list']:
            ok = False
            for k in i.descendants:
                if k.name == 'a':
                    if (not (k['href'] + '\n' in tasqs)) and '/tasks/' in k['href']:
                        news.append([k['href'], k.string])
                        ok = True
                    elif '/tasks/' in k['href']:
                        ok = False
                elif k.name == 'span':
                    if k.has_attr('class') and (k['class'][0] == 'negotiated_price' or k['class'][0] == 'count') and ok:
                        for q in k.descendants:
                            if str(type(q)) == "<class 'bs4.element.NavigableString'>":
                                news[len(news) - 1].append(q.string)
                                break

    with open('tasks/' + id + '.txt', 'w') as fl:
        for i in tasqs:
            fl.write(i)
        for i in news:
            fl.write(i[0] + '\n')
    for i in news:
        send_new(id, i)
    return


def checker():
    c = 0
    ok = True
    while True:
        try:
            print('check: ' + str(c))
            with open('tags_users.txt') as fl:
                for i in fl:
                    check_updates(i.split()[0])
            time.sleep(20)
            c += 1
            ok = True
        except Exception:
            try:
                if not (ok):
                    bot.send_message(DANGEON_ID, 'со мной чтото не так')
                    ok = False
            except Exception:
                pass
            time.sleep(20)


main_thr = threading.Thread(target=checker)
main_thr.start()


def return_to_the_title(msg):
    time.sleep(90)
    keyboard = types.InlineKeyboardMarkup()
    callback_button = types.InlineKeyboardButton(text="описание", callback_data="test")
    keyboard.add(callback_button)
    bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id, text=msg.text,
                          reply_markup=keyboard)
    return


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        if call.message:
            if call.data == "test":
                # регулярку надо бы
                id = call.message.text.split('id: ')[1].split('\n')[0]
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text=call.message.text + '\n\ndescr: ' + get_descr(id))
                t1 = threading.Thread(target=return_to_the_title, args=[call.message])
                t1.start()
    except Exception:
        try:
            bot.send_message(DANGEON_ID, 'со мной чтото не так')
        except Exception:
            pass
        time.sleep(60 ** 6)


def inizialisation(msg):
    url = msg.text

    if "https://freelance.habr.com/tasks?" not in url:
        bot.send_message(msg.from_user.id, 'неверная ссылка')
        return
    try:
        resp = requests.get(url)
        sp = BeautifulSoup(resp.content, 'lxml')

        divs = sp.find_all('article')

        a = divs[0]
        data = []
        with open('tags_users.txt') as fl:
            for i in fl:
                data.append(i)
        data.append(str(msg.from_user.id) + ' ' + url + '\n')
        with open('tags_users.txt', 'w') as fl:
            for i in data:
                fl.write(i)
        f = open('tasks/%s.txt' % msg.from_user.id, 'w')
        f.close()
    except Exception:
        bot.send_message(msg.from_user.id, 'неверная ссылка')
        return


@bot.message_handler(commands=['check'])
def text_handler(msg):
    bot.send_message(msg.from_user.id, 'i am fine')
    print(msg.from_user.id)


@bot.message_handler(commands=['start'])
def text_handler(msg):
    ids = []
    tags = []
    with open('tags_users.txt') as fl:
        for i in fl:
            tags.append(int(i.split()[0]))
            ids.append(i.split()[1])

    if not (msg.from_user.id in tags):
        bot.send_message(msg.from_user.id,
                         text='пришлите ссылку с https://freelance.habr.com/tasks с выбранными тегами')
        bot.register_next_step_handler(msg, inizialisation)


while True:
    try:
        print('connecting')
        bot.polling()
    except Exception:
        print('smthg is wrong, reconnecting')
