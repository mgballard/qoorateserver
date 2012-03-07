#!/usr/bin/env python
from dictshield import fields
from dictshield.document import Document, EmbeddedDocument
from dictshield.fields import ShieldException
from dictshield.fields.compound import EmbeddedDocumentField
import json
import datetime
import time
from datetime import timedelta
from qoorateserver.qoorate import getTimeAgo
##
## Our dictshield class defintions
##
class Qoorate(Document):
    """a qoorate user
    Will matche the field in MySQL table"""

    def __init__(self, *args, **kwargs):
        super(Qoorate, self).__init__(*args, **kwargs)


class User(Document):
    """a qoorate user
    Matches a row in MySQL table"""
    id = fields.LongField(required=True,id_field=True)
    role = fields.LongField(required=True)
    email = fields.StringField(required=True)
    password = fields.StringField(required=True, max_length=255)
    oauth_provider = fields.StringField(required=True, max_length=10)
    oauth_uid = fields.StringField(required=True, max_length=255)
    username = fields.StringField(required=True, max_length=255)
    location = fields.StringField(required=True, max_length=255)
    changeDate = fields.DateTimeField(required=True)
    createDate = fields.DateTimeField(required=True)
    thumbnailSmall = fields.StringField(required=True, max_length=255)
    thumbnailLarge = fields.StringField(required=True, max_length=255)
    oauth_session_id = fields.StringField(required=True, max_length=128)
    oauth_access_token = fields.StringField(required=True, max_length=4096)
    oauth_data = fields.StringField(required=True, max_length=5000)    

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        
        # seconds is enough here, we need an int
        self.timestamp = int(time.time())


class Comment(Document):
    """A single comment message
    Matches a row in MySQL table"""

    id = fields.LongField(required=True,id_field=True)
    locationId = fields.LongField(required=True)
    relatedId = fields.LongField(required=True)
    parentId = fields.LongField(required=True)
    userId = fields.LongField(required=True)
    type = fields.LongField(required=True)
    name = fields.StringField(required=True, max_length=1000)
    location = fields.StringField(required=True, max_length=255)
    description = fields.StringField(required=True, max_length=10000)
    voteCount = fields.LongField(required=True)
    voteNumber = fields.LongField(required=True)
    votesUp = fields.LongField(required=True)
    votesDown = fields.LongField(required=True)
    flagCount = fields.LongField(required=True)
    sortOrder = fields.LongField(required=True)
    status = fields.StringField(required=True, max_length=255)
    thumbnailSmall = fields.StringField(required=True, max_length=255)
    thumbnailLarge = fields.StringField(required=True, max_length=255)
    referer = fields.StringField(required=True, max_length=2083)
    changeDate = fields.DateTimeField(required=True)
    createDate = fields.DateTimeField(required=True)

    # The table name, since each API user has unique table name for comments
    tableName = fields.StringField(required=True, max_length=255)
	 
    def __init__(self, *args, **kwargs):
        super(Comment, self).__init__(*args, **kwargs)
        self.timestamp = int(time.time() * 1000)

    def getTimeAgo(self):
        """a wrapper for our method"""
        return getTimeAgo(self.createDate)


class Image(EmbeddedDocument):
    """A single comment message
    Matches a row in MySQL table"""

    id = fields.LongField(required=True,id_field=True)
    itemId = fields.LongField(required=True)
    s3Bucket = fields.StringField(required=True, max_length=255)
    thumbnailLargeHash = fields.StringField(required=True, max_length=255)

    # The table name, since each API user has unique table names for images
    tableName = fields.StringField(required=True, max_length=255)

    def __init__(self, *args, **kwargs):
        super(Image, self).__init__(*args, **kwargs)
        self.timestamp = int(time.time() * 1000)


class CommentItem(Document):
    """A single comment message
    This is not really an entity now, 
    but the data returned by a query need to build the template"""
    parent_sequence = fields.IntField(required=True)
    child_sequence = fields.IntField(required=True)
    id = fields.IntField(required=True,id_field=True)
    locationId = fields.IntField(required=True)
    relatedId = fields.IntField(required=True)
    parentId = fields.IntField(required=True)
    userId = fields.IntField(required=True)
    username = fields.StringField(max_length=255)
    userThumbnailLarge = fields.StringField(max_length=255)
    relatedUsername = fields.StringField(max_length=255)
    relatedUserThumbnailLarge = fields.StringField(max_length=255)
    type = fields.IntField(required=True)
    name = fields.StringField(max_length=1000)
    location = fields.StringField(max_length=255)
    description = fields.StringField(max_length=5000)
    voteCount = fields.IntField(required=True)
    voteNumber = fields.IntField(required=True)
    votesUp = fields.IntField(required=True)
    votesDown = fields.IntField(required=True)
    flagCount = fields.IntField(required=True)
    sortOrder = fields.IntField(required=True)
    status = fields.StringField(max_length=255)
    thumbnailSmall = fields.StringField(max_length=40)
    thumbnailLarge = fields.StringField(max_length=40)
    changeDate = fields.DateTimeField(required=True)
    createDate = fields.DateTimeField(required=True)
    imageUrl = fields.StringField(max_length=512)
    images = fields.compound.ListField(EmbeddedDocumentField(Image))

    # The comment table name, since each API user has unique table names
    tableName = fields.StringField(required=True, max_length=255)

    def __init__(self, *args, **kwargs):
        super(CommentItem, self).__init__(*args, **kwargs)
        self.timestamp = int(time.time() * 1000)

    def getTimeAgo(self):
        """a wrapper for our method"""
        return getTimeAgo(self.createDate)


class Vote(Document):
    """A single vote
    Matches a row in MySQL table"""

    id = fields.LongField(required=True,id_field=True)
    refTable = fields.StringField(required=True, max_length=255)
    itemId = fields.LongField(required=True)
    userId = fields.LongField(required=True)
    qootid = fields.StringField(required=True, max_length=255)
    up = fields.IntField(required=True)
    down = fields.IntField(required=True)
    comment = fields.StringField(required=True, max_length=255)
    createDate = fields.DateTimeField(required=True)
    thumbnailLarge = fields.StringField(required=True, max_length=255)

    def __init__(self, *args, **kwargs):
        super(Vote, self).__init__(*args, **kwargs)
        self.timestamp = int(time.time() * 1000)

class Flag(Document):
    """A single flag
    Matches a row in MySQL table"""

    id = fields.LongField(required=True,id_field=True)
    refTable = fields.StringField(required=True, max_length=255)
    itemId = fields.LongField(required=True)
    userId = fields.LongField(required=True)
    flagTypeId = fields.LongField(required=True)
    createDate = fields.DateTimeField(required=True)

    def __init__(self, *args, **kwargs):
        super(Flag, self).__init__(*args, **kwargs)
        self.timestamp = int(time.time() * 1000)

class KeyPair(Document):
    """An API key pair (key, secret)
    Matches a row in MySQL table"""

    id = fields.LongField(required=True,id_field=True)
    key = fields.LongField(required=True)
    secret = fields.LongField(required=True)

    def __init__(self, *args, **kwargs):
        super(KeyPair, self).__init__(*args, **kwargs)
        self.timestamp = int(time.time() * 1000)

class Qoorate(Document):
    """A single flag
    Matches a row in MySQL table"""

    id = fields.LongField(required=True,id_field=True)
    userId = fields.LongField(required=True)
    shortTitle = fields.StringField(required=True, max_length=255)
    longTitle = fields.StringField(required=True, max_length=255)
    url = fields.StringField(required=True, max_length=250)
    preferences = fields.StringField(required=True, max_length=1000)
    description = fields.StringField(max_length=255)
    fieldNames = fields.StringField(max_length=255)
    refTable = fields.StringField(required=True, max_length=255)
    hasCat = fields.StringField(max_length=255)
    hasLoc = fields.StringField(max_length=255)
    hasPrice = fields.StringField(max_length=255)
    hasDesc = fields.StringField(max_length=255)
    createDate = fields.StringField(max_length=255)
    hangeDate = fields.StringField(max_length=255)
    catNames = fields.StringField(required=True, max_length=1000)
    catAllowed = fields.StringField(required=True, max_length=1000)
    thumbnailSmall = fields.StringField(max_length=255)
    thumbnailLarge = fields.StringField(max_length=255)

    def __init__(self, *args, **kwargs):
        super(Qoorate, self).__init__(*args, **kwargs)
        self.timestamp = int(time.time() * 1000)

