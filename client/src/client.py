from time import sleep


class Client:
    def __init__(self, renderer, connection):
        self.renderer = renderer
        self.connection = connection

    def update(self):
        while True:
            data = self.connection.read() or None
            if data:
                print(data)
            else:
                sleep(0.5)

            self.renderer.render()
