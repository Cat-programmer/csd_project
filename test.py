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
import unittest

def cut_after(start_substring, input_string):
    pattern = re.compile(start_substring + '.*', re.DOTALL)
    output_string = re.sub(pattern, '', input_string)
    return output_string.strip()

test = """Название ИИ: 'КСД'
rubrush ec: нарисуй пейзаж, который рисуется за 5 секунд, 1 минуту, 1 час, 24 часа, 1 неделя
КСД:  DRAW abstract landscape, minimalist, few details, incomplete, sketch, unfinished, ethereal, dreamlike, duality. END"""

new_text = cut_after(f"rubrush ec: ", test)

print (new_text)