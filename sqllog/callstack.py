import traceback


class CallStack(object):
    def __init__(self, filter_func=None):
        self.filter_func = filter_func

    def get(self):
        return [
            x for x in traceback.extract_stack()
            if self.filter_func and self.filter_func(x.filename)
        ]

    def __str__(self):
        return '\n'.join(
            f'{x.filename}:{x.lineno}'
            for x in self.get()
        )
