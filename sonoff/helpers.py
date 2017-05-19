class Lock():
    def __init__(self,value=True):
        self.locked = value

    def __bool__(self):
        return self.locked

    def is_locked(self):
        return self.__bool__()

    def __str__(self):
        return 'Locked' if self.is_locked else 'Unlocked'

    def lock(self):
        self.locked = True

    def unlock(self):
        self.locked = False


