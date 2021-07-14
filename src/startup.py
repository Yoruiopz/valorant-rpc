from InquirerPy.utils import color_print
import sys, psutil, time, cursor, valclient, ctypes

from .utilities.killable_thread import Thread
from .utilities.config.app_config import Config
from .utilities.config.modify_config import Config_Editor
from .utilities.processes import Processes
from .utilities.rcs import Riot_Client_Services
from .utilities.systray import Systray
from .utilities.version_checker import Checker

from .presence.presence import Presence

kernel32 = ctypes.WinDLL('kernel32')
#kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), 128) #disable inputs to console
kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7) #allow for ANSI sequences

class Startup:
    def __init__(self):
        cursor.hide()
        Config.check_config()

        self.config = Config.fetch_config()
        self.systray = Systray()
        self.client = None
        ctypes.windll.kernel32.SetConsoleTitleW(f"valorant-rpc {self.config['version']}") 

        if self.config["region"] == "":
            # if region hasn't been set yet
            self.config["region"] = Config_Editor.set_region("na")
            Config.modify_config(self.config)


        color_print([("Red", "waiting for rpc client")])
        try:
            self.presence = Presence()
            Startup.clear_line()
            self.dispatch_systray()
            self.run()
        except Exception as e:
            color_print([("Cyan",f"discord not detected! starting game without presence... ({e})")])
            if not Processes.are_processes_running():
                color_print([("Red", "starting VALORANT")])
                self.start_game()
                sys.exit()


    def run(self):
        self.presence.update_presence("startup")
        Checker.check_version(self.config)
        if not Processes.are_processes_running():
            color_print([("Red", "starting VALORANT")])
            self.start_game()
        
        self.setup_client()
        
        if self.client.fetch_presence() is None:
            self.wait_for_presence()
        
        self.dispatch_presence()
        self.systray_thread.join()
        self.presence_thread.stop()
        color_print([("Red","presence closed")])
        
        
        
    def dispatch_presence(self):
        self.presence_thread = Thread(target=self.presence.main_loop,args=(self.systray,),daemon=True)
        self.presence_thread.start()

    def dispatch_systray(self):
        self.systray_thread = Thread(target=self.systray.run)
        self.systray_thread.start()

    def setup_client(self):
        self.client = valclient.Client(region=self.config["region"])
        self.client.activate()
        self.presence.client = self.client

    def wait_for_presence(self):
        presence_timeout = self.config["startup"]["presence_timeout"]
        presence_timer = 0 
        print()
        while self.client.fetch_presence() is None:
            Startup.clear_line()
            color_print([("Cyan", "["),("White",f"{presence_timer}"),("Cyan", "] waiting for presence... ")])
            presence_timer += 1
            if presence_timer >= presence_timeout:
                self.systray.exit()
                sys.exit()
            time.sleep(1)
        Startup.clear_line()
        Startup.clear_line()

    def start_game(self):
        path = Riot_Client_Services.get_rcs_path()
        launch_timeout = self.config["startup"]["game_launch_timeout"]
        launch_timer = 0

        psutil.subprocess.Popen([path, "--launch-product=valorant", "--launch-patchline=live"])
        print()
        while not Processes.are_processes_running():
            Startup.clear_line()
            color_print([("Cyan", "["),("White",f"{launch_timer}"),("Cyan", "] waiting for valorant... ")])
            launch_timer += 1
            if launch_timer >= launch_timeout:
                self.systray.exit()
                sys.exit()
            time.sleep(1)
        Startup.clear_line()

    @staticmethod
    def clear_line():
        sys.stdout.write("\033[F") # move cursor up one line
        sys.stdout.write("\r\033[K")