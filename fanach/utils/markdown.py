# Markdown -> HTML 

import re

bl_markers = {
	"unordered_list": "-",
	"ordered_list": ".",
	"header": "#",
	"quote": ">"
}

MAX_HEAD_LEVEL = 1

tag_style = "badge badge-secondary"

def _count_head_markers(line, mar):
	i = 0
	while line[i] == mar:
		i += 1
		if line[i] == " ":
			break
	return i

def _beginning_of_line(line, line_status):
	to_add = ""
	slicepoint = 0
	if line == "":
		for i in range(len(line_status["list_structure"]) - 1, -1 , -1):
			to_add += "</%sl>" % line_status["list_structure"][i]
		line_status["list_structure"] = ""
		if line_status["quote"]:
			to_add += "</blockquote>"
		line_status["quote"] = False
		return to_add + line, line_status
	num_ul = _count_head_markers(line, bl_markers["unordered_list"])
	num_ol = _count_head_markers(line, bl_markers["ordered_list"])
	if num_ul > 0 or num_ol > 0 :
		dl = num_ul + num_ol - len(line_status["list_structure"])
		if dl > 0:
			to_add += ("<ul>" * dl) * (num_ul > num_ol) + ("<ol>" * dl) * (num_ol > num_ul)
			for i in range(dl):
				line_status["list_structure"] += "u" * (num_ul > num_ol) + "o" * (num_ol > num_ul)
		elif dl < 0:
			for i in range(-1, dl - 1, -1):
				to_add += "</%sl>" % line_status["list_structure"][i]
			line_status["list_structure"] = line_status["list_structure"][:dl]
		to_add += "<li>"
		slicepoint = num_ol + num_ul + 1
	num_headers = _count_head_markers(line, bl_markers["header"])
	if num_headers > 0:
		to_add += "<h%d>" % (num_headers + MAX_HEAD_LEVEL)
		line += "</h%d>" % (num_headers + MAX_HEAD_LEVEL)
		slicepoint = num_headers + 1
	num_quotes = _count_head_markers(line, bl_markers["quote"])
	if line_status["quote"]:
		if num_quotes == 0:
			line_status["quote"] = False
	else:
		if num_quotes > 0:
			to_add += "<blockquote class=\"blockquote\">"
			slicepoint = num_quotes + 1
	return to_add + line[slicepoint:], line_status

"""
markers = {
	"bold": **,
	"italic": *,
	"underline": __,
	"strike": ~~,
}

link = [ ]( )
"""

def _inlines(line):
	style_pats = [r"\*\*(.+?)\*\*", r"\*(.+?)\*", r"__(.+?)__", r"~~(.+?)~~"]
	style_names = ["b", "i", "u", "s"]
	for p, n in zip(style_pats, style_names):
		line = re.sub(p, r"<%s>\1</%s>" % (n, n), line)
	link_pat = re.compile(r"\[(\S+)\]\((\S+)\)")
	line = re.sub(link_pat, "<a href=\"\\2\">\\1</a>", line)
	return line

def _create_table(line, line_status):
	to_add = ""
	if len(line) == 0:
		if line_status["table_mode"]:
			to_add += "</table>"
		line_status["table_mode"] = False
		return to_add + line, line_status
	if line[0] == "|" and line[-1] == "|":
		if not line_status["table_mode"]:
			to_add += "<table>"
			line_status["table_mode"] = True
		line = line[1:-1]
		line = line.replace("|", "</td><td>")
		line = "<tr><td>" + line + "</td></tr>"
	else:
		if line_status["table_mode"]:
			to_add += "</table>"
		line_status["table_mode"] = False
	return to_add + line, line_status

def parse_md(mdtext):
	line_status = {
		"list_structure": "",
		"quote": False,
		"table_mode": False,
	}
	cvted = ""
	mdtext = _avoid_tags(mdtext)
	mdlines = mdtext.splitlines()
	for line in mdlines:
		line, line_status = _beginning_of_line(line, line_status)
		line, line_status = _create_table(line, line_status)
		line = _inlines(line)
		cvted += line
		if not line_status["table_mode"]:
			cvted += "<br>"
	return cvted

def _avoid_tags(text):
	tag_pat = r"<([^>]*?)>"
	text = re.sub(tag_pat, "&lt;\\1&gt;",text)
	return text