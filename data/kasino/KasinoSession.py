import json
import os
from json import JSONEncoder
from json import JSONDecoder

class KasinoSession(object):
    def __init__(self, question, optionA, optionB, bets, amountA, amountB, guildID, channelID, messageID, locked=False, optionABets=None, optionBBets=None):
        if optionBBets is None:
            optionBBets = {}
        if optionABets is None:
            optionABets = {}
        self.question = question
        self.optionA = optionA
        self.optionB = optionB
        self.bets = bets
        self.amountA = amountA
        self.amountB = amountB
        self.guildID = guildID
        self.channelID = channelID
        self.messageID = messageID
        self.locked = locked
        self.optionABets = optionABets
        self.optionBBets = optionBBets

    def save_session(self):
        with open(os.path.abspath('./data/kasino/session.json'), 'w') as outfile:
            json.dump(self, outfile, cls=KasinoEncoder, indent=4)


class KasinoBet(object):
    def __init__(self, userID, amount):
        self.userID = userID
        self.amount = amount


class KasinoEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, KasinoSession):
            out = dict()
            out['__KasinoSession__'] = True
            out['question'] = o.question
            out['optionA'] = o.optionA
            out['optionB'] = o.optionB
            out['bets'] = o.bets
            out['amountA'] = o.amountA
            out['amountB'] = o.amountB
            out['guildID'] = o.guildID
            out['channelID'] = o.channelID
            out['messageID'] = o.messageID
            out['locked'] = o.locked
            out['optionABets'] = o.optionABets
            out['optionBBets'] = o.optionBBets
            return out
        elif isinstance(o, KasinoBet):
            out = dict()
            out['__KasinoBet__'] = True
            out['userID'] = o.userID
            out['amount'] = o.amount
            return out
        else:
            return super().default(o)


class KasinoDecoder(JSONDecoder):
    def __init__(self, *args, **kwargs):
        JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, o):
        if '__KasinoSession__' in o:
            optionABets = KasinoDecoder.object_hook(self, o['optionABets'])
            optionBBets = KasinoDecoder.object_hook(self, o['optionBBets'])
            return KasinoSession(o['question'], o['optionA'], o['optionB'], int(o['bets']), int(o['amountA']), int(o['amountB']), o['guildID'], o['channelID'], o['messageID'], o['locked'], optionABets, optionBBets)
        elif '__KasinoBet__' in o:
            return KasinoBet(int(o['userID']),int(o['amount']))
        else:
            return o