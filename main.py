from canvasapi import Canvas  # pip install canvasapi 
import os
import json
import importlib

# Canvas API URL
API_URL = "https://canvas.instructure.com/"
# Canvas API key
API_KEY = "7~XHBD7yRxf00NlUvfzjf6e5mRpmzm0vpLnWqP1geDCeAuGKmiCRehopSg2oejoBwY"

# Initialize a new Canvas object
canvas = Canvas(API_URL, API_KEY)

def get_config_files():
    files = []
    for file in os.listdir("configs"):
        if file.endswith(".json"):
            files.append(file)
    return files


def get_submissions(config, config_file):
    course = canvas.get_course(config["CANVAS"]["COURSE_ID"])
    assignment = course.get_assignment(config["CANVAS"]["ASSIGNMENT_ID"])


    submissions = assignment.get_submissions()

    # get submissions and test them
    submission_count = 0
    for submission in submissions:
        submission_count += 1
        if submission.workflow_state == "submitted":
            # progress_bar(submission_count, get_paginated_list_length(submissions), submission.attachments[0])
            attachment = Canvas.get_file(canvas, submission.attachments[0]).get_contents()
            file = open("DownloadedAssignment.py", "w")
            for line in attachment:
                file.write(line.rstrip('\r'))
            file.close()

            check_submission(submission, config)


def check_submission(submission, config):
    for test in config["TESTS"]:
        if test["OUTPUT_TYPE"] == "print":
            check_print(test)
        elif test["OUTPUT_TYPE"] == "return":
            check_return(test, submission)


def run_function(module_name, function_name, args):
    # dynamically import the module
    module = importlib.import_module(module_name)

    # dynamically get the function object and call it with the parameters
    try:
        my_function = getattr(module, function_name)
        return my_function(*args)
    except TypeError:
        print(f"Error: '{function_name}' expects {my_function.__code__.co_argcount} arguments, but {len(args)} were given.")
        return None


def check_print(test):
    pass


def check_return(test, submission):
    function_name = test["FUNCTION_NAME"]
    module_name = "DownloadedAssignment"
    for params in test["INPUTS"]:
        result = run_function(module_name, function_name, params)
        if result is not None:
            print(f"Testing function '{function_name}' with parameters {params}...")
            print(f"The result of the function call is: {result} \n")


def push_grade():
    pass


def get_paginated_list_length(paginated_list):
    # Paginated lists don't have a length attribute, so we have to count them manually
    count = 0
    for x in paginated_list:
        count += 1
    return count


def progress_bar(progress, total, text):
    percent = 100 * (progress / float(total))
    bar = "▮" * int(percent) + "-" * (100 - int(percent))
    print(f"\r|{bar}| {percent:.2f}% {text}", end="\r")


def main():
    config_files = get_config_files()

    for config_file in config_files:
        with open("configs/" + config_file) as f:
            config = json.load(f)

            get_submissions(config, config_file)


if __name__ == "__main__":
    main()
