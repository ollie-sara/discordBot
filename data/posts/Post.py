from json import JSONDecoder, JSONEncoder
from datetime import datetime
import dateutil.parser

class Post(object):
    def __init__(self, url, mid, created_at, content, authorname, up=0, down=0):
        self.message_url = url
        self.message_id = mid
        self.upvotes = up
        self.downvotes = down
        self.created_at = created_at
        self.content = content
        self.author = authorname

    def change_value(self, value, increase):
        if value == 'up':
            if increase:
                self.upvotes += 1
            else:
                self.upvotes = max(0, self.upvotes - 1)
        elif value == 'down':
            if increase:
                self.downvotes += 1
            else:
                self.downvotes = max(0, self.downvotes - 1)


class PostEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, Post):
            out = dict()
            out['__Post__'] = True
            out['message_url'] = o.message_url
            out['message_id'] = o.message_id
            out['upvotes'] = o.upvotes
            out['downvotes'] = o.downvotes
            out['content'] = o.content
            out['author'] = o.author
            out['created_at'] = o.created_at.isoformat()
            return out
        else:
            return super().default(o)


class PostDecoder(JSONDecoder):
    def __init__(self, *args, **kwargs):
        JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, o):
        if '__Post__' in o:
            return Post(url=o['message_url'], mid=o['message_id'], created_at=dateutil.parser.parse(o['created_at']), content=o['content'], up=o['upvotes'], down=o['downvotes'], authorname=o['author'])
        else:
            return o
