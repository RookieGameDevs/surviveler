from client import sdl2context
from client import Client


@sdl2context()
def main():
    client = Client(1024, 768)
    client.start()
    client.quit()


if __name__ == '__main__':
    main()
