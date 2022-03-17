#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from pymongo import MongoClient, errors
import os

class Command(object):
    def __init__(self, data):
        self._data = data

    def __eq__(self, other):
        """Overrides the default implementation"""
        if not isinstance(other, Command):
            return False

        if self.getName() != other.getName():
            return False

        if self.getCommand() != other.getCommand():
            return False

        if self.getGroup() != other.getGroup():
            return False

        return True

    def getName(self):
        return self._data['name']

    def getCommand(self):
        return self._data['command']

    def getGroup(self):
        return self._data['group']

class Commands(object):
    def __init__(self, db):
        self._dbCommands = db['commands']
        self._dbUsers = db['users']
        # TODO add /users command when DB is empty

    def add(self, command, name, group):
        item = {
        'command': command,
        'name': name,
        'group': group
        }
        self._dbCommands.insert_one(item)

    def remove(self, command):
        self._dbCommands.delete_one({'command': command})
        self._dbUsers.update_many({}, {'$pull' : {'commands': command}})

    def getAllCommands(self):
        result = []
        commandsData = self._dbCommands.find({})
        for commandData in commandsData:
            command = Command(commandData)
            result.append(command)
        return result

    def getCommand(self, command):
        return Command(self._dbCommands.find({'command' : command})[0])

    def exists(self, command):
        return self._dbCommands.count_documents({'command' : command}) > 0

class Users(object):
    def __init__(self, db, commands):
        self._db = db
        self._commands = commands

    def _getUser(self, id):
        return self._db.find({'id' : id})[0]

    def getAdminId(self):
        return self._db.find({'firstUser': True})[0]['id']

    def add(self, id, name, admin):
        firstUser = (self._db.count_documents({}) == 0)
        item = {
        'id': id,
        'name': name,
        'admin': admin,
        'firstUser': firstUser,
        'blacklisted': False,
        'commands': []
        }
        self._db.insert_one(item)

    def getName(self, id):
    	return self._getUser(id)['name']

    def isBlacklisted(self, id):
        return self._getUser(id)['blacklisted']

    def isAdmin(self, id):
        return self._getUser(id)['admin']

    def exists(self, id):
        return self._db.count_documents({'id' : id}) > 0

    def getCommands(self, id):
        if self.isAdmin(id):
            return self._commands.getAllCommands()

        result = []
        commands = self._getUser(id)['commands']
        for command in commands:
            result.append(self._commands.getCommand(command))
        return result

    def addCommand(self, id, command):
        if not self._commands.exists(command):
            return
        self._db.update_one({'id' : id}, {'$addToSet' : {'commands': command}})

    def removeCommand(self, id, command):
        self._db.update_one({'id' : id}, {'$pull' : {'commands': command}})

    def getCommandsString(self, id):
        result = ""
        commands = self._getUser(id)['commands']
        for command in commands:
            result += command + " "

        return result

    def getUserIds(self):
        result = []
        allUsers = self._db.find({})
        for user in allUsers:
            result.append(user['id'])
        return result


    def hasAtLeastOneUser(self):
        return self._db.count_documents({}) > 0

class Database(object):
    def __init__(self):
        self._mongo = MongoClient(
            host = [ "mongo:27017" ],
            serverSelectionTimeoutMS = 3000, # 3 second timeout
            username = os.environ["MONGO_USER"],
            password = os.environ["MONGO_PASS"],
        )
        db = self._mongo['telegramDb']
        self._commands = Commands(db)
        self._users = Users(db['users'], self._commands)

    def getUsers(self):
        return self._users

    def getCommands(self):
        return self._commands

