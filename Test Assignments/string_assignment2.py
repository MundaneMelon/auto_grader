def hello_name(name=""):
    return "Hello " + "!"


def make_tags(tag="", string=""):
    return f"<{tag}>{string}<{tag}>"


def make_out_word(brackets="", word=""):
    for i in range(len(brackets)):
        if brackets[i] == ">":
            brackets = brackets[:i] + word + brackets[i:]
            return brackets
