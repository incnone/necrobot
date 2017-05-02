from necrobot.util import console
from necrobot.util.singleton import Singleton


class NecroEvent(object):
    def __init__(self, event_type: str, **kwargs):
        self.event_type = event_type
        self._argdict = kwargs

    def __getattr__(self, item):
        return self._argdict[item]


class NEDispatch(object, metaclass=Singleton):
    def __init__(self):
        self._subscribers = list()

    def subscribe(self, subscriber):
        if 'ne_process' not in type(subscriber).__dict__:
            console.warning(
                "Object of type {0} tried to subscribe to NEDispatch, but doesn't implement ne_process.".format(
                    type(subscriber).__name__
                )
            )
            return

        self._subscribers.append(subscriber)

    async def publish(self, event_type: str, **kwargs):
        ev = NecroEvent(event_type, **kwargs)
        console.info('Processing event of type {0}.'.format(ev.event_type))

        for subber in self._subscribers:
            await subber.ne_process(ev)
