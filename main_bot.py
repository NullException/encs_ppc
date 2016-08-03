#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Example Bot to show some of the functionality of the library
# This program is dedicated to the public domain under the CC0 license.

"""
This Bot uses the Updater class to handle the bot.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and the CLI-Loop is entered, where all text inputs are
inserted into the update queue for the bot to handle.
Usage:
Repeats messages with a delay.
Reply to last chat from the command line by typing "/reply <text>"
Type 'stop' on the command line to stop the bot.
"""

import telegram
from telegram import InlineQueryResultArticle
from telegram.ext import Updater
from telegram.ext import InlineQueryHandler
from telegram.ext import StringCommandHandler
from telegram.ext import StringRegexHandler
from telegram.ext import MessageHandler
from telegram.ext import CommandHandler
from telegram.ext import RegexHandler
from telegram.ext.dispatcher import run_async
from time import sleep
import logging

from datetime import datetime, timedelta, time

from settings_provider import SettingsProvider
from data_models import User
from data_models import ActionType
from data_models import EncsPPC_Action


#     {
#     "message_id": 286,
#     "date": 1461505329,
#     "entities": [
#         {
#             "type": "bot_command",
#             "length": 8
#         }
#     ],
#     "new_chat_title": "",
#     "text": "/checkIn TEST",
#     "from": {
#         "type": "",
#         "username": "nullexception",
#         "first_name": "Денис",
#         "last_name": "Поликашин",
#         "id": 42520899
#     },
#     "caption": "",
#     "chat": {
#         "type": "private",
#         "title": "",
#         "last_name": "Поликашин",
#         "username": "nullexception",
#         "id": 42520899,
#         "first_name": "Денис"
#     }
# }


# TODO
# выделить компоненты отвечающие за определенную бизнесслогику в отдельные сущности
# так чтобы эти сущности при необходимости дополгительных аргументов к запросу запросе
#   создавали новую клавиатуру так, что в кнопках лежит следующее:
#      /command arg_on_previous_step new_step_arg_variant
#  тогда роутер всегда будет перенаправлять команду в одину и туже функцию обработки, но
#  с новыми аргументами. Таким образом мы избавимся от необходимости хранить состояние
#  непосредственно в боте и добавим интерактивности в диалог, но
#  надо не переборщить  с глубиной веток запросов, иначе работа будет утомительна

# Enable Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)

# We use this var to save the last chat id, so we can reply to it
last_chat_id = 0


class CommandsKeys:
    start = 'start'
    check_in = 'i'
    check_out = 'o'
    cheked_time = 't'
    check_remove = 'r'
    esc = 'e'
    man = 'm'
    man_pool = [
        'm_' + x for x in [check_in, check_out, check_remove, cheked_time, esc]
    ]


class KeyboardFabric:
    check_in = telegram.KeyboardButton('/' + CommandsKeys.check_in)
    check_out = telegram.KeyboardButton('/' + CommandsKeys.check_out)
    start = telegram.KeyboardButton('/' + CommandsKeys.start)
    man = telegram.KeyboardButton('/' + CommandsKeys.man)
    man_pool = [telegram.KeyboardButton('/' + x)
                for x in CommandsKeys.man_pool]
    esc = telegram.KeyboardButton('/' + CommandsKeys.esc)
    check_remove = telegram.KeyboardButton('/' + CommandsKeys.check_remove)

    def buld_custom_keyboard(custom_keyboard):
        if custom_keyboard is None:
            custom_keyboard = []
        return telegram.ReplyKeyboardMarkup(custom_keyboard)

    def start_keyboard():
        custom_keyboard = [
            [KeyboardFabric.check_in, KeyboardFabric.check_out],
            [KeyboardFabric.check_remove, KeyboardFabric.man]
        ]
        return KeyboardFabric.buld_custom_keyboard(custom_keyboard)

    def man_keyboard():
        custom_keyboard = [
            KeyboardFabric.man_pool,
            [KeyboardFabric.esc]
        ]
        print(custom_keyboard)
        return KeyboardFabric.buld_custom_keyboard(custom_keyboard)

    def build_check_in_keyboard():
        custom_keyboard = [
            [KeyboardFabric.check_in],
            [KeyboardFabric.check_remove, KeyboardFabric.esc]
        ]
        return KeyboardFabric.buld_custom_keyboard(custom_keyboard)

    def build_check_out_keyboard():
        custom_keyboard = [
            [KeyboardFabric.check_out],
            [KeyboardFabric.check_remove, KeyboardFabric.esc]
        ]
        return KeyboardFabric.buld_custom_keyboard(custom_keyboard)


settings_provider = SettingsProvider('settings.json')
token = settings_provider.bot_secret_token()


def get_or_create_user(message):
    message_from = message.from_user
    user, is_create = User.get_or_create(
        uid=message_from.id,
        username=message_from.username,
        last_name=message_from.last_name,
        first_name=message_from.first_name
    )
    return user


# Define a few (command) handler callback functions. These usually take the
# two arguments bot and update. Error handlers also receive the raised
# TelegramError object in error.
def start(bot, update):
    """ Answer in Telegram """
    print('start cmd')
    print(update)
    message = update.message
    user = get_or_create_user(message)
    text = "Hi " + user.username + "!"
    bot.sendMessage(
        chat_id=message.chat_id,
        text=text,
        reply_markup=KeyboardFabric.start_keyboard()
        # reply_markup=KeyboardFabric.build_check_in_keyboard()
    )


def man(bot, update):
    message = update.message
    command = message.text
    man_text = 'command info: /'
    command = command[len(CommandsKeys.man) + 2:]
    print(command)
    if command == CommandsKeys.start:
        man_text += CommandsKeys.start
        man_text += '\application start'
    elif command == CommandsKeys.esc:
        man_text += CommandsKeys.esc
        man_text += '\nshow start keyboard'
    elif command == CommandsKeys.check_in:
        man_text += CommandsKeys.check_in
        man_text += '\nargs: [date [hour [minute]]]'
        man_text += '\ndate: number or char "t"(oday) or char "y"(esterday)'
        man_text += '\nhour: number'
        man_text += '\nminute: number'
        man_text += '\nusage:\n/i - save now date and time'
        man_text += '\nusage:\n/i y - save yesterday date and now time'
        man_text += '\nusage:\n/i y 12 50 - save yesterday date, 12 hour 50 minute'
        man_text += '\nusage:\n/i t 12 50 - save today date, 12 hour 50 minute'
    elif command == CommandsKeys.check_out:
        man_text += CommandsKeys.check_out
        man_text += '\nargs: [date [hour [minute]]]'
        man_text += '\ndate: number or char "t"(oday) or char "y"(esterday)'
        man_text += '\nhour: number'
        man_text += '\nminute: number'
        man_text += '\nusage:\n/o - save now date and time'
        man_text += '\nusage:\n/o y - save yesterday date and now time'
        man_text += '\nusage:\n/o y 12 50 - save yesterday date, 12 hour 50 minute'
        man_text += '\nusage:\n/o t 12 50 - save today date, 12 hour 50 minute'
    elif command == CommandsKeys.check_remove:
        man_text += CommandsKeys.check_remove
        man_text += '\nargs: id or specific_key'
        man_text += '\nid: check info id'
        man_text += '\nspecific key: char "t"(oday) or "y"(esterday) or "m"(onth) or "a"(ll)'
        man_text += '\nusage:\n/r 12 - remove from database user check info with id 12'
        man_text += '\nusage:\n/r m - remove from database user check info for this month'
    elif command == CommandsKeys.man:
        man_text += CommandsKeys.man
        man_text += '\nopen comands info'
    else:
        command = 'select any comand'
    if command:
        bot.sendMessage(
            chat_id=message.chat_id,
            text=man_text,
            reply_markup=KeyboardFabric.man_keyboard()
        )


def esc(bot, update):
    message = update.message
    bot.sendMessage(
        chat_id=message.chat_id,
        text='return to main menu',
        reply_markup=KeyboardFabric.start_keyboard()
    )


def check_in_check_out_date(message):
    good_arg = True
    args = message.text[len(CommandsKeys.check_in) + 2:]
    print(args)
    arglist = args.split(' ')
    day_arg, hour_arg, minute_arg = '', '', ''
    if len(arglist) >= 1:
        day_arg = arglist[0]
    if len(arglist) >= 2:
        hour_arg = arglist[1]
    if len(arglist) == 3:
        minute_arg = arglist[2]

    date = datetime.today()
    print(date)
    if day_arg:
        if day_arg == 't':
            pass
        elif day_arg == 'y':
            delta = timedelta(days=1)
            date = date - delta
        elif day_arg.isdigit():
            x = int(day_arg)
            if x > 0:
                date = date.replace(day=x)
                print(date)
            else:
                good_arg = False
                return date, good_arg
        else:
            good_arg = False
            return date, good_arg
        hour = date.time().hour
        minute = date.time().minute
        if hour_arg:
            hour = int(hour_arg)
            if minute_arg:
                minute = int(minute_arg)
            else:
                minute = 0
        t = time(hour, minute)
        date = datetime.combine(date, t)
    print(date, type(date))
    return date, good_arg


def check_in(bot, update):
    """ Answer in Telegram """
    print('check_in cmd')
    message = update.message
    print(message)

    date, good_arg = check_in_check_out_date(message)
    if good_arg is False:
        bot.sendMessage(
            update.message.chat_id,
            text='error args',
            reply_markup=KeyboardFabric.build_check_in_keyboard()
        )
        return
    any_user = get_or_create_user(message)

    action = EncsPPC_Action()
    action.action, isCreate = ActionType.get_or_create(
        description=CommandsKeys.check_in)
    action.user = any_user
    action.created_date = date
    action.save()

    text = 'Your check_in at: ' + str(action.created_date)
    text += '\naction id: ' + str(action.id)
    bot.sendMessage(
        update.message.chat_id,
        text=text,
        reply_markup=KeyboardFabric.build_check_out_keyboard()
    )


def check_out(bot, update):
    """ Answer in Telegram """
    print('check_out cmd')
    message = update.message
    print(message)

    date, good_arg = check_in_check_out_date(message)
    if good_arg is False:
        bot.sendMessage(
            update.message.chat_id,
            text='error args',
            reply_markup=KeyboardFabric.build_check_out_keyboard()
        )
        return
    any_user = get_or_create_user(message)

    action = EncsPPC_Action()
    action.action, isCreate = ActionType.get_or_create(
        description=CommandsKeys.check_out)
    action.user = any_user
    action.created_date = date
    action.save()

    text = 'Your check_out at: ' + str(action.created_date)
    text += '\naction id: ' + str(action.id)
    bot.sendMessage(
        update.message.chat_id,
        text=text,
        reply_markup=KeyboardFabric.build_check_in_keyboard()
    )


def checked_time(bot, update):
    bot.sendMessage(
        update.message.chat_id,
        text='TODO',
    )


def check_remove(bot, update):
    bot.sendMessage(
        update.message.chat_id,
        text='TODO',
    )


def any_message(bot, update):
    """ Print to console """
    print('any_message', update)
    # Save last chat_id to use in reply handler
    global last_chat_id
    last_chat_id = update.message.chat_id

    logger.info("New message\nFrom: %s\nchat_id: %d\nText: %s" %
                (update.message.from_user,
                 update.message.chat_id,
                 update.message.text))


@run_async
def message(bot, update):
    """
    Example for an asynchronous handler. It's not guaranteed that replies will
    be in order when using @run_async. Also, you have to include **kwargs in
    your parameter list. The kwargs contain all optional parameters that are
    """

    sleep(2)  # IO-heavy operation here
    bot.sendMessage(update.message.chat_id, text='Echo: %s' %
                                                 update.message.text)


# These handlers are for updates of type str. We use them to react to inputs
# on the command line interface
def cli_reply(bot, update, args):
    """
    For any update of type telegram.Update or str that contains a command, you
    can get the argument list by appending args to the function parameters.
    Here, we reply to the last active chat with the text after the command.
    """
    if last_chat_id is not 0:
        bot.sendMessage(chat_id=last_chat_id, text=' '.join(args))


def cli_noncommand(bot, update, update_queue):
    """
    You can also get the update queue as an argument in any handler by
    appending it to the argument list. Be careful with this though.
    Here, we put the input string back into the queue, but as a command.
    To learn more about those optional handler parameters, read the
    documentation of the Handler classes.
    """
    update_queue.put('/%s' % update)


def error(bot, update, error):
    """ Print error to console """
    logger.warn('Update %s caused error %s' % (update, error))


def inline_caps(bot, update):
    query = bot.update.inline_query.query
    results = list()
    results.append(
        InlineQueryResultArticle(query.upper(), 'Caps', query.upper()))
    bot.answerInlineQuery(update.inline_query.id, results)


def main():
    print(token)
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(token, workers=10)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    inline_caps_handler = InlineQueryHandler(inline_caps)
    # This is how we add handlers for Telegram messages
    dp.addHandler(inline_caps_handler)
    dp.addHandler(CommandHandler(CommandsKeys.start, start))
    dp.addHandler(CommandHandler(CommandsKeys.check_in, check_in))
    dp.addHandler(CommandHandler(CommandsKeys.check_out, check_out))
    dp.addHandler(CommandHandler(CommandsKeys.man, man))
    dp.addHandler(CommandHandler(CommandsKeys.check_remove, check_remove))
    dp.addHandler(CommandHandler(CommandsKeys.cheked_time, checked_time))
    dp.addHandler(CommandHandler(CommandsKeys.esc, esc))
    [dp.addHandler(CommandHandler(x, man)) for x in CommandsKeys.man_pool]

    # Message handlers only receive updates that don't contain commands
    # dp.addHandler(MessageHandler([filters.TEXT], message))
    # Regex handlers will receive all updates on which their regex matches,
    # but we have to add it in a separate group, since in one group,
    # only one handler will be executed
    # dp.addHandler(RegexHandler('.*', any_message), group='log')

    # String handlers work pretty much the same. Note that we have to tell
    # the handler to pass the args or update_queue parameter
    # dp.addHandler(StringCommandHandler('reply', cli_reply, pass_args=True))
    dp.addHandler(StringRegexHandler(r'/.*', cli_noncommand,
                                     pass_update_queue=True))

    # All TelegramErrors are caught for you and delivered to the error
    # handler(s). Other types of Errors are not caught.
    dp.addErrorHandler(error)

    # Start the Bot and store the update Queue, so we can insert updates
    update_queue = updater.start_polling(timeout=10)

    '''
    # Alternatively, run with webhook:
    update_queue = updater.start_webhook('0.0.0.0',
                                         443,
                                         url_path=token,
                                         cert='cert.pem',
                                         key='key.key',
                                         webhook_url='https://example.com/%s'
                                             % token)
    # Or, if SSL is handled by a reverse proxy, the webhook URL is already set
    # and the reverse proxy is configured to deliver directly to port 6000:
    update_queue = updater.start_webhook('0.0.0.0', 6000)
    '''

    # Start CLI-Loop
    while True:
        try:
            text = raw_input()
        except NameError:
            text = input()

        # Gracefully stop the event handler
        if text == 'stop':
            updater.stop()
            break

        # else, put the text into the update queue to be handled by our
        # handlers
        elif len(text) > 0:
            update_queue.put(text)

if __name__ == '__main__':
    main()
