import os

import psutil


def check_ggnet_app():
    for proc in psutil.process_iter(['pid', 'name', 'username']):
        try:
            if proc.info['name'] in ['GGnet.exe']:
                print('GGnet is running')
                return
            else:
                application_path = r"C:\Users\Administrator\AppData\Roaming\POKEROK\bin\Loader\GGnet.exe"
                os.startfile(application_path)
                print('Starting GGnet')
                return
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass


if __name__ == "__main__":
    check_ggnet_app()
