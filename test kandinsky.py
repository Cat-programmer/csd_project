import logging
import random
import time
import re
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode
from aiogram.utils import executor
import requests
from bs4 import BeautifulSoup
from api import generate as kandinsky # api поменяйте на название файла `api.py` без `.py` в конце

kandinsky('cat','./cat.jpg')