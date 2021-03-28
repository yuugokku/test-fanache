import xml.etree.ElementTree as et

def export_csv(wordlist, replace_newline="\\"):
	cvted = ""
	cvted += "word,trans,ex\n"
	for word in wordlist:
		line = ""
		for text in word:
			if text is None:
				text = ""
			line += text.replace("\r", "").replace("\n", replace_newline)
			line += ","
		line = line[:-1]
		cvted += line + "\n"
	return cvted

def parse_csv(csvtext):
	cvted = []
	for line in csvtext.splitlines():
		record = line.split(",")
		print(record)
		for _ in range(len(record), 3):
			record.append("")
		if len(record) > 3:
			record = record[:3]
		cvted.append(record)
	return cvted

# XML <-> [[word, trans, ex]] の変換を行う
cfg = {"wordtag": "word", "transtag": "trans", "extag": "ex"}

def parse_xml(xmltext):
	cvted = []
	info = ""
	root = et.fromstring(xmltext)
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
	print(info)
	return cvted

def export_xml(wordlist):
	root = et.Element("fanache")
	for word in wordlist:
		record = et.Element("record")
		for tag,text in zip([cfg["wordtag"], cfg["transtag"], cfg["extag"]], word):
			elem = et.Element(tag)
			elem.text = text
			record.append(elem)
		root.append(record)
	return et.tostring(root, encoding="unicode", method="xml")

def parse(text, mimetype):
	if mimetype == "text/csv":
		if type(text) is bytes:
			return parse_csv(text.decode("utf-8"))
		else:
			return parse_csv(text)
	elif mimetype == "text/xml":
		return parse_xml(text)