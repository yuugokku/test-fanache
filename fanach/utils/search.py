# 検索条件のクラス
import re

from fanach.utils.syllables import into_syllables, scan

def condition_default(o):
    if isinstance(o, Condition):
        return str(o)
    raise TypeError(repr(o) + "is not JSON serializable")

def xor(con1, con2):
    if con1 and con2:
        return False
    if (not con1) and (not con2):
        return False
    return True


# 条件のクラス
class Condition():
    def __str__(self):
        return "Condition(%s, %s, %s)" % (self.keyword, self.option, str(self.revert))

    def __init__(self, keyword, option="is", revert=False):
        self.keyword = keyword
        self.option = option
        self.revert = revert

    def validate(self, target, rhyme=False):
        if rhyme:
            target = scan(target)
        keyword = self.keyword
        if self.option == "starts":
            return xor(target.startswith(keyword), self.revert)
        elif self.option == "ends":
            return xor(target.endswith(keyword), self.revert)
        elif self.option == "includes":
            return xor(keyword in target, self.revert)
        elif self.option == "is":
            return xor(keyword == target, self.revert)
        elif self.option == "regex":
            pattern = self.keyword
            matches = re.match(pattern, target)
            if matches is None:
                return xor(self.revert, False)
            return xor(self.revert, True)
