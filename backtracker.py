#!/usr/bin/python
# -*- coding:utf-8 -*-
'''
Created on 10 мая 2017 г.

@author: info@lineris.ru
'''

import os, time, sys
from datetime import datetime
from telegram.ext import Updater         
from telegram.ext import CommandHandler
from telegram import error
import ConfigParser  
from signal import SIGTERM


HandleMessage = "Сканирование папок резервного копирования на сервере %s в папке %s завершено %s.\r\n"
NoNewFiles = "Новых файлов в сканируемых папках не обнаружено."
NewFiles = "Обнаружено %s новых файлов в сканируемых папках:\r\n"
BadToken = '''В конфигурационном файле указан некорректный токен.
Создайте своего Telegram бота и укажите правильный token в конфигурационном файле.
Подробности https://core.telegram.org/bots
'''
tChatIDinit = '''В конфигурационном файле не указан ChatID для отправки сообщений о результатах сканирования.
Отправьте своему боту команду /start для автоматического определения ChatID.
'''
tChatIDdone = "Конфигурация успешно сохранена. Запустите утилиту повторно для сканирования папок"
tChatID = '''Ваш ChatID: %s зарегистрирован и автоматически записан в конфигурационный файл.
Дождитесь завершения выполнения утилиты и запустите ее повторно для сканирования папок.
''' 

def BuildFilesList(FilesList, FilePath, FileAge):
    for i in  os.listdir(FilePath):
        if os.path.isfile(os.path.join(FilePath, i)):
            if time.time() - os.path.getctime(os.path.join(FilePath, i)) <  FileAge:
                FilesList.append(os.path.join(FilePath, i))
        elif os.path.isdir(os.path.join(FilePath, i)):
            BuildFilesList(FilesList, os.path.join(FilePath, i), FileAge) 


    
def Scan(settings, updater):
    FilesList = []
    BuildFilesList(FilesList, settings.get('Scan', 'Path'), settings.getint('Scan', 'Hours')*60*60)
    tMessage = HandleMessage  % (os.uname()[1],settings.get('Scan', 'Path'),datetime.today())
    if len(FilesList):
        if bool(settings.getboolean('Telegram', 'FailOnly')):
            return
        else:
            tMessage = tMessage + NewFiles % len(FilesList)  
            for i in FilesList:
                tMessage = tMessage + i +"\r\n" 
    else:
        tMessage = tMessage + NoNewFiles
    updater.bot.sendMessage(chat_id=settings.get('Telegram', 'ChatID'), text=tMessage)


def start(bot, update):
    ChatID = str(update.message.chat_id)
    bot.sendMessage(chat_id=update.message.chat_id, text=tChatID % ChatID)
    settings.set('Telegram', 'ChatID', ChatID)
    os.kill(os.getpid(), SIGTERM)

            
if __name__ == '__main__':
    settings = ConfigParser.ConfigParser()
    settings.read('backtracker.conf')
    
    try:
        updater = Updater(settings.get('Telegram', 'Token'))
    except error.InvalidToken:
        print BadToken   
        sys.exit()
    
    try:
        settings.get('Telegram', 'ChatID')
    except ConfigParser.NoOptionError:
        print tChatIDinit
        start_handler = CommandHandler('start', start)
        updater.dispatcher.add_handler(start_handler)
        #os.kill(os.getpid(), SIGTERM) 
        updater.start_polling()
        updater.idle()
        #settings.write('backtracker.conf')
        with open('backtracker.conf', 'wb') as configfile:
            settings.write(configfile)
        print tChatIDdone
        updater.stop()  
        sys.exit()      
    else:
        Scan(settings, updater)
        