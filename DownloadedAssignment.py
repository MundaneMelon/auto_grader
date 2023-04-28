def main():
    all_books = []
    all_ratings = {}
    with open("booklist.txt", "r") as booklist:
        for line in booklist:
            split = line.split(",")
            author, title = split[0], split[1]
            title = title.rstrip("\n")
            all_books.append((author, title))
    with open("ratings.txt", "r") as ratings:
        count = 0
        current_list = []
        for line in ratings:
            if count % 2 == 0:
                name = line
                name = name.lower()
                name = name.strip("\n")
                count += 1
                current_list.append(name)
            else:
                rates = line
                rates = rates.rstrip("\n")
                count += 1
                current_list.append(rates)
                all_ratings[current_list[0]] = current_list[1]
                current_list = []
    recommend_name = input("Enter a reader's name: ")
    if recommend_name in all_ratings:
        recommend(all_ratings, all_books, recommend_name)
    else:
        print(f"No such reader {recommend_name}")


def dotprod(x="", y=""):
    total = 0
    new_list = [int(i) for i in (x.split())]
    new_list2 = [int(j) for j in (y.split())]
    for j in range(len(new_list)):
        total += (new_list[j] * new_list2[j])
    return total


def friends(all_ratings={}, name=""):
    name_list = all_ratings[name]
    all_ratings.pop(name)
    current_max = 0
    current_max2 = 0
    max1_name = ""
    max2_name = ""
    for i in all_ratings:
        current_name = i
        current_list = all_ratings[i]
        current_num = dotprod(name_list, current_list)
        if current_num > current_max:
            current_max = current_num
            max1_name = current_name
        elif current_num > current_max2:
            current_max2 = current_num
            max2_name = current_name
    return max1_name + "," + max2_name


def recommend(all_ratings={}, all_books=[], name=""):
    the_list = all_ratings[name]
    new_the_list = [int(m) for m in (the_list.split())]
    x = friends(all_ratings, name)
    split, split1 = x.split(",")
    split = str(split)
    split1 = str(split1)
    list1 = all_ratings.get(split)
    list2 = all_ratings.get(split1)
    new_list1 = [int(j) for j in (list1.split())]
    new_list2 = [int(k) for k in (list2.split())]
    good_index1 = []
    good_index2 = []
    for i in range(len(new_list1) - 1):
        if new_the_list[i] == 0 and new_list1[i] >= 3:
            good_index1.append(i)
    for k in range(len(new_list2) - 1):
        if new_the_list[k] == 0 and new_list2[k] >= 3:
            good_index2.append(k)
    for m in range(len(good_index1) - 1):
        for n in range(len(good_index2) - 1):
            if good_index1[m] == good_index2[n]:
                good_index2.pop(n)
    all_indexes = good_index1 + good_index2
    sort = [split, split1]
    sort = sorted(sort)
    print(f"Recommendations for {name} from {sort[0]} and {sort[1]}")
    for r in all_indexes:
        string = str(all_books[r])
        string = string[2:-2]
        x = string.index(",")
        string = string[:x-1] + ", " + string[x+3:]
        print("      " + string)


main()