def hello_name(name=""):
    return "Hello " + "!"


def make_abba(a="", b=""):
    return a + b + a


def make_tags(tag="", string=""):
    return f"<{tag}>{string}<{tag}>"


def make_out_word(brackets="", word=""):
    for i in range(len(brackets)):
        if brackets[i] == ">" or brackets[i] == "}" or brackets[i] == "]":
            brackets = brackets[:i] + word + brackets[i:]
            return brackets


def extra_end(string=""):
    return string[len(string) - 2:] * 2
