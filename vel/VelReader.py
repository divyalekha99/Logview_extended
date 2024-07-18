class VelReader:
    def __init__(self, jsonPath):
        self.path = jsonPath
        self.vel = None

    def read(self):
        with open(self.path, 'r') as f:
            self.vel = f.read()

    def get_vel(self):
        return self.vel