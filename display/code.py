import re
from colorama import Fore, Style

def highlight_code(lang: str, code: str) -> str:
    # 根据语言名称做轻量高亮
    lang = (lang or "").lower().strip()
    BLUE = Fore.BLUE + Style.BRIGHT
    GREEN = Fore.GREEN
    CYAN = Fore.CYAN
    GREY = Fore.LIGHTBLACK_EX
    YELLOW = Fore.YELLOW
    MAGENTA = Fore.MAGENTA
    LIGHTBLUE = Fore.LIGHTBLUE_EX
    LIGHTGREEN = Fore.LIGHTGREEN_EX
    LIGHTRED = Fore.LIGHTRED_EX
    LIGHTCYAN = Fore.LIGHTCYAN_EX
    LIGHTMAGENTA = Fore.LIGHTMAGENTA_EX
    RESET = Style.RESET_ALL

    string_pat = re.compile(r'(\"\"\"[\s\S]*?\"\"\"|\'\'\'[\s\S]*?\'\'\'|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')')
    line_comment = re.compile(r'(//.*$|#.*$|--.*$)', re.MULTILINE)
    block_comment = re.compile(r'/\*[\s\S]*?\*/')
    number_pat = re.compile(r'\b\d+(?:\.\d+)?\b')
    op_pat = re.compile(r'(\+\+|--|==|!=|<=|>=|->|<<|>>|&&|\|\||[+\-*/%=&|^<>!~])')
    call_pat = re.compile(r'\b([A-Za-z_]\w*)(?=\s*\()')
    type_pat = re.compile(r'\b([A-Z][A-Za-z0-9_]*|int|float|double|char|bool|boolean|string|String|List|Map|Dict|Set|Tuple|Vector|Array|Object|Class)\b')
    var_pat = re.compile(r'\b([A-Za-z_]\w*)\b')
    bracket_pat = re.compile(r'[\[\]\(\)\{\}]')

    kw_common = {
        "python": ["def","class","import","from","as","if","elif","else","for","while","return","try","except","with","yield","lambda","pass","break","continue","in","is","not","and","or","None","True","False"],
        "java": ["class","public","private","protected","static","final","void","int","double","float","boolean","new","return","if","else","switch","case","break","continue","try","catch","finally","import","package","for","while","do","extends","implements","this","super","null","true","false"],
        "c": ["int","char","float","double","void","struct","typedef","return","if","else","for","while","do","switch","case","break","continue","static","const","include","define","NULL"],
        "cpp": ["int","char","float","double","void","struct","class","template","typename","using","namespace","std","return","if","else","for","while","do","switch","case","break","continue","static","const","include","define","new","delete","NULL","nullptr","virtual","override"],
        "c#": ["class","public","private","protected","static","readonly","void","int","double","float","bool","new","return","if","else","switch","case","break","continue","try","catch","finally","using","namespace","for","while","do","var","null","true","false","async","await"],
        "go": ["func","package","import","var","const","type","struct","interface","return","if","else","switch","case","break","continue","for","range","go","defer","nil","true","false"],
        "lua": ["function","local","end","if","then","elseif","else","for","while","repeat","until","return","nil","true","false"],
        "js": ["function","class","import","from","export","const","let","var","return","if","else","switch","case","break","continue","try","catch","finally","new","this","=>","null","true","false","await","async"],
        "ts": ["function","class","import","from","export","const","let","var","return","if","else","switch","case","break","continue","try","catch","finally","new","this","=>","null","true","false","await","async","interface","type"],
        "css": ["color","background","margin","padding","display","position","flex","grid","border","font","width","height","content","::before","::after","hover"],
        "html": [],
        "xml": [],
        "json": [],
    }

    # 用占位符保护字符串/注释，避免后续规则误匹配
    tokens = []
    def _store(kind: str, text_value: str) -> str:
        tokens.append((kind, text_value))
        marker = chr(0xE000 + len(tokens) - 1)
        return f"\uFFF2{marker}\uFFF3"

    text = code
    text = string_pat.sub(lambda m: _store("str", m.group(0)), text)
    text = block_comment.sub(lambda m: _store("com", m.group(0)), text)
    text = line_comment.sub(lambda m: _store("com", m.group(0)), text)

    # 再做标签、键名与关键词
    if lang in ("html","xml"):
        tag_pat = re.compile(r'(<\/?[\w\-:]+)')
        text = tag_pat.sub(lambda m: f"\uFFF0T{m.group(1)}\uFFF1", text)
        attr_pat = re.compile(r'(\s[\w\-:]+)(=)')
        text = attr_pat.sub(lambda m: f"\uFFF0A{m.group(1)}\uFFF1{m.group(2)}", text)
    elif lang == "json":
        key_pat = re.compile(r'("([^"\\]|\\.)*")\s*:')
        text = key_pat.sub(lambda m: f"\uFFF0J{m.group(1)}\uFFF1:", text)
    else:
        base = "python" if lang == "py" else "cpp" if lang in ("c++","cpp","cc","hpp") else "c#" if lang in ("cs","csharp","c#") else "js" if lang in ("javascript","node") else "ts" if lang in ("typescript") else lang
        kws = kw_common.get(base, [])
        if kws:
            kw_re = re.compile(r'\b(' + '|'.join(map(re.escape, kws)) + r')\b')
            text = kw_re.sub(lambda m: f"\uFFF0K{m.group(1)}\uFFF1", text)

    kw_set = set(kw_common.get(base, [])) if 'base' in locals() else set()
    type_set = set([t.lower() for t in [
        "int","float","double","char","bool","boolean","string","String",
        "List","Map","Dict","Set","Tuple","Vector","Array","Object","Class"
    ]])

    def _apply_unmarked(src: str, pattern, repl):
        out = []
        i = 0
        while i < len(src):
            start = src.find("\uFFF0", i)
            if start == -1:
                out.append(pattern.sub(repl, src[i:]))
                break
            out.append(pattern.sub(repl, src[i:start]))
            end = src.find("\uFFF1", start + 1)
            if end == -1:
                out.append(src[start:])
                break
            out.append(src[start:end + 1])
            i = end + 1
        return "".join(out)

    def _var_repl(m):
        name = m.group(1)
        if name in kw_set:
            return name
        if name.lower() in type_set:
            return name
        return f"\uFFF0V{name}\uFFF1"

    text = _apply_unmarked(text, var_pat, _var_repl)

    # 运算符与数字
    text = _apply_unmarked(text, call_pat, lambda m: f"\uFFF0F{m.group(1)}\uFFF1")
    text = _apply_unmarked(text, type_pat, lambda m: f"\uFFF0T{m.group(1)}\uFFF1")
    text = _apply_unmarked(text, op_pat, lambda m: f"\uFFF0O{m.group(0)}\uFFF1")
    text = _apply_unmarked(text, number_pat, lambda m: f"\uFFF0N{m.group(0)}\uFFF1")
    text = _apply_unmarked(text, bracket_pat, lambda m: f"\uFFF0B{m.group(0)}\uFFF1")

    # 先还原字符串与注释，避免标记被误替换
    for i, (kind, token_text) in enumerate(tokens):
        key = f"\uFFF2{chr(0xE000 + i)}\uFFF3"
        color = GREEN if kind == "str" else GREY
        text = text.replace(key, f"{color}{token_text}{RESET}")

    # 再替换高亮标记为颜色
    text = text.replace("\uFFF0K", BLUE).replace("\uFFF0N", CYAN).replace("\uFFF0O", Fore.LIGHTYELLOW_EX)
    text = text.replace("\uFFF0F", LIGHTGREEN).replace("\uFFF0T", LIGHTBLUE)
    text = text.replace("\uFFF0V", LIGHTCYAN).replace("\uFFF0B", LIGHTMAGENTA)
    text = text.replace("\uFFF0A", MAGENTA).replace("\uFFF0J", MAGENTA)
    text = text.replace("\uFFF0C", LIGHTRED)
    text = text.replace("\uFFF1", RESET)
    return text
