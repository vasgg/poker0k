import psutil


def print_non_system_processes():
    for proc in psutil.process_iter(['pid', 'name', 'username']):
        try:
            if proc.info['name'] in ['GGnet.exe', 'pokerok.exe']:
                print(f"PID: {proc.info['pid']}, User: {proc.info['username']}, Name: {proc.info['name']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass


if __name__ == "__main__":
    print_non_system_processes()
