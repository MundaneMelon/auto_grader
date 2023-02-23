class TestAssignment:
    pass


def add(a, b):
    return a + b


def switch(a, b):
    return b, a


def factorial(num):
    if num == 0:
        return 1
    return num * factorial(num - 1)


def print_twice(string):
    print(string)
    print(string)


def get_user_input():
    string = str(input("Type something: "))
    return string


def test_from_file():
    print("This is a test case.")
