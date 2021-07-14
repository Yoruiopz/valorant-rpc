from pypresence import Presence as PyPresence
from pypresence.exceptions import InvalidPipe
from InquirerPy.utils import color_print
import time, sys

from ..utilities.config.app_config import Config
from ..content.content_loader import Loader
from .presences import (ingame,menu,startup,pregame)

class Presence:

    def __init__(self):
        self.config = Config.fetch_config()
        self.client = None
        try:
            self.rpc = PyPresence(client_id=str(self.config["client_id"]))
            self.rpc.connect()
        except InvalidPipe as e:
            raise Exception(e)
        self.content_data = {}
    
    def main_loop(self,systray):
        self.content_data = Loader.load_all_content(self.client)
        color_print([("LimeGreen bold", "presence running!")])
        while True:
            presence_data = self.client.fetch_presence()
            if presence_data is not None:
                self.update_presence(presence_data["sessionLoopState"],presence_data)
                #print(presence_data)
                time.sleep(self.config["presence_refresh_interval"])
            else:
                systray.exit() #stop systray thread
                sys.exit()

    def update_presence(self,ptype,data=None):
        presence_types = {
            "startup": startup,
            "MENUS": menu,
            "PREGAME": pregame,
            "INGAME": ingame,
        }
        if ptype in presence_types.keys():
            presence_types[ptype].presence(self.rpc,client=self.client,data=data,content_data=self.content_data,config=self.config)