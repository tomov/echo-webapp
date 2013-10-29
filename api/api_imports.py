# common stuff
# note that you cannot do this in __init__.py

from flask import request, Blueprint
import json

from model import db, User, Quote
from auth import *
from tracking import *
from util import *
from constants import *
from common import *