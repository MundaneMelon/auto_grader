from canvasapi import Canvas  # pip install canvasapi
from canvasapi.course import Course
from canvasapi.submission import Submission
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


def get_submissions(config: json) -> None:
    """
    Retrieves all submissions, runs them against test cases, and awards points to each student.\n
    :param config: the JSON file containing the configuration settings for the assignment, including the Canvas course and assignment ID.
    :return: nothing
    """
    try:
        course = canvas.get_course(config["CANVAS"]["COURSE_ID"])
        assignment = course.get_assignment(config["CANVAS"]["ASSIGNMENT_ID"])
    except TypeError:
        print("Error: course and assignment ID not properly specified.")
        return
    except CanvasException as e:
        print("Error: ", e)
        return

    # check that test cases are specified in the config file
    try:
        tests = config["TESTS"]
        if len(tests) < 1:
            print("Error: no test cases listed in config file.")
            return
    except KeyError:
        print("Error: no test cases specified in config file.")
        return

    # check that the right number of points are possible
    points_possible = 0
    total_points = assignment.points_possible
    for test in config["TESTS"]:
        try:
            points_possible += test["POINTS"]
        except KeyError:
            print("Error: no points assigned to test. Defaulting to 0 points.")
    if points_possible != total_points:
        print("Warning: total points possible does not match the assignment's value")
        print(f"    (Config includes {points_possible} points, "
              f"assignment is worth {total_points} points)")

    # SETTING TO ONLY GRADE CERTAIN STUDENTS (OVERRIDES EVERYTHING)
    try:
        only_grade_students = config["SETTINGS"]["ONLY_GRADE_STUDENTS"]
    except KeyError:
        only_grade_students = False

    # SETTING TO IGNORE STUDENTS
    try:
        dont_grade_students = config["SETTINGS"]["DONT_GRADE_STUDENTS"]
    except KeyError:
        dont_grade_students = False

    # SETTING TO REGRADE SPECIFIC STUDENTS
    try:
        regrade_students = config["SETTINGS"]["REGRADE_STUDENTS"]
    except KeyError:
        regrade_students = []

    # SETTING TO LEAVE COMMENTS ON SUBMISSIONS
    try:
        leave_comments = config["SETTINGS"]["LEAVE_COMMENTS"]
    except KeyError:
        leave_comments = True

    # SETTING TO DESCRIBE TEST CASES IN COMMENTS
    try:
        describe_test_cases = config["SETTINGS"]["DESCRIBE_TEST_CASES"]
    except KeyError:
        describe_test_cases = False

    # SETTING TO IGNORE ALREADY GRADED SUBMISSIONS
    try:
        ignore_already_graded = config["SETTINGS"]["IGNORE_ALREADY_GRADED"]
    except KeyError:
        ignore_already_graded = False

    submissions = assignment.get_submissions()

    # get submissions and test them
    submission_count = 0
    for submission in submissions:
        student_name = get_student_name(submission.user_id, course)
        submission_count += 1

        if only_grade_students:
            if student_name not in config["SETTINGS"]["ONLY_GRADE_STUDENTS"]:
                print(f"{student_name} is not in the ONLY_GRADE_STUDENTS list... IGNORING")
                continue

        if dont_grade_students:
            if student_name in config["SETTINGS"]["DONT_GRADE_STUDENTS"]:
                print(f"{student_name} is in the DONT_GRADE_STUDENTS list... IGNORING")
                continue

        if ignore_already_graded:
            if submission.workflow_state == "graded" and student_name not in regrade_students:
                print(f"{student_name} has already been graded... IGNORING")
                continue

        if submission.workflow_state == "submitted" or \
                (submission.workflow_state == "graded" and not ignore_already_graded):
            # progress_bar(submission_count, get_paginated_list_length(submissions), submission.attachments[0])
            try:
                attachment = Canvas.get_file(canvas, submission.attachments[0]).get_contents()
            except IndexError:  # Assignment has not been submitted yet
                try:
                    ignore_unsubmitted = config["SETTINGS"]["IGNORE_UNSUBMITTED"]
                except KeyError:
                    ignore_unsubmitted = False
                if ignore_unsubmitted:
                    print(
                        f"{student_name} has not submitted the assignment yet or has not submitted a NEW "
                        f"assignment... IGNORING")
                else:
                    print(
                        f"{student_name} has not submitted the assignment yet or has not submitted a NEW "
                        f"assignment... GRADE SET TO 0")
                    if leave_comments:
                        push_grade(submission, 0, student_name, f"Graded by Auto Grader. \nScore: 0 / {total_points}. "
                                                                f"\nDetails: No assignment submitted.")
                    else:
                        push_grade(submission, 0, student_name)
                continue
            file = open(f"{student_name}.py", "w")
            for line in attachment:
                file.write(line.rstrip('\r'))
            file.close()
            check_submission(submission, config, student_name, total_points, leave_comments, describe_test_cases)
            os.remove(f"{student_name}.py")
        else:
            # SETTING TO GIVE 0 IF NOT SUBMITTED
            try:
                ignore_unsubmitted = config["SETTINGS"]["IGNORE_UNSUBMITTED"]
            except KeyError:
                ignore_unsubmitted = False
            if ignore_unsubmitted:
                print(f"{student_name} has not submitted the assignment yet or has not submitted a NEW assignment... "
                      f"IGNORING")
            else:
                print(f"{student_name} has not submitted the assignment yet or has not submitted a NEW assignment... "
                      f"GRADE SET TO 0")
                if leave_comments:
                    push_grade(submission, 0, student_name, f"Graded by Auto Grader. \nScore: 0 / {total_points}. "
                                                            f"\nDetails: No assignment submitted.")
                else:
                    push_grade(submission, 0, student_name)


def get_student_name(student_id: int, course: Course) -> str:
    """
    Gets a students name from a Canvas course based on their ID.\n
    :param student_id: the student's ID
    :param course: the Canvas course
    :return: the name of the student
    """
    student = course.get_user(student_id)
    student_name = student.name
    return student_name


def check_submission(submission: Submission, config: json, student_name: str, total_points: float,
                     leave_comments: bool, describe_test_cases: bool) -> None:
    """
    Takes a student's submission, checks it against every test case, and awards points to the student
    based on which cases pass.\n
    :param submission: the submission to check
    :param config: the config file containing the test cases
    :param student_name: the name of the student to check
    :param total_points: the total number of points available for the assignment
    :param leave_comments: whether to leave comments for the student or not
    :param describe_test_cases: whether to provide detailed notes to the student on the test cases they failed
    :return: Nothing
    """
    total_score = 0
    test_case_count = len(config["TESTS"])
    passed_cases = 0
    results = ""

    for test in config["TESTS"]:
        result = check_return(test, student_name)
        if result != "":  # Test case did not pass
            results += result + '\n'
        else:  # Test case passed
            passed_cases += 1
            try:
                total_score += test["POINTS"]
            except KeyError:
                total_score += (total_points / total_score)

    comment = f"Graded by Auto Grader. \nScore: {total_score} / {total_points}. " \
              f"\nDetails: {passed_cases} of {test_case_count} test cases passed. "

    if describe_test_cases:
        if results != "":
            comment += "\n\n" + results

    if leave_comments:
        push_grade(submission, total_score, student_name, comment)
    else:
        push_grade(submission, total_score, student_name)


def run_function(module_name: str, function_name: str, args: list[any], test: json) -> any:
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
                raise e
        elif test["OUTPUT_TYPE"] == "print":
            # redirect the standard output.txt to a variable
            output = io.StringIO()
            sys.stdout = output

            # call the function and get the result and output.txt
            try:
                my_function(*args)
            except Exception as e:
                raise e

            result = output.getvalue()

            # restore the standard output.txt
            sys.stdout = sys.__stdout__
        else:
            print("Error: output.txt type not properly specified for test case.")

        return result

    except TypeError:
        raise TypeError(f"Function expects {my_function.__code__.co_argcount} arguments, "
                        f"but {len(args)} were given")
    except KeyError:
        print("Error: output.txt type not specified for test case. Skipping test.")
        return ""


def check_return(test: json, student_name: str) -> str:
    """
    Runs a set of tests on a student's downloaded submission.\n
    :param test: the set of tests to run.
    :param student_name: the name of the student.
    :return: A string detailing what mistakes or errors occurred. Returns an empty string if all tests pass.
    """
    try:
        function_name = test["FUNCTION_NAME"]
    except KeyError:
        print("Error: no function name specified for test case. Skipping test.")
        return ""
    try:
        length = len(test["INPUTS"])
    except KeyError:
        print("Error: no inputs specified for test case. Skipping test.")
        return ""

    passed = ""
    module_name = f"{student_name}"

    # Run each test
    for i in range(length):
        try:
            result = run_function(module_name, function_name, test["INPUTS"][i], test)
        except AttributeError:
            print(f"Submission has no function {function_name}.")
            return f"Submission has no function {function_name}."
        except TimeoutError:
            print(f"Function {function_name} with args {test['INPUTS'][i]} timed out.")
            return f"Function {function_name} with args {test['INPUTS'][i]} timed out."
        except Exception as e:
            print(f"Function {function_name} with args {test['INPUTS'][i]} throws exception: {e}.")
            return f"Function {function_name} with args {test['INPUTS'][i]} throws exception: {e}."
        if result is not None:
            try:
                expected_output = test["EXPECTED_OUTPUTS"][i]
            except KeyError:
                print("Error: output.txt not specified for test case. Skipping test.")
                return ""
            if result != expected_output:
                if type(result) == str:  # Make strings more readable
                    result = readable(result)
                    expected_output = readable(expected_output)
                print(f"Function {function_name} with args {test['INPUTS'][i]} {test['OUTPUT_TYPE']}ed {result}, "
                      f"expecting {expected_output}")
                passed += f"Function {function_name} with args {test['INPUTS'][i]} {test['OUTPUT_TYPE']}ed {result}, " \
                          f"expected {expected_output}. \n"
        elif test["EXPECTED_OUTPUTS"][i] is not None:
            passed += f"Function {function_name} with args {test['INPUTS'][i]} {test['OUTPUT_TYPE']}ed nothing, " \
                      f"expected {test['EXPECTED_OUTPUTS'][i]}. \n"
    return passed


def push_grade(submission: Submission, score: int | float, student_name: str, comment: str | None = None) -> None:
    """
    Pushes a student's grade for a particular assignment. Also leaves an optional comment with details.\n
    :param submission: The specific submission to grade
    :param score: The score the student earned on the assignment
    :param student_name: The student to grade
    :param comment: An optional comment, detailing why the student received that score
    :return: Nothing
    """
    try:
        if comment is None:
            # Update the submission score
            submission.edit(submission={'posted_grade': score})
        else:
            # Update the submission score and leave a comment
            submission.edit(submission={'posted_grade': score}, comment={'text_comment': comment})

        # Print a message indicating success
        print(f"Grade of {score} pushed successfully for {student_name}\n")
    except CanvasException as e:
        print('Error:', e)


def get_paginated_list_length(paginated_list: iter) -> int:
    """
    Returns the length of a paginated list. Paginated lists don't have a length attribute, so they
    have to be manually counted.\n
    :param paginated_list: the list to count
    :return: the length of the list
    """
    #
    count = 0
    for _ in paginated_list:
        count += 1
    return count


def readable(string: str) -> str:
    """
    Makes a string into a more clear and readable format.\n
    :param string: a string to modify
    :return: the modified string
    """
    return "\"" + string.replace("\n", "\\n ").replace("\t", "\\t ") + "\""


def main() -> None:
    config_files = get_config_files()
    if len(config_files) < 1:
        print("Error: No config files found."
              "Please make sure all config files end with .json and are located in the /configs folder.")

    for config_file in config_files:
        with open("configs/" + config_file) as f:
            try:
                config = json.load(f)
            except Exception as e:
                print(f"Error: problem found with json file: {e}")
                return

            get_submissions(config)


if __name__ == "__main__":
    main()
