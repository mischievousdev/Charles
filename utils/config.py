import os
import json

from utils.logger import log


class Config:
    def __init__(self):

        with open('db/config.json', 'r') as f:
            data = json.load(f)

        self.owner_id = data["BOT_OWNER"]
        self.support_ids = data["BOT_SUPPORT"]

    def check(self):
        if not self.owner_id:
            log.critical("No owner ID was specified in the config, please put your ID for the owner ID in the config")
            os._exit(1)

        if len(self.support_ids) is not 0:
            try:
                ids = self.support_ids.split()
                self.support_ids = []
                for id in ids:
                    self.support_ids.append(int(id))
            except:
                log.warning("Support IDs are invalid, all support member IDs have been ignored!")