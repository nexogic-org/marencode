import re
from colorama import Style, Fore

class InlineStyler:
    def __init__(self):
        # 是否处于加粗状态
        self.bold_open = False
        # 是否处于标题样式
        self.heading_open = False
        # 是否在行首，用于识别列表符号
        self.line_start = True
        # 处理 ** 被拆分的情况
        self.star_hold = ""
        # 处理 ` 被拆分的情况
        self.backtick_hold = ""
        # 是否处于行内代码状态
        self.inline_code = False
        # 处理 __ 被拆分的情况
        self.underline_hold = ""
        # 是否处于下划线强调
        self.underline_open = False

    def feed(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'[\uFFF0-\uFFF3]', '', text)
        text = re.sub(r'[\uE000-\uF8FF]', '', text)
        text = self.star_hold + self.backtick_hold + self.underline_hold + text
        self.star_hold = ""
        self.backtick_hold = ""
        self.underline_hold = ""
        output = []
        i = 0
        while i < len(text):
            if self.line_start and text[i] == "#":
                j = i
                count = 0
                while j < len(text) and text[j] == "#":
                    count += 1
                    j += 1
                
                if j < len(text) and text[j].isspace():
                    # 不同的 # 数量使用不同的颜色和前缀
                    prefix_char = ""
                    if count == 1:
                        color = Style.BRIGHT + Fore.LIGHTMAGENTA_EX
                        prefix_char = "▍ "
                    elif count == 2:
                        color = Style.BRIGHT + Fore.LIGHTBLUE_EX
                        prefix_char = "## "
                    elif count == 3:
                        color = Style.BRIGHT + Fore.CYAN
                        prefix_char = "### "
                    elif count == 4:
                        color = Style.BRIGHT + Fore.GREEN
                        prefix_char = "#### "
                    elif count == 5:
                        color = Style.BRIGHT + Fore.YELLOW
                        prefix_char = "##### "
                    elif count == 6:
                        color = Style.BRIGHT + Fore.LIGHTRED_EX
                        prefix_char = "###### "
                    else:
                        color = Style.BRIGHT + Fore.WHITE
                        prefix_char = "#" * count + " "
                        
                    output.append(color + prefix_char)
                    self.heading_open = True
                    # 跳过 # 后的空格
                    k = j
                    while k < len(text) and text[k].isspace() and text[k] != "\n":
                        k += 1
                    i = k
                    continue
            if text[i] == "`":
                if i + 1 == len(text):
                    self.backtick_hold = "`"
                    break
                self.inline_code = not self.inline_code
                output.append(Style.BRIGHT if self.inline_code else Style.NORMAL)
                i += 1
                continue
            if text[i] == "_" and i + 1 < len(text) and text[i + 1] == "_":
                self.underline_open = not self.underline_open
                output.append(Style.DIM if self.underline_open else Style.NORMAL)
                i += 2
                continue
            if text[i] == "_" and i + 1 == len(text):
                self.underline_hold = "_"
                break
            if text[i] == "*" and i + 1 < len(text) and text[i + 1] == "*":
                self.bold_open = not self.bold_open
                output.append(Style.BRIGHT if self.bold_open else Style.NORMAL)
                i += 2
                continue
            if text[i] == "*" and i + 1 == len(text):
                self.star_hold = "*"
                break
            if self.inline_code:
                output.append(text[i])
                self.line_start = (text[i] == "\n")
                i += 1
                continue
            if self.line_start and text[i] == "-":
                j = i
                while j < len(text) and text[j] in "- ":
                    if text[j] == "\n":
                        break
                    j += 1
                line_seg = text[i:j]
                dash_count = line_seg.count("-")
                if line_seg.strip("- ") == "" and dash_count >= 3:
                    output.append("─" * 48)
                    self.line_start = True
                    i = j
                    continue
                # 处理列表项符号 "-"，渲染为带颜色的圆点
                if i + 1 < len(text) and text[i+1].isspace():
                    output.append(f"{Style.BRIGHT}{Fore.LIGHTGREEN_EX}•{Style.RESET_ALL} ")
                    # 跳过后续的一个或多个空格
                    k = i + 1
                    while k < len(text) and text[k].isspace() and text[k] != "\n":
                        k += 1
                    i = k
                    self.line_start = False
                    continue
            
            if text[i] == "\n":
                if self.heading_open:
                    output.append(Style.NORMAL)
                    self.heading_open = False
                if self.underline_open:
                    output.append(Style.NORMAL)
                    self.underline_open = False
                if self.bold_open:
                    output.append(Style.NORMAL)
                    self.bold_open = False
                output.append("\n")
                self.line_start = True
                i += 1
                continue
            if self.heading_open and text[i] == "\n":
                output.append(Style.NORMAL)
                self.heading_open = False
                self.line_start = True
                i += 1
                continue
            if self.line_start:
                if text[i].isspace() and text[i] != "\n":
                    output.append(text[i])
                    i += 1
                    continue
                # 删除这一段重复的 "-" 处理逻辑，因为上面已经处理过了
                # if text[i] == "-" and (i + 1 < len(text) and text[i + 1].isspace()):
                #     output.append("· ")
                #     ...
            ch = text[i]
            output.append(ch)
            self.line_start = (ch == "\n")
            i += 1
        return "".join(output)

    def finalize(self) -> str:
        output = []
        if self.star_hold:
            output.append(self.star_hold)
            self.star_hold = ""
        if self.backtick_hold:
            output.append(self.backtick_hold)
            self.backtick_hold = ""
        if self.inline_code:
            output.append(Style.NORMAL)
            self.inline_code = False
        if self.bold_open:
            output.append(Style.NORMAL)
            self.bold_open = False
        if self.underline_open:
            output.append(Style.NORMAL)
            self.underline_open = False
        if self.heading_open:
            output.append(Style.NORMAL)
            self.heading_open = False
        return "".join(output)
