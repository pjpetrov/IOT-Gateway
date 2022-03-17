#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import logging

from database import Database

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import MessageHandler, Filters, CallbackQueryHandler
from telegram.ext import CommandHandler
from telegram.ext import Updater
import redis
import datetime
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramBot(object):
    def __init__(self, updater, database, redisCache):
        self._cache = redisCache
        self._db = database
        self._commands = self._db.getCommands()
        self._users = self._db.getUsers()

        self._updater = updater
        self._dispatcher = updater.dispatcher
        self._request_markup = ReplyKeyboardMarkup((['/request_access']), resize_keyboard=True)

        self._dispatcher.add_handler(CommandHandler('addCmd', self.addCommand))
        self._dispatcher.add_handler(CommandHandler('rmCmd', self.rmCommand))
        self._dispatcher.add_handler(CommandHandler('start', self.startHandler))
        self._dispatcher.add_handler(CommandHandler('users', self.users))
        self._dispatcher.add_handler(CommandHandler('e', self.executeCommand))
        self._dispatcher.add_handler(CallbackQueryHandler(self.inlineQuery))

    def addCommand(self, update, context):
        args = update.message.text.split(' ')[1:]
        self._commands.add(args[0], args[1], args[2])

    def rmCommand(self, update, context):
        cmd = update.message.text.split(' ')[1]
        self._commands.remove(cmd)

    def getTelegramName(self, telegramUser):
        name = ""
        if telegramUser.first_name is not None:
            name += telegramUser.first_name + " "
        if telegramUser.last_name is not None:
            name += telegramUser.last_name
        return name

    def startHandler(self, update, context):
        userId = update.effective_user.id
        name = self.getTelegramName(update.effective_user)

        if self._users.exists(userId) and self._users.isBlacklisted(userId):
            # TODO check in the API if it is possible to ignore all the messages from the user.
            return

        if not self._users.hasAtLeastOneUser():
            # First user detected. Admin rights should be granted.
            self._users.add(userId, name, True)
            self.sendText(context, "You are the admin.", userId)
            return

        if self._users.exists(userId):
            self.sendText(context, 'Select command:', userId)
            return

        self._users.add(userId, name, False)

        self.editUserRights(update, context, userId, self._users.getName(userId))

    def sendText(self, context, message, userId):
        if not self._users.exists(userId):
            return

        markup = self.createReplyKeyboardMakrup(self._users.getCommands(userId))
        if self._users.isAdmin(userId):
            markup.append(['/users'])
        context.bot.send_message(chat_id=int(userId), text=message, reply_markup=ReplyKeyboardMarkup(markup))

    def createReplyKeyboardMakrup(self, commands):
        result = []

        commandsByGroup = self.groupCommands(commands)
        for group in commandsByGroup:
            groupCmds = []
            for cmd in commandsByGroup[group]:
                groupCmds.append('/e ' + cmd.getCommand()   )
            result.append(groupCmds)

        return result

    def editUserRights(self, update, context, userId, name):
        commandsString = self._users.getCommandsString(userId)
        context.bot.send_message(chat_id=self._users.getAdminId(), text="Access rights: " + name + " " + commandsString,
            reply_markup=InlineKeyboardMarkup(self.formatAccessCommands(userId)))

    def groupCommands(self, commands):
        commandsByGroup = {}
        for command in commands:
            group = command.getGroup()
            if group not in commandsByGroup:
                commandsByGroup[group] = []
            commandsByGroup[group].append(command)

        return commandsByGroup

    def formatAccessCommands(self, userId):
        commandsByGroup = self.groupCommands(self._commands.getAllCommands())

        result = [[],[]]

        for group in sorted(commandsByGroup):
            for command in commandsByGroup[group]:
                result[0].append(InlineKeyboardButton("Add " + command.getName(), callback_data = str(userId) + ",add_" + command.getCommand()))
                result[1].append(InlineKeyboardButton("Del " + command.getName(), callback_data = str(userId) + ",del_" + command.getCommand()))
        return result

    def inlineQuery(self, update, context):
        if not self._users.isAdmin(update.effective_user.id):
            return
        query = update.callback_query

        userIdStr, actionCommand = query.data.split(',')
        action, command = actionCommand.split('_', 1)

        userId = int(userIdStr)

        if action == 'add':
            self._users.addCommand(userId, command)

        elif action == 'del':
            self._users.removeCommand(userId, command)

        elif action == 'edit':
            self.editUserRights(update, context, userId, self._users.getName(userId))
            return

        query.edit_message_text(text="user {} : {}".format(userId, self._users.getName(userId)), 
            reply_markup=InlineKeyboardMarkup(self.formatAccessCommands(userId)))
        self.sendText(context, 'Select command: ', userId)

    def commandReport(self, update, context, title):
        self.sendText(context, self._users.getName(update.effective_user.id) + " executes: " + title, self._users.getAdminId())

    def users(self, update, context):
        if not self._users.isAdmin(update.effective_user.id):
            return
        self.usersMenu(update, context)

    def validateAccess(self, userId, cmdString):
        if not self._users.exists(userId) or self._users.isBlacklisted(userId):
            return

        commands = self._users.getCommands(userId)
        for command in commands:
            if command.getCommand() == cmdString:
                return True
        return False

    def executeCommand(self, update, context):
        cmdString = context.args[0]
        if not self.validateAccess(update.effective_user.id, cmdString):
            return

        self._cache.setex(cmdString, datetime.timedelta(seconds=10), value='toggle')

        self.commandReport(update, context, cmdString)

    def getUsers(self):
        result = []
        for userId in self._users.getUserIds():
            result.append([InlineKeyboardButton(self._users.getName(userId), callback_data = str(userId) + ",edit_")])

        return result

    def usersMenu(self, update, context):
        if not self._users.isAdmin(update.effective_user.id):
            return

        query = update.callback_query
        context.bot.send_message(chat_id = self._users.getAdminId(), text="Users: ", reply_markup=InlineKeyboardMarkup(self.getUsers()))

    def run(self):
        self._updater.start_polling()
        self._updater.idle()

if __name__ == "__main__":
    cache = redis.Redis(host='redis', port=6379)
    bot = TelegramBot(Updater(token=os.environ["TELEGRAM_TOKEN"], use_context=True), Database(), cache)
    bot.run()