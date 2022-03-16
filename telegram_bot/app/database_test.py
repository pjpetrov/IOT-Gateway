#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import unittest
import database
import mongomock

class TestUsersAndCommands(unittest.TestCase):
	def testUsers(self):
		db = mongomock.MongoClient().db

		commands = database.Commands(db)
		users = database.Users(db['users'], commands)

		users.add(1, 'Mincho', True)

		self.assertEqual(users.getAdminId(), 1)
		self.assertEqual(users.getUserIds(), [1])
		self.assertEqual(users.hasAtLeastOneUser(), True)
		self.assertEqual(users.exists(1), True)
		self.assertEqual(users.isAdmin(1), True)
		self.assertEqual(users.isBlacklisted(1), False)
		self.assertEqual(users.getCommands(1), [])

		commands.add('open_garage_1', 'Open Garage 1', 'G1')

		command = commands.getAllCommands()[0]
		self.assertEqual(command.getCommand(), 'open_garage_1')
		self.assertEqual(command.getName(), 'Open Garage 1')
		self.assertEqual(command.getGroup(), 'G1')
		self.assertEqual(users.getCommands(users.getAdminId()), commands.getAllCommands())

		users.add(2, 'Mincho2', True)
		self.assertEqual(users.getUserIds(), [1, 2])
		self.assertEqual(users.hasAtLeastOneUser(), True)
		self.assertEqual(users.exists(2), True)
		self.assertEqual(users.isAdmin(2), True)
		self.assertEqual(users.isBlacklisted(2), False)
		self.assertEqual(users.getCommands(2), commands.getAllCommands())

		users.add(3, 'Mincho3', False)
		self.assertEqual(users.getUserIds(), [1, 2, 3])
		self.assertEqual(users.hasAtLeastOneUser(), True)
		self.assertEqual(users.exists(3), True)
		self.assertEqual(users.isAdmin(3), False)
		self.assertEqual(users.isBlacklisted(3), False)
		self.assertEqual(users.getCommands(3), [])

		users.addCommand(3, 'open_garage_1')
		self.assertEqual(users.getCommands(3)[0], command)
		self.assertEqual(users.getCommandsString(3), 'open_garage_1 ')

		# Add invalid command
		users.addCommand(3, 'open_garage_3')
		self.assertEqual(len(users.getCommands(3)), 1)

		# Remove command from user
		users.removeCommand(3, 'open_garage_1')
		self.assertEqual(len(users.getCommands(3)), 0)

		# Remove command globally
		users.addCommand(3, 'open_garage_1')
		self.assertEqual(len(users.getCommands(3)), 1)

		users.add(4, 'Mincho4', False)
		users.addCommand(4, 'open_garage_1')
		self.assertEqual(len(users.getCommands(4)), 1)

		commands.remove('open_garage_1')
		self.assertEqual(len(users.getCommands(3)), 0)
		self.assertEqual(len(users.getCommands(4)), 0)
		# The admins should be unchanged
		self.assertEqual(users.getCommands(1), commands.getAllCommands())
		self.assertEqual(users.getCommands(2), commands.getAllCommands())

if __name__ == '__main__':
    unittest.main()
