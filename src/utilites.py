import os

import psutil


def check_ggnet_app():
    for proc in psutil.process_iter(['pid', 'name', 'username']):
        try:
            if proc.info['name'] in ['GGnet.exe']:
                return
            else:
                application_path = "C:\\Users\\Administrator\\Desktop\\poker0k\\GGnet.exe"
                os.startfile(application_path)
                return
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass


if __name__ == "__main__":
    check_ggnet_app()
