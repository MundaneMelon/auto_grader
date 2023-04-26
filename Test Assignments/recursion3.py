def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)


def remove_every_other_letter(n):
    if len(n) < 1:
        return ""
    return n[0] + remove_every_other_letter(n[2:])


def print_n_times(n, string):  # BROKEN
    if n < 1:
        return
    return print_n_times(n - 1, string)


def recursive_addition(n):
    if n == 0:
        return 0
    return 1 + recursive_addition(n - 1)
