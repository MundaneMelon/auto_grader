def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)


# MISSING remove_every_other_letter


def print_n_times(n, string):
    if n < 1:
        return
    print(string)
    return print_n_times(n - 1, string)


def recursive_addition(n):
    if n == 0:
        return 0
    return 1 + recursive_addition(n - 1)
