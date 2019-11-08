import time
import json
import timeago as timesince

from collections import namedtuple
from discord.ext import commands


class commandsPlus(commands.Command):
    def __init__(self, func, **kwargs):
        super().__init__(func, **kwargs)
        self.category = kwargs.pop("category")

def commandExtra(*args, **kwargs):
    return commands.command(*args, **kwargs, cls=commandsPlus)

class GroupPlus(commands.Group):
    def __init__(self, func, **kwargs):
        super().__init__(func, **kwargs)
        self.category = kwargs.pop("category")

def groupExtra(*args, **kwargs):
    return commands.group(*args, **kwargs, cls=GroupPlus)


def timeago(target):
    return timesince.format(target)


def date(target, clock=True):
    if clock is False:
        return target.strftime("%d %B %Y")
    return target.strftime("%d %B %Y, %H:%M")

