from django.db import models
from rest_framework.reverse import reverse as api_reverse
import uuid
import os
from os import path
from binascii import hexlify
from django.contrib.auth.hashers import make_password

from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
import datetime

def createHash():
    """This function generate 10 character long hash"""
    return uuid.uuid4().hex[:30]
