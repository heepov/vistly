from peewee import *
from playhouse.postgres_ext import ArrayField
from datetime import datetime
from models.enum_classes import PrivacyType, EntityType, StatusType


def update_timestamp(func):
    def wrapper(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return func(self, *args, **kwargs)

    return wrapper


class BaseModel(Model):
    class Meta:
        database = None


class User(BaseModel):
    id = AutoField()
    tg_id = BigIntegerField(unique=True, null=True)
    username = CharField(null=True)
    name = CharField(null=True)
    info = TextField(null=True)
    privacy_type = CharField(
        choices=[(tag.value, tag.value) for tag in PrivacyType],
        default=PrivacyType.PUBLIC.value,
    )
    added_db = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "user_profile"
        database = None


class Entity(BaseModel):
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
        return super(Entity, self).save(*args, **kwargs)

    class Meta:
        table_name = "entity"
        database = None


class Rating(BaseModel):
    entity = ForeignKeyField(Entity, backref="ratings")
    source = CharField()
    value = FloatField()
    max_value = IntegerField()
    percent = BooleanField(default=False)

    class Meta:
        primary_key = CompositeKey("entity", "source")
        table_name = "rating"
        database = None


class UserEntity(BaseModel):
    id = AutoField()
    user = ForeignKeyField(User, backref="user_entities")
    entity = ForeignKeyField(Entity, backref="user_entities")
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
        return super(UserEntity, self).save(*args, **kwargs)

    class Meta:
        table_name = "user_entity"
        database = None


class Collection(BaseModel):
    id = AutoField()
    user = ForeignKeyField(User, backref="collections")
    title = CharField()
    hashtags = ArrayField(CharField, null=True)
    description = TextField(null=True)
    type = CharField(
        choices=[(tag.value, tag.value) for tag in EntityType],
        default=EntityType.UNDEFINED.value,
    )
    privacy_type = CharField(
        choices=[(tag.value, tag.value) for tag in PrivacyType],
        default=PrivacyType.PUBLIC.value,
    )
    is_default = BooleanField(default=False)
    added_db = DateTimeField(default=datetime.now)
    updated_db = DateTimeField(default=datetime.now)

    @update_timestamp
    def save(self, *args, **kwargs):
        return super(Collection, self).save(*args, **kwargs)

    class Meta:
        table_name = "collection"
        database = None


class CollectionEntity(BaseModel):
    collection = ForeignKeyField(Collection, backref="collection_entities")
    user_entity = ForeignKeyField(UserEntity, backref="collection_entities")

    class Meta:
        primary_key = CompositeKey("collection", "user_entity")
        table_name = "collection_entity"
        database = None
