from canvasapi import Canvas  # pip install canvasapi 
import os
import json
import math
import builtins
import shutil


# Canvas API URL
API_URL = "https://canvas.instructure.com/"
# Canvas API key
API_KEY = "7~XHBD7yRxf00NlUvfzjf6e5mRpmzm0vpLnWqP1geDCeAuGKmiCRehopSg2oejoBwY"

# Initialize a new Canvas object
canvas = Canvas(API_URL, API_KEY)

# Override standard input and print functions with mock functions for testing
mock_inputs = iter([])
mock_prints = []
old_in = builtins.input
old_out = builtins.print


def mock_input(prompt):
    print(prompt)
    try:
        return next(mock_inputs)
    except StopIteration:
        return ""


def mock_print(*objects, sep='', end='\n', file=None, flush=False):
    for obj in objects:
        objs = obj.split('\n')
        for item in objs:
            mock_prints.append(item.rstrip())


def get_config_files():
    files = []
    for file in os.listdir("configs"):
        if file.endswith(".json"):
            files.append(file)
    return files


def get_submissions(config, config_file):
    try:
        course = canvas.get_course(config["CANVAS"]["COURSE_ID"])
    except:
        print("Error getting course from config file: " + config_file)
        return
    try:
        assignment = course.get_assignment(config["CANVAS"]["ASSIGNMENT_ID"])
    except:
        print("Error getting assignment from config file: " + config_file)
        return

    submissions = assignment.get_submissions()

    # get submissions and test them
    submission_count = 0
    for submission in submissions:
        submission_count += 1
        if submission.workflow_state == "submitted":
            progress_bar(submission_count, get_paginated_list_length(submissions), submission.attachments[0])
            attachment = Canvas.get_file(canvas, submission.attachments[0]).get_contents()
            file = open("DownloadedAssignment.py", "w")  # TODO: add a proper name here for each file
            for line in attachment:
                file.write(line.rstrip('\r'))
            file.close()
            check_submission("DownloadedAssignment", config)
            shutil.move("DownloadedAssignment.py", "downloads/DownloadedAssignment.py")


def check_submission(file, config):
    total_score, max_score = 0, 0
    builtins.input = mock_input
    builtins.print = mock_print

    for test in config["TESTS"]:
        function = test["FUNCTION_NAME"]
        score = 0
        length = 1

        if "USER_INPUT" in test:
            global mock_inputs
            _mock_inputs = []
            # Unpack user input into a single stream
            for item in test["USER_INPUT"]:
                if type(item) is list:
                    for sub_item in item:
                        _mock_inputs.append(sub_item)
                else:
                    _mock_inputs.append(item)
            mock_inputs = iter(_mock_inputs)
            length = len(test["USER_INPUT"])

        if "INPUTS" in test:
            length = len(test["INPUTS"])

        for i in range(length):
            passes = True
            if "INPUTS" in test:
                try:
                    result = eval(f"submission.{function}(*{test['INPUTS'][i]})")
                except:
                    passes = False
                    break
            else:
                try:
                    result = eval(f"submission.{function}()")
                except:
                    passes = False
                    break

            if "PRINT" in test:
                expected_print = test["PRINT"][i]
                passes = (expected_print == mock_prints)
            elif "FILE_PRINT" in test:
                expected_prints = []
                if test["FILE_PRINT"][i] != "":
                    print_file = open(test["FILE_PRINT"][i])
                    for line in print_file:
                        expected_prints.append((line.rstrip('\r\n')))
                    print_file.close()
                    passes = (expected_prints == mock_prints)
            if "OUTPUTS" in test:
                if test["OUTPUTS"][i] != "None":
                    expected_output = test["OUTPUTS"][i]
                    if "OUTPUT_TYPE" in test:
                        expected_output = eval(f"{test['OUTPUT_TYPE']}(expected_output)")
                else:
                    expected_output = None
                passes = passes and (result == expected_output)
            if passes:
                score += test["POINTS"] / length
            mock_prints.clear()

        max_score += test["POINTS"]
        total_score += math.floor(score)

    builtins.input = old_in
    builtins.print = old_out

    print(f"Score: {total_score} out of {max_score}")


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
            try:
                get_submissions(config, config_file)
            except Exception as e:
                print("Error loading config file: " + config_file + "; skipping...")
                print(e)


if __name__ == "__main__":
    main()
