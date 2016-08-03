from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase
import datetime


from data_models import User
from data_models import ActionType
from data_models import EncsPPC_Action

from settings_provider import SettingsProvider
from pprint import pprint

settings_provider = SettingsProvider('settings.json')
database_path = settings_provider.database_path()

db = SqliteExtDatabase(database_path)
db.connect()

db.create_tables([User, ActionType, EncsPPC_Action])

action_type_list = ['in', 'out']
for action_type_value in action_type_list:
    action_type = ActionType()
    action_type.description = action_type_value
    action_type.save()