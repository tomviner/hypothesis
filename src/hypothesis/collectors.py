import threading


class DataCollector(object):
    local_storage = threading.local()

    @classmethod
    def active(cls):
        try:
            return cls.local_storage.active
        except AttributeError:
            cls.local_storage.active = None
            return cls.local_storage.active

    def __init__(self):
        self.features_seen = set()

    def note_feature(self, feature):
        self.features_seen.add(feature)

    def __enter__(self):
        self.previously_active = self.__class__.active()
        self.__class__.local_storage.active = self

    def __exit__(self, *args, **kwargs):
        assert self.__class__.active() == self
        self.__class__.local_storage.active = self.previously_active
        delattr(self, 'previously_active')


def note_feature(feature):
    active = DataCollector.active()
    if active is not None:
        active.note_feature(feature)
