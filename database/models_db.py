from peewee import *
from playhouse.postgres_ext import ArrayField
from datetime import datetime
from models.enum_classes import EntityType, StatusType


def update_timestamp(func):
    def wrapper(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return func(self, *args, **kwargs)

    return wrapper


class BaseModel(Model):
    class Meta:
        database = None


class UserDB(BaseModel):
    id = AutoField()
    tg_id = BigIntegerField(unique=True, null=True)
    username = CharField(null=True)
    name = CharField(null=True)
    info = TextField(null=True)
    added_db = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "user_profile"
        database = None


class EntityDB(BaseModel):
    id = AutoField()
    src_id = CharField(unique=True, null=True)
    title = CharField()
    type = CharField(
        choices=[(tag.value, tag.value) for tag in EntityType],
        default=EntityType.UNDEFINED.value,
    )
    description = TextField(null=True)
    poster_url = CharField(null=True)
    duration = IntegerField(null=True)
    genres = ArrayField(CharField, null=True)
    authors = ArrayField(CharField, null=True)
    actors = ArrayField(CharField, null=True)
    countries = ArrayField(CharField, null=True)
    release_date = DateField(null=True)
    year_start = IntegerField(null=True)
    year_end = IntegerField(null=True)
    total_season = IntegerField(null=True)
    added_db = DateTimeField(default=datetime.now)
    updated_db = DateTimeField(default=datetime.now)

    @update_timestamp
    def save(self, *args, **kwargs):
        return super(EntityDB, self).save(*args, **kwargs)

    class Meta:
        table_name = "entity"
        database = None


class RatingDB(BaseModel):
    entity = ForeignKeyField(EntityDB, backref="ratings")
    source = CharField()
    value = FloatField()
    max_value = IntegerField()
    percent = BooleanField(default=False)

    class Meta:
        primary_key = CompositeKey("entity", "source")
        table_name = "rating"
        database = None


class UserEntityDB(BaseModel):
    id = AutoField()
    user = ForeignKeyField(UserDB, backref="user_entities")
    entity = ForeignKeyField(EntityDB, backref="user_entities")
    status = CharField(
        choices=[(tag.value, tag.value) for tag in StatusType],
        default=StatusType.UNDEFINED.value,
    )
    user_rating = IntegerField(null=True)
    comment = TextField(null=True)
    current_season = IntegerField(null=True)
    added_db = DateTimeField(default=datetime.now)
    updated_db = DateTimeField(default=datetime.now)

    @update_timestamp
    def save(self, *args, **kwargs):
        return super(UserEntityDB, self).save(*args, **kwargs)

    class Meta:
        table_name = "user_entity"
        database = None
