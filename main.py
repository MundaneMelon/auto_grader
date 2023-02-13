from canvasapi import Canvas
import os
import json

"""
TO DO LIST

get all turned in assignments and test them indivdually
pull test function from config file with test cases
"""

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
    print("\nTesting config file: " + config_file)
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

    # get sumbissions and test them
    for submission in submissions:
        if submission.workflow_state == "submitted":
            # print("Testing submission: " + str(Canvas.get_user(canvas, 37434307).name))
            file = Canvas.get_file(canvas, submission.attachments[0])
            print(file.get_contents())
            test_submission(file, config)


def test_submission(file, config):
    pass


def main():
    config_files = get_config_files()

    for config_file in config_files:
        with open("configs/" + config_file) as f:
            config = json.load(f)
            try:
                get_submissions(config, config_file)
            except:
                print("Error loading config file: " + config_file)
                continue


if __name__ == "__main__":
    main()
