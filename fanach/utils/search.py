# 検索条件のクラス
import re

def xor(con1, con2):
	if con1 and con2:
		return False
	if (not con1) and (not con2):
		return False
	return True


# 条件のクラス
class Condition():
	def __init__(self, keyword, option="is", revert=False, regex=False):
		self.keyword = keyword
		self.option = option
		self.regex = regex
		self.revert = revert

	def validate(self, target):
		if not self.regex:
			if self.option == "starts":
				return xor(target.startswith(self.keyword), self.revert)
			elif self.option == "ends":
				return xor(target.endswith(self.keyword), self.revert)
			elif self.option == "includes":
				return xor(self.keyword in target, self.revert)
			elif self.option == "is":
				return xor(self.keyword == target, self.revert)

		pattern = self.keyword
		sprint(pattern)
		matches = re.finditer(pattern, target)
		loc = []
		if matches is None:
			return xor(self.revert, False)
		loc = [m.span() for m in matches]
		return xor(self.revert, True)
