import telegram_bot
import unittest
from telegram import User, Message, Chat, Update
from telegram.ext import Updater, CommandHandler
from telegram.utils.request import Request
import mongomock
import database
from unittest.mock import Mock, ANY

class TestDatabase(object):
    def __init__(self):
        self.db = mongomock.MongoClient().db
        self.commands = database.Commands(self.db)
        self.users = database.Users(self.db['users'], self.commands)

    def getCommands(self):
        return self.commands

    def getUsers(self):
        return self.users;


class TelegramBotTest(unittest.TestCase):
    def testStartAdmin(self):        
        redis = Mock()
        updater = Mock()
        botHandler = telegram_bot.TelegramBot(updater, TestDatabase(), redis)
        update = Mock()
        adminUser = User(id=1, first_name="FirstAdmin", is_bot=False)
        update.effective_user = adminUser
        update.message.text = '/start'
        context = Mock()
        botHandler.startHandler(update, context)
        context.bot.send_message.assert_called_with(chat_id=1, text="You are the admin.", reply_markup=ANY)
        self.assertEqual(botHandler._users.getName(1), "FirstAdmin ")

        context.reset_mock()

        update.message.text = '/addCmd garage_1 Garage1 g1'
        botHandler.addCommand(update, context)
        self.assertEqual(botHandler._commands.getAllCommands()[0].getName(), 'Garage1')

        normalUser = User(id=2, first_name="User", is_bot=False)
        update.effective_user = normalUser
        update.message.text = 'start'
        botHandler.startHandler(update, context)
        context.bot.send_message.assert_called_with(chat_id=1, text="Access rights: (User ) = ", reply_markup=ANY)

        context.reset_mock()

        update.effective_user = adminUser
        update.callback_query.data = '2,add_garage_1'
        botHandler.inlineQuery(update, context)
        self.assertEqual(len(botHandler._users.getCommands(2)), 1)
        context.bot.send_message.assert_called_with(chat_id=2, text="Select command: ", reply_markup=ANY)

        context.reset_mock()

        update.effective_user = normalUser
        context.args = ['garage_1']
        botHandler.executeCommand(update, context)
        redis.setex.assert_called_with('garage_1', ANY, value='toggle,telegram=2')

        update.effective_user = adminUser
        update.callback_query.data = '2,del_garage_1'
        botHandler.inlineQuery(update, context)
        self.assertEqual(len(botHandler._users.getCommands(2)), 0)
        context.bot.send_message.assert_called_with(chat_id=2, text="Select command: ", reply_markup=ANY)

        context.reset_mock()
        redis.reset_mock()

        update.effective_user = normalUser
        context.args = ['garage_1']
        botHandler.executeCommand(update, context)
        redis.setex.assert_not_called()

        update.effective_user = adminUser
        update.callback_query.data = '2,add_garage_1'
        botHandler.inlineQuery(update, context)
        self.assertEqual(len(botHandler._users.getCommands(2)), 1)
        context.bot.send_message.assert_called_with(chat_id=2, text="Select command: ", reply_markup=ANY)

        context.reset_mock()

        update.message.text = '/rmCmd garage_1 Garage1 g1'
        botHandler.rmCommand(update, context)
        self.assertEqual(len(botHandler._commands.getAllCommands()), 0)

        update.effective_user = normalUser
        context.args = ['garage_1']
        botHandler.executeCommand(update, context)
        redis.setex.assert_not_called()
        redis.reset_mock()

        update.effective_user = adminUser
        botHandler.users(update, context)
        context.bot.send_message.assert_called_with(chat_id=1, text="Users: ", reply_markup=ANY)
        context.reset_mock()
        update.callback_query.data = '1,edit_'
        botHandler.inlineQuery(update, context)
        context.bot.send_message.assert_called_with(chat_id=1, text="Access rights: (FirstAdmin ) = ADMIN", reply_markup=ANY)

        val = Mock()
        val.decode = Mock(return_value='text:test')
        redis.get = Mock(return_value=val)
        botHandler.checkRedisMessages(None)
        updater.bot.send_message.assert_called_with(chat_id=ANY, text='test')


if __name__ == '__main__':
    unittest.main()
