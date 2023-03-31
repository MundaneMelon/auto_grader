from canvasapi import Canvas  # pip install canvasapi 
from canvasapi.exceptions import CanvasException
import os
import io
import sys
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


def get_submissions(config):
    course = canvas.get_course(config["CANVAS"]["COURSE_ID"])
    assignment = course.get_assignment(config["CANVAS"]["ASSIGNMENT_ID"])


    submissions = assignment.get_submissions()

    # get submissions and test them
    submission_count = 0
    for submission in submissions:
        student_name = get_student_name(submission.user_id, course)
        submission_count += 1

        # SETTING TO ONLY GRADE CERTAIN STUDENTS (OVERRIDES EVERYTHING)
        if config["SETTINGS"]["ONLY_GRADE_STUDENTS"] != []:
            if student_name not in config["SETTINGS"]["ONLY_GRADE_STUDENTS"]:
                print(f"{student_name} is not in the ONLY_GRADE_STUDENTS list... IGNORING")
                continue

        # SETTING TO IGNORE STUDENTS
        if config["SETTINGS"]["DONT_GRADE_STUDENTS"] != []:
            if student_name in config["SETTINGS"]["DONT_GRADE_STUDENTS"]:
                print(f"{student_name} is in the DONT_GRADE_STUDENTS list... IGNORING")
                continue

        # SETTING TO IGNORE ALREADY GRADED SUBMISSIONS
        if config["SETTINGS"]["IGNORE_ALREADY_GRADED"]:
            if submission.workflow_state == "graded":
                print(f"{student_name} has already been graded... IGNORING")
                continue
            

        if submission.workflow_state == "submitted":
            # progress_bar(submission_count, get_paginated_list_length(submissions), submission.attachments[0])
            attachment = Canvas.get_file(canvas, submission.attachments[0]).get_contents()
            file = open("DownloadedAssignment.py", "w")
            for line in attachment:
                file.write(line.rstrip('\r'))
            file.close()
            check_submission(submission, config, student_name)
        else:
            # SETTING TO GIVE 0 IF NOT SUBMITTED
            if config["SETTINGS"]["IGNORE_UNSUBMITTED"]:
                print(f"{student_name} has not submitted the assignment yet... IGNORING")
            else:
                print(f"{student_name} has not submitted the assignment yet... GRADE SET TO 0")
                push_grade(submission, 0, student_name)


def get_student_name(student_id, course):
        student = course.get_user(student_id)
        student_name = student.name
        return student_name


def check_submission(submission, config, student_name):
    total_score = 0
    for test in config["TESTS"]:
        if check_return(test):
            total_score += test["POINTS"]
    
    push_grade(submission, total_score, student_name)


def run_function(module_name, function_name, args, test):
    # dynamically import the module
    module = importlib.import_module(module_name)

    # dynamically get the function object and call it with the parameters
    try:
        my_function = getattr(module, function_name)

        if test["OUTPUT_TYPE"] == "return":
            result = my_function(*args)
        elif test["OUTPUT_TYPE"] == "print":
            # redirect the standard output to a variable
            output = io.StringIO()
            sys.stdout = output

            # call the function and get the result and output
            my_function(*args)
            result = output.getvalue()

            # restore the standard output
            sys.stdout = sys.__stdout__

        return result
        
    except TypeError:
        print(f"Error: '{function_name}' expects {my_function.__code__.co_argcount} arguments, but {len(args)} were given.")
        return None
    

def check_return(test):
    passed = True
    function_name = test["FUNCTION_NAME"]
    module_name = "DownloadedAssignment"
    for i in range(len(test["INPUTS"])):
        result = run_function(module_name, function_name, test["INPUTS"][i], test)
        if result is not None:
            if result != test["EXPECTED_OUTPUTS"][i]:
                passed = False

    return passed
    
                
def push_grade(submission, score, student_name):
    try:
        # Update the submission score and comment
        submission.edit(submission={'score': score, 'comment': 'Your grade is ' + str(score)})
        
        # Print a message indicating success
        print('Grade pushed successfully for', student_name)
    except CanvasException as e:
        print('Error:', e)


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

            get_submissions(config)


if __name__ == "__main__":
    main()
