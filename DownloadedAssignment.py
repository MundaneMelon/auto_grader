class TestAssignment:
    pass


def add(a, b):  # Test multiple inputs -> one output
    return a + b


def switch(a, b):  # Test multiple inputs -> multiple outputs
    return b, a


def factorial(num):  # Test one input -> one output
    if num == 0:
        return 1
    return num * factorial(num - 1)


def print_twice(string):  # Test input -> printed output
    print(string)
    print(string)


def get_user_input():  # Test user input -> output
    string = str(input("Type something: "))
    return string


def check_from_file():  # Test reading print values from a file
    print("This is a test case.")
    print("This is another line.")


def check_all_types(user_name, order_cost, pay_type="cash", *args):  # Test everything, including combinations
    address = str(input("Enter address: "))
    if order_cost <= 0:
        return
    phone_number = int(input("Enter phone number: "))
    pizzas = []
    for arg in args:
        pizzas.append(arg + " pizza")
    print(f"User {user_name} has ordered: ")
    for pizza in pizzas:
        print(pizza)
    print(f"User address: {address}")
    print(f"User phone number: {phone_number}")
    print(f"Order cost: {order_cost}\nPaid with {pay_type}")
    print("-" * 30)
    return pizzas


def main():
    check_all_types("Joe", 15, "card", "Pepperoni")
    check_all_types("Susan", 25, "phone", "Pepperoni", "Cheese")
    check_all_types("Bob", 0, "", "check")


if __name__ == "__main__":
    main()
