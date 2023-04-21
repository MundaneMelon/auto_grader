import time

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
    try:
        course = canvas.get_course(config["CANVAS"]["COURSE_ID"])
        assignment = course.get_assignment(config["CANVAS"]["ASSIGNMENT_ID"])
    except TypeError:
        print("Error: course and assignment ID not properly specified.")
        return
    except CanvasException as e:
        print("Error: ", e)
        return

    # check that the right number of points are possible
    points_possible = 0
    for test in config["TESTS"]:
        try:
            points_possible += test["POINTS"]
        except KeyError:
            print("Error: no points assigned to test. Defaulting to 0 points.")
    if points_possible != assignment.points_possible:
        print("Warning: total points possible does not match the assignment's value")
        print(f"    (Config includes {points_possible} points, "
              f"assignment is worth {assignment.points_possible} points)")

    submissions = assignment.get_submissions()

    # get submissions and test them
    submission_count = 0
    for submission in submissions:
        student_name = get_student_name(submission.user_id, course)
        submission_count += 1

        # SETTING TO ONLY GRADE CERTAIN STUDENTS (OVERRIDES EVERYTHING)
        try:
            only_grade_students = config["SETTINGS"]["ONLY_GRADE_STUDENTS"]
        except KeyError:
            only_grade_students = False
        if only_grade_students:
            if student_name not in config["SETTINGS"]["ONLY_GRADE_STUDENTS"]:
                print(f"{student_name} is not in the ONLY_GRADE_STUDENTS list... IGNORING")
                continue

        # SETTING TO IGNORE STUDENTS
        try:
            dont_grade_students = config["SETTINGS"]["DONT_GRADE_STUDENTS"]
        except KeyError:
            dont_grade_students = False
        if dont_grade_students:
            if student_name in config["SETTINGS"]["DONT_GRADE_STUDENTS"]:
                print(f"{student_name} is in the DONT_GRADE_STUDENTS list... IGNORING")
                continue

        # SETTING TO IGNORE ALREADY GRADED SUBMISSIONS
        try:
            ignore_already_graded = config["SETTINGS"]["IGNORE_ALREADY_GRADED"]
        except KeyError:
            ignore_already_graded = False
        if ignore_already_graded:
            if submission.workflow_state == "graded":
                print(f"{student_name} has already been graded... IGNORING")
                continue

        if submission.workflow_state == "submitted":
            attachment = Canvas.get_file(canvas, submission.attachments[0]).get_contents()
            file = open("DownloadedAssignment.py", "w")
            for line in attachment:
                file.write(line.rstrip('\r'))
            file.close()
            check_submission(submission, config, student_name)
        else:
            # SETTING TO GIVE 0 IF NOT SUBMITTED
            try:
                ignore_unsubmitted = config["SETTINGS"]["IGNORE_UNSUBMITTED"]
            except KeyError:
                ignore_unsubmitted = False
            if ignore_unsubmitted:
                print(f"{student_name} has not submitted the assignment yet... IGNORING")
            else:
                print(f"{student_name} has not submitted the assignment yet... GRADE SET TO 0")
                push_grade(submission, 0, student_name)
        progress_bar(submission_count, get_paginated_list_length(submissions))


def get_student_name(student_id, course):
    student = course.get_user(student_id)
    student_name = student.name
    return student_name


def check_submission(submission, config, student_name):
    total_score = 0
    for test in config["TESTS"]:
        if check_return(test):
            try:
                total_score += test["POINTS"]
            except KeyError:
                pass

    push_grade(submission, total_score, student_name)


def run_function(module_name, function_name, args, test):
    # dynamically import the module
    module = importlib.import_module(module_name)

    # dynamically get the function object and call it with the parameters
    my_function = getattr(module, function_name)
    result = None
    try:
        if test["OUTPUT_TYPE"] == "return":
            try:
                result = my_function(*args)
            except Exception as e:
                print(f"Submission throws error:", e)
                return None
        elif test["OUTPUT_TYPE"] == "print":
            # redirect the standard output to a variable
            output = io.StringIO()
            sys.stdout = output

            # call the function and get the result and output
            try:
                my_function(*args)
            except Exception as e:
                print(f"Submission throws error: ", e)
                return None

            result = output.getvalue()

            # restore the standard output
            sys.stdout = sys.__stdout__
        else:
            print("Error: output type not properly specified for test case.")

        return result

    except TypeError:
        print(f"Error: '{function_name}' expects {my_function.__code__.co_argcount} arguments,"
              f" but {len(args)} were given. Skipping test.")
        return False
    except KeyError:
        print("Error: output type not specified for test case. Skipping test.")
        return None


def check_return(test):
    passed = True
    try:
        function_name = test["FUNCTION_NAME"]
    except KeyError:
        print("Error: no function name specified for test case. Skipping test.")
        return False
    module_name = "DownloadedAssignment"

    try:
        length = len(test["INPUTS"])
    except KeyError:
        print("Error: no inputs specified for test case. Skipping test.")
        return False

    for i in range(length):
        try:
            result = run_function(module_name, function_name, test["INPUTS"][i], test)
        except AttributeError:
            print(f"Submission has no function {function_name}")
            return False
        if result is not None:
            try:
                expected_output = test["EXPECTED_OUTPUTS"][i]
            except KeyError:
                print("Error: output not specified for test case. Skipping test.")
                return False
            if result != expected_output:
                print(f"Function {function_name} with args {test['INPUTS'][i]} {test['OUTPUT_TYPE']}ed {result}, "
                      f"expecting {test['EXPECTED_OUTPUTS'][i]}")
                passed = False
        elif test["EXPECTED_OUTPUTS"][i] is not None:
            passed = False
    return passed


def push_grade(submission, score, student_name):
    try:
        # Update the submission score and comment
        submission.edit(submission={'score': score, 'comment': 'Your grade is ' + str(score)})

        # Print a message indicating success
        print(f"Grade of {score} pushed successfully for {student_name}")
    except CanvasException as e:
        print('Error:', e)


def get_paginated_list_length(paginated_list):
    # Paginated lists don't have a length attribute, so we have to count them manually
    count = 0
    for x in paginated_list:
        count += 1
    return count


def progress_bar(progress, total):
    progress_percent = progress / total
    progress_bar_length = 20  # Length of progress bar
    filled_length = int(progress_bar_length * progress_percent)
    bar = '▮' * filled_length + '-' * (progress_bar_length - filled_length)
    print(f'[{bar}] {int(progress_percent * 100)}%')


def main():
    config_files = get_config_files()
    if len(config_files) < 1:
        print("Error: No config files found."
              "Please make sure all config files end with .json and are located in the /configs folder.")

    for config_file in config_files:
        with open("configs/" + config_file) as f:
            try:
                config = json.load(f)
            except:
                print("Error: problem found with json file.")
                return

            get_submissions(config)


if __name__ == "__main__":
    main()
