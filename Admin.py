class Admin():
    def __init__(self, name, password):
        self.name = name
        self.password = password
    def login(self, input_name, input_password):
        if input_name == self.name and input_password == self.password:
            return True
        else:
            return False