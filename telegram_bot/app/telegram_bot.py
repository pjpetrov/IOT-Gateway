#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import logging

from database import Users, Commands, Database

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import MessageHandler, Filters, CallbackQueryHandler
from telegram.ext import CommandHandler
from telegram.ext import Updater

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)
logger = logging.getLogger(__name__)



class TelegramBot(object):
	def __init__(self):
		self._commands = Commands()
		self._users = Users()
		self._updater = Updater(token='TODO ENVVAR!', use_context=True)
		self._dispatcher = updater.dispatcher
		self._request_markup = ReplyKeyboardMarkup((['/request_access']), resize_keyboard=True)

		dispatcher.add_handler(CommandHandler('start', self.startHandler))
		dispatcher.add_handler(CallbackQueryHandler(self.inlineQuery))

	def startHandler(self, update, context):
		userId = update.effective_user.id
		name = update.effective_user.first_name + " " + update.effective_user.last_name

		if self._users.isBlacklisted(userId):
			# TODO check in the API if it is possible to ignore all the messages from the user.
			return

		if not self._users.hasAtLeastOneUser():
			# First user detected. Admin rights should be granted.
			self._users.add(userId, name, True)
			return

		if self.users.exists(userId):
		    self.sendText(context, 'Select command:', userId)
			return

		self._users.add(userId, name, False)

        self.editUserRights(update, context, userId, self._users.getName(userId))

	def sendText(self, context, message, userId):
		if not self._users.exists(userId):
			return

	    markup = createReplyKeyboardMakrup(self._users.getCommands(userId))
	    context.bot.send_message(chat_id=int(userId), text=message, reply_markup=markup)

	def createReplyKeyboardMakrup(commands):
	    result = []

	    commandsByGroup = self.groupCommands(commands):
	    for group in commandsByGroup:
	    	result.append(commandsByGroup[group])

	    return ReplyKeyboardMarkup(result)

	def editUserRights(update, context, userId, name):
		commandsString = self._users.getCommandsString(userId)
	    context.bot.send_message(chat_id=self._users.getAdminId(), text="Access rights: " + name + " " + commandsString,
	        reply_markup=InlineKeyboardMarkup(self.formatAccessCommands(userId)))

	def groupCommands(self, commands):
		commandsByGroup = {}
		for command in self._commands.getCommands():
			group = command.getGroup()
			if group not in commandsByGroup:
				commandsByGroup[group] = []
			commandsByGroup[group].append(command)

		return commandsByGroup

	def formatAccessCommands(self, userId):
		commandsByGroup = self.groupCommands(self._commands.getCommands())

		result = [[],[]]

		for group in sorted(commandsByGroup):
			for command in commandsByGroup[group]:
				result[0][0].append(InlineKeyboardButton("Add " + command.getName(), callback_data = userId + ",add_" + command.getCmd()))
				result[0][1].append(InlineKeyboardButton("Del " + command.getName(), callback_data = userId + ",del_" + command.getCmd()))
	    return result

	def inlineQuery(self, update, context):
		if not self._users.isAdmin(update.effective_user.id):
			return
		query = update.callback_query

	    userId, actionCommand = query.data.split(',')
	    action, command = actionCommand.split('_')

	    if action == 'add':
	    	self._users.addCommand(userId, command)

	    elif action == 'del':
	    	self._users.removeCommand(userId, command)

	    elif action == 'edit':
	        self.editUserRights(update, context, userId, self._users.getName(userId))
	        return

	    query.edit_message_text(text="user {} : {}".format(userId, self._users.getName(userId)), 
	    	reply_markup=InlineKeyboardMarkup(self.formatAccessCommands(userId)))
	    self.sendText(context, 'Select command', user_id)

	def commandReport(self, update, context, title):
	    self.sendText(context, self._users.getName(update.effective_user.id) + " executes: " + title, self._users.getAdminId())

	def executeCommand(update, context):	
		cmdString = update.message.text
	    if not self.validateAccess(update.effective_user.id, cmdString):
	        return

	    if cmdString == "users" and self._users.isAdmin(update.effective_user.id):
	    	self.usersMenu()
	    	return

	    # TODO connect to the redis and push the command
	    commandReport(update, context, cmdString)

	def getUsers(self):
	    result = []
	    for userId in self._users.getUserIds():
	        result.append([InlineKeyboardButton(self._users.getName(userId), callback_data = userId + ",edit_")])

	    return result

	def usersMenu(self, update, context):
	    if self._users.isAdmin(update.effective_user.id):
	        return

	    query = update.callback_query
	    context.bot.sendMessage(chat_id = self._users.getAdminId(), text="Users: ", reply_markup=InlineKeyboardMarkup(getUsers()))

	def run(self):
		self._updater.start_polling()
		self._updater.idle()

if __name__ == "__main__":
	bot = TelegramBot()
	bot.run()