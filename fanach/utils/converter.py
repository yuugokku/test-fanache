import xml.etree.ElementTree as et

# XML -> [[word, trans, ex]] の変換を行う
class XMLConverter():
	def __init__(self, cfg):
		"""
		cfg = {"wordtag": <見出し語のタグ>, "transtag": <訳語のタグ>, "extag": <用例のタグ>}
		"""
		self.cfg = cfg

	def parse_xml(self, xmltext):
		cvted = []
		info = ""
		root = et.fromstring(xmltext)
		cfg = self.cfg
		if root.tag != "pdic":
			info += "probably not PDIC-XML data;"

		for idx, record in enumerate(root):
			to_add = ["", "", ""]
			if record.tag != "record":
				info += "unexpected tag <%s>;" % record.tag
			for elem in record:
				if elem.tag == cfg["wordtag"]:
					to_add[0] = elem.text
				elif elem.tag == cfg["transtag"]:
					to_add[1] = elem.text
				elif elem.tag == cfg["extag"]:
					to_add[2] = elem.text
				else:
					info += "unexpected tag <%s> in the record %d" % (elem.tag, idx)

			cvted.append(to_add)
		return cvted, info
