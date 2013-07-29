#!/usr/bin/env python
import datetime
import json
import time
from datetime import timedelta
import schematics
from schematics import types
from schematics.types import compound as CompoundType
from qoorateserver.qoorate import getTimeAgo
from schematics.models import Model
from schematics.types.compound import ModelType, DictType
##
## Our dictshield class defintions
##
class Qoorate(Model):
    """a qoorate user
    Will matche the field in MySQL table"""

    def __init__(self, *args, **kwargs):
        super(Qoorate, self).__init__(*args, **kwargs)


class User(Model):
    """a qoorate user
    Matches a row in MySQL table"""
    id = types.LongType()

    role = types.LongType(required=True)
    email = types.StringType(required=True)
    password = types.StringType(required=True, max_length=255)
    oauth_provider = types.StringType(required=True, max_length=10)
    oauth_uid = types.StringType(required=True, max_length=255)
    username = types.StringType(required=True, max_length=255)
    location = types.StringType(required=True, max_length=255)
    changeDate = types.DateTimeType(required=True)
    createDate = types.DateTimeType(required=True)
    thumbnailSmall = types.StringType(required=True, max_length=255)
    thumbnailLarge = types.StringType(required=True, max_length=255)
    oauth_session_id = types.StringType(required=True, max_length=128)
    oauth_access_token = types.StringType(required=True, max_length=4096)
    oauth_data = types.StringType(required=True, max_length=5000)
    admin_role_qoorates = types.StringType(required=True, max_length=255)

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        
        # seconds is enough here, we need an int
        self.timestamp = int(time.time())


class Comment(Model):
    """A single comment message
    Matches a row in MySQL table"""
    id = types.LongType()

    locationId = types.LongType(required=True)
    relatedId = types.LongType(required=True)
    parentId = types.LongType(required=True)
    userId = types.LongType(required=True)
    type = types.LongType(required=True)
    is_anonymous = types.IntType(required=True)
    name = types.StringType(required=True, max_length=1000)
    location = types.StringType(required=True, max_length=255)
    description = types.StringType(required=True, max_length=10000)
    voteCount = types.LongType(required=True)
    voteNumber = types.LongType(required=True)
    votesUp = types.LongType(required=True)
    votesDown = types.LongType(required=True)
    flagCount = types.LongType(required=True)
    childCount = types.LongType(required=True)
    sortOrder = types.LongType(required=True)
    status = types.StringType(required=True, max_length=255)
    thumbnailSmall = types.StringType(required=True, max_length=255)
    thumbnailLarge = types.StringType(required=True, max_length=255)
    referer = types.StringType(required=True, max_length=2083)
    changeDate = types.DateTimeType(required=True)
    createDate = types.DateTimeType(required=True)
    nickname = types.StringType(required=False, max_length=255)
    # The table name, since each API user has unique table name for comments
    tableName = types.StringType(required=True, max_length=255)
	 
    def __init__(self, *args, **kwargs):
        super(Comment, self).__init__(*args, **kwargs)
        self.timestamp = int(time.time() * 1000)

    def getTimeAgo(self):
        """a wrapper for our method"""
        return getTimeAgo(self.createDate)


class ImageItem(Model):
    """A single comment message
    Matches a row in MySQL table"""

    id = types.LongType(required=True)
    itemId = types.LongType(required=True)
    s3Bucket = types.StringType(required=True, max_length=255)
    thumbnailLargeHash = types.StringType(required=True, max_length=255)

    # The table name, since each API user has unique table names for images
    tableName = types.StringType(max_length=255)

    def __init__(self, *args, **kwargs):
        super(ImageItem, self).__init__(*args, **kwargs)
        self.timestamp = int(time.time() * 1000)

class CommentItem(Model):
    """A single comment message
    This is not really an entity now, 
    but the data returned by a query need to build the template"""

    id = types.LongType()

    parent_sequence = types.IntType(required=True)
    child_sequence = types.IntType(required=True)
    locationId = types.IntType(required=True)
    relatedId = types.IntType(required=True)
    parentId = types.IntType(required=True)
    userId = types.IntType(required=True)
    username = types.StringType(max_length=255)
    userThumbnailLarge = types.StringType(max_length=255)
    relatedUsername = types.StringType(max_length=255)
    relatedUserThumbnailLarge = types.StringType(max_length=255)
    type = types.IntType(required=True)
    is_anonymous = types.IntType(required=True)
    name = types.StringType(max_length=1000)
    location = types.StringType(max_length=255)
    description = types.StringType(max_length=5000)
    voteCount = types.IntType(required=True)
    voteNumber = types.IntType(required=True)
    votesUp = types.IntType(required=True)
    votesDown = types.IntType(required=True)
    flagCount = types.IntType(required=True)
    childCount = types.IntType(required=True)
    sortOrder = types.IntType(required=True)
    status = types.StringType(max_length=255)
    thumbnailSmall = types.StringType(max_length=40)
    thumbnailLarge = types.StringType(max_length=40)
    changeDate = types.DateTimeType(required=True)
    createDate = types.DateTimeType(required=True)
    imageUrl = types.StringType(max_length=512)
    nickname = types.StringType(max_length=255)

    images = types.compound.ListType(ModelType(ImageItem))

    # The comment table name, since each API user has unique table names
    tableName = types.StringType(required=True, max_length=255)

    def __init__(self, *args, **kwargs):
        super(CommentItem, self).__init__(*args, **kwargs)
        self.timestamp = int(time.time() * 1000)

    def getTimeAgo(self):
        """a wrapper for our method"""
        return getTimeAgo(self.createDate)


class Vote(Model):
    """A single vote
    Matches a row in MySQL table"""

    id = types.LongType()

    refTable = types.StringType(required=True, max_length=255)
    itemId = types.LongType(required=True)
    userId = types.LongType(required=True)
    qootid = types.StringType(required=True, max_length=255)
    up = types.IntType(required=True)
    down = types.IntType(required=True)
    comment = types.StringType(required=True, max_length=255)
    createDate = types.DateTimeType(required=True)
    thumbnailLarge = types.StringType(required=True, max_length=255)

    def __init__(self, *args, **kwargs):
        super(Vote, self).__init__(*args, **kwargs)
        self.timestamp = int(time.time() * 1000)


class Flag(Model):
    """A single flag
    Matches a row in MySQL table"""

    id = types.LongType()

    refTable = types.StringType(required=True, max_length=255)
    itemId = types.LongType(required=True)
    userId = types.LongType(required=True)
    flagTypeId = types.LongType(required=True)
    createDate = types.DateTimeType(required=True)

    def __init__(self, *args, **kwargs):
        super(Flag, self).__init__(*args, **kwargs)
        self.timestamp = int(time.time() * 1000)


class FlagType(Model):
    """A single flagtype
    Matches a row in MySQL table"""

    id = types.LongType()

    name = types.StringType(required=True, max_length=255)
    description = types.StringType(required=True, max_length=255)
    role = types.LongType()
    createDate = types.DateTimeType(required=True)

    def __init__(self, *args, **kwargs):
        super(FlagType, self).__init__(*args, **kwargs)
        self.timestamp = int(time.time() * 1000)


class KeyPair(Model):
    """An API key pair (key, secret)
    Matches a row in MySQL table"""

    id = types.LongType()

    key = types.LongType(required=True)
    secret = types.LongType(required=True)

    def __init__(self, *args, **kwargs):
        super(KeyPair, self).__init__(*args, **kwargs)
        self.timestamp = int(time.time() * 1000)


class Qoorate(Model):
    """A single flag
    Matches a row in MySQL table"""
    id = types.LongType()

    userId = types.LongType(required=True)
    shortTitle = types.StringType(required=True, max_length=255)
    longTitle = types.StringType(required=True, max_length=255)
    url = types.StringType(required=True, max_length=250)
    preferences = types.StringType(required=True, max_length=1000)
    description = types.StringType(max_length=255)
    fieldNames = types.StringType(max_length=255)
    refTable = types.StringType(required=True, max_length=255)
    hasCat = types.StringType(max_length=255)
    hasLoc = types.StringType(max_length=255)
    hasPrice = types.StringType(max_length=255)
    hasDesc = types.StringType(max_length=255)
    createDate = types.StringType(max_length=255)
    hangeDate = types.StringType(max_length=255)
    catNames = types.StringType(required=True, max_length=1000)
    catAllowed = types.StringType(required=True, max_length=1000)
    thumbnailSmall = types.StringType(max_length=255)
    thumbnailLarge = types.StringType(max_length=255)

    def __init__(self, *args, **kwargs):
        super(Qoorate, self).__init__(*args, **kwargs)
        self.timestamp = int(time.time() * 1000)
