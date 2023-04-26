def factorial(n):
    return n * factorial(n - 1)  # Infinite loop


def remove_every_other_letter(n):
    if len(n) < 1:
        return ""
    return n[0] + remove_every_other_letter(n[2:])


def print_n_times(n, string):
    if n < 1:
        return
    print(string)
    return print_n_times(n + 1, string)  # Infinite loop


def recursive_addition(n):
    if n == 0:
        return 0
    return n + recursive_addition(n - 1)
