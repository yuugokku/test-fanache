# Markdown -> HTML 

import re

bl_markers = {
    "unordered_list": "-",
    "ordered_list": ".",
    "header": "#",
    "quote": ">",
    "code": "```",
}
"""
markers = {
    "bold": **,
    "italic": *,
    "underline": __,
    "strike": ~~,
}
link = [ ]( )
image = [ ]
"""


image_class = "img-fluid"

MAX_HEAD_LEVEL = 1

"""
行頭の記号の数を数える
"""
def _count_head_markers(line, mar):
    i = 0
    while line[i] == mar:
        i += 1
        if line[i] == " ":
            break
    return i

"""
行頭の記号を反映させる。

"-": 順序なしリスト
".": 順序ありリスト
"#": 見出し記号
">": 引用
"```": 等幅フォント
"""
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
    if bl_markers["code"] in line:
        if not line_status["code"]:
            line = "<pre>"
        else:
            line = "</pre>"
        line_status["code"] = not line_status["code"]
    return to_add + line[slicepoint:], line_status

"""
"<", ">"のエスケープ処理。

```...```の内部では、すべての<, >を回避する。
それ以外の箇所では、/<, />によって回避する。
"""
def _esc_tags(line, is_code):
    if is_code:
        if line == "<pre>":
            return line
        line = line.replace("<", "&lt;")
        line = line.replace(">", "&gt;")
    line = line.replace("\\<", "&lt;")
    line = line.replace("\\>", "&gt;")
    return line

"""
エスケープされた行に対し修飾する。
"""
def _inlines_escaped(line):
    style_pats = [r"\*\*(.+?)\*\*", r"\*(.+?)\*", r"__(.+?)__", r"~~(.+?)~~", r"`(.+?)`"]
    style_names = ["b", "i", "u", "s", "code"]
    for p, n in zip(style_pats, style_names):
        line = re.sub(p, r"<%s>\1</%s>" % (n, n), line)
        # print(re.search(p, line))
    link_pat = re.compile(r"\[([^\t]+?)\]\((\S+?)\)")
    line = re.sub(link_pat, "<a href=\"\\2\">\\1</a>", line)
    image_pat = re.compile(r"\[(\S+)\]")
    line = re.sub(image_pat, "<img src=\"\\1\" class=\"%s\">" % image_class, line) 
    return line

"""
エスケープ処理をかけた上で、修飾を適用する。
バックスラッシュ'\'によりエスケープされる。
"""
def _inlines(line):
    escape_pat = re.compile(r"\\{1}[\*~_\[\]\(\)]{1}")
    matches = re.split(escape_pat, line)
    escapes = [m for m in re.findall(escape_pat, line)]
    if len(matches) < 2:
        return _inlines_escaped(line)
    line = ""
    for m, e in zip(matches, escapes):
        line += _inlines_escaped(m) + e[1]
    line += _inlines_escaped(matches[-1])
    return line

"""
テーブルを作成する。
"""
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

"""
markdownをパースする。

mdtext: markdownテキストデータ

line_status: 行ごとの状態。
"""
def parse_md(mdtext):
    line_status = {
        "list_structure": "",
        "quote": False,
        "table_mode": False,
        "code": False,
    }
    cvted = ""
    mdlines = mdtext.splitlines()
    for line in mdlines:
        line, line_status = _beginning_of_line(line, line_status)
        line, line_status = _create_table(line, line_status)
        line = _esc_tags(line, line_status["code"])
        line = _inlines(line)
        cvted += line
        if not line_status["table_mode"]:
            cvted += "<br>"
    return cvted
