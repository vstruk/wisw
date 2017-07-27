class Lock():
    """ Such a simple class was implemented because timer's callback needs a
    function to call
    """
    def __init__(self,value=True):
        self.locked = value

    def __bool__(self):
        return self.locked

    def is_locked(self):
        return self.__bool__()

    def lock(self):
        self.locked = True

    def unlock(self):
        self.locked = False


