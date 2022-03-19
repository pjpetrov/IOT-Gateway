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
    def setUp(self):
        self.redis = Mock()
        self.updater = Mock()
        self.botHandler = telegram_bot.TelegramBot(self.updater, TestDatabase(), self.redis)

    def testNoUser(self):
        update = Mock()
        context = Mock()

        adminUser = User(id=1, first_name="FirstAdmin", is_bot=False)

        update.effective_user = adminUser

        # No user in the DB. All commands should be inaccesible
        update.message.text = '/addCmd garage_1 Garage1 g1'
        self.botHandler.addCommand(update, context)
        self.assertEqual(len(self.botHandler._commands.getAllCommands()), 0)
        context.bot.send_message.assert_not_called()
        context.reset_mock()

        update.message.text = '/rmCmd garage_1 Garage1 g1'
        self.botHandler.rmCommand(update, context)
        self.assertEqual(len(self.botHandler._commands.getAllCommands()), 0)
        context.bot.send_message.assert_not_called()
        context.reset_mock()

        self.botHandler.users(update, context)
        context.bot.send_message.assert_not_called()
        context.reset_mock()

        update.message.text = '/e garage_1'
        self.botHandler.executeCommand(update, context)
        self.redis.setex.assert_not_called()
        context.reset_mock()

    def testNoAccess(self):
        update = Mock()
        context = Mock()

        adminUser = User(id=1, first_name="FirstAdmin", is_bot=False)

        update.effective_user = adminUser
        update.message.text = '/start'
        self.botHandler.startHandler(update, context)
        context.reset_mock()

        noAccessUser = User(id=2, first_name="NoAccess", is_bot=False)
        update.effective_user = noAccessUser

        # No user in the DB. All commands should be inaccesible
        update.message.text = '/addCmd garage_1 Garage1 g1'
        self.botHandler.addCommand(update, context)
        self.assertEqual(len(self.botHandler._commands.getAllCommands()), 0)
        context.bot.send_message.assert_not_called()
        context.reset_mock()

        update.message.text = '/rmCmd garage_1 Garage1 g1'
        self.botHandler.rmCommand(update, context)
        self.assertEqual(len(self.botHandler._commands.getAllCommands()), 0)
        context.bot.send_message.assert_not_called()
        context.reset_mock()

        self.botHandler.users(update, context)
        context.bot.send_message.assert_not_called()
        context.reset_mock()

        update.message.text = '/e garage_1'
        self.botHandler.executeCommand(update, context)
        self.redis.setex.assert_not_called()
        context.reset_mock()


    def testMainFlow(self):        
        update = Mock()
        context = Mock()

        adminUser = User(id=1, first_name="FirstAdmin", is_bot=False)

        update.effective_user = adminUser

        update.effective_user = adminUser
        update.message.text = '/start'
        self.botHandler.startHandler(update, context)
        context.bot.send_message.assert_called_with(chat_id=1, text="You are the admin.", reply_markup=ANY)
        self.assertEqual(self.botHandler._users.getName(1), "FirstAdmin ")

        context.reset_mock()

        update.message.text = '/addCmd garage_1 Garage1 g1'
        self.botHandler.addCommand(update, context)
        self.assertEqual(self.botHandler._commands.getAllCommands()[0].getName(), 'Garage1')

        normalUser = User(id=2, first_name="User", is_bot=False)
        update.effective_user = normalUser
        update.message.text = 'start'
        self.botHandler.startHandler(update, context)
        context.bot.send_message.assert_called_with(chat_id=1, text="Access rights: (User ) = ", reply_markup=ANY)

        context.reset_mock()

        update.effective_user = adminUser
        update.callback_query.data = '2,add_garage_1'
        self.botHandler.inlineQuery(update, context)
        self.assertEqual(len(self.botHandler._users.getCommands(2)), 1)
        context.bot.send_message.assert_called_with(chat_id=2, text="Select command: ", reply_markup=ANY)

        context.reset_mock()

        update.effective_user = normalUser
        update.message.text = '/e garage_1'
        self.botHandler.executeCommand(update, context)
        self.redis.setex.assert_called_with('garage_1', ANY, value='toggle,telegram=2')

        update.effective_user = adminUser
        update.callback_query.data = '2,del_garage_1'
        self.botHandler.inlineQuery(update, context)
        self.assertEqual(len(self.botHandler._users.getCommands(2)), 0)
        context.bot.send_message.assert_called_with(chat_id=2, text="Select command: ", reply_markup=ANY)

        context.reset_mock()
        self.redis.reset_mock()

        update.effective_user = normalUser
        update.message.text = '/e garage_1'
        self.botHandler.executeCommand(update, context)
        self.redis.setex.assert_not_called()

        update.effective_user = adminUser
        update.callback_query.data = '2,add_garage_1'
        self.botHandler.inlineQuery(update, context)
        self.assertEqual(len(self.botHandler._users.getCommands(2)), 1)
        context.bot.send_message.assert_called_with(chat_id=2, text="Select command: ", reply_markup=ANY)

        context.reset_mock()

        update.message.text = '/rmCmd garage_1 Garage1 g1'
        self.botHandler.rmCommand(update, context)
        self.assertEqual(len(self.botHandler._commands.getAllCommands()), 0)

        update.effective_user = normalUser
        update.message.text = '/e garage_1'
        self.botHandler.executeCommand(update, context)
        self.redis.setex.assert_not_called()
        self.redis.reset_mock()

        update.effective_user = adminUser
        self.botHandler.users(update, context)
        context.bot.send_message.assert_called_with(chat_id=1, text="Users: ", reply_markup=ANY)
        context.reset_mock()
        update.callback_query.data = '1,edit_'
        self.botHandler.inlineQuery(update, context)
        context.bot.send_message.assert_called_with(chat_id=1, text="Access rights: (FirstAdmin ) = ADMIN", reply_markup=ANY)

        val = Mock()
        val.decode = Mock(return_value='test')
        self.redis.get = Mock(return_value=val)
        self.botHandler.checkRedisMessages(None)
        self.updater.bot.send_message.assert_called_with(chat_id=ANY, text='test')


if __name__ == '__main__':
    unittest.main()
