from json import JSONEncoder
from json import JSONDecoder

class User(object):
    def __init__(self, user_id, post=0, link=0):
        self.user_id = user_id
        self.post_karma = post
        self.link_karma = link

    def increase_karma(self, karma_type):
        if karma_type == 'post':
            self.post_karma += 1
        elif karma_type == 'link':
            self.link_karma += 1
        else:
            raise RuntimeError(f'Cannot increase Karma of type {karma_type}')

    def decrease_karma(self, karma_type):
        if karma_type == 'post':
            self.post_karma = max(0, self.post_karma-1)
        elif karma_type == 'link':
            self.link_karma = max(0, self.link_karma-1)
        else:
            raise RuntimeError(f'Cannot increase Karma of type {karma_type}')


class UserEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, User):
            out = dict()
            out['__User__'] = True
            out['user_id'] = o.user_id
            out['post_karma'] = o.post_karma
            out['link_karma'] = o.link_karma
            return out
        else:
            return super().default(o)


class UserDecoder(JSONDecoder):
    def __init__(self, *args, **kwargs):
        JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, o):
        if '__User__' in o:
            return User(o['user_id'], o['post_karma'], o['link_karma'])
        else:
            return o
