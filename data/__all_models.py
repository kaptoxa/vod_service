import datetime
import sqlalchemy as sa
from sqlalchemy import orm
from .db import SqlAlchemyBase
from marshmallow import Schema, fields, ValidationError, pre_load, post_load
from hashids import Hashids

from pprint import pprint


### MODELS ###

class ShortUrl(SqlAlchemyBase):
    __tablename__ = 'short_urls'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    url = sa.Column(sa.String, unique=True)
    long_id = sa.Column(sa.Integer, sa.ForeignKey("long_urls.id"))

    long = orm.relation("LongUrl", back_populates='short')
    jumps_count = sa.Column(sa.Integer, default=0)

    def __repr__(self):
        return f"Short link ({self.id}): {self.url}"


class LongUrl(SqlAlchemyBase):
    __tablename__ = 'long_urls'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    url = sa.Column(sa.Text)
    short = orm.relation(ShortUrl, back_populates='long')


### SCHEMAS ###


class SchemaShortUrl(Schema):
    id = fields.Int(dump_only=True)
    url = fields.Str(data_key='short_link')
    jumps_count = fields.Int(data_key='count')
    long_id = fields.Int()

    @pre_load
    def create_hashid(self, data, **kwargs):
        url = data.get('short_link')
        if not url:
            url = 1  # oops... record with id = 1 in short_urls will be rewriting
            # raise exception...
        data['short_link'] = Hashids().encode(url)
        return data

    @post_load
    def make_link(self, data, **kwargs):
        return ShortUrl(url=data['url'], long_id=Hashids().decode(data['url']))


class SchemaLongUrl(Schema):
    id = fields.Int(dump_only=True)
    url = fields.Str(data_key='long_url', required=True)