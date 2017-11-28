class Lock():
    """ Such a simple class was implemented because timer's callback needs a
    function to call.
    """
    def __init__(self,value=True):
        self.locked = value

    def __bool__(self):
        return self.locked

    def is_locked(self):
        return self.__bool__()

    # Should be parametrized as the timer calls it with a (useless in this case)
    # parameter
    def lock(self,*args,**kwargs):
        self.locked = True

    def unlock(self,*args,**kwargs):
        self.locked = False


