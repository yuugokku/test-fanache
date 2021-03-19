# 検索条件のクラス
import re

def xor(con1, con2):
	if con1 and con2:
		return False
	if (not con1) and (not con2):
		return False
	return True


def find_words(self, target, conditions, operator="or"):
	spans = []
	flags = []
	for result in [cond.validate(target) for cond in conditions]:
		spans.append(result[0])
		flags.append(result[1])

	if operator == "and":
		return sum(flags) == len(flags), spans
	elif operator == "or":
		return sum(flags) > 0, spans

class Condition():
	def __init__(self, keyword, option="is", revert=False, regex=False):
		self.keyword = keyword
		self.option = option
		self.regex = regex

	def validate(self, target):
		if not regex:
			if self.option == "starts":
				pattern = r"\w+" + self.keyword
			elif self.option == "ends":
				pattern = self.keyword + r"\w+"
			elif self.option == "includes":
				pattern = r"\w+" + self.keyword + r"\w+"
			elif self.option == "is":
				pattern = self.keyword

		else:
			pattern = self.keyword

		matches = re.finditer(pattern, target)
		loc = []
		if matches is None:
			return xor(revert, False), loc
		loc = [m.span for m in matches]
		return xor(revert, True), loc
