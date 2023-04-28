def Factorial(n):  # Capitalized
    if n == 0:
        return 1
    return n * Factorial(n - 1)


def Remove_Every_Other_Letter(n):  # Capitalized
    if len(n) < 1:
        return ""
    return n[0] + Remove_Every_Other_Letter(n[2:])


def Print_N_Times(n, string):  # Capitalized
    if n < 1:
        return
    print(string)
    return Print_N_Times(n - 1, string)


def Recursive_Addition(n):  # Capitalized
    if n == 0:
        return 0
    return 1 + Recursive_Addition(n - 1)
