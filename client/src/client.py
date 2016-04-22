class Client:
    def __init__(self, renderer, connection):
        self.renderer = renderer
        self.connection = connection

    def start(self):
        while True:
            data = self.connection.read() or None
            if data:
                print(data)

            self.renderer.render()
