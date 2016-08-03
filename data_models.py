from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase
import datetime
from pprint import pprint
from settings_provider import SettingsProvider
import os

settings_dir = os.path.dirname(os.path.abspath(__file__))
setings_path = os.path.normpath(os.path.join(settings_dir, 'settings.json'))
print(setings_path)
settings_provider = SettingsProvider(setings_path)


db = SqliteExtDatabase(settings_provider.database_path())

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    uid = BigIntegerField(index=True)
    username = TextField(index=True)
    last_name = TextField(index=True) 
    first_name =TextField(index=True)

class ActionType(BaseModel):
    description = TextField(index=True, unique=True)

class EncsPPC_Action(BaseModel):
    action = ForeignKeyField(ActionType)
    created_date = DateTimeField()
    user = ForeignKeyField(User, related_name='user', index=True)