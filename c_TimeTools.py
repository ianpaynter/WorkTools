import datetime
import random
import string
import numpy as np

class Manager:

    def __init__(self):

        pass

class Timesheet:

    def __init__(self):

        self.dates = {}


class Task:

    def __init__(self, name, description=None):

        self.efforts = []
        self.name = name
        self.description = description

    # Record
    def addTime(self, hours=None, minutes=None, now=True):
        # If no duration was entered
        if hours is None and minutes is None:
            # Print warning
            print("Warning: No duration was entered for this effort. Include hours= and/or minutes= in addTime() call.")
            # Exit without further action
            return
        # Create effort object
        newEffort = Effort(self)
        # If now was the time to log the effort
        if now is True:
            # Set time in the effort to now
            newEffort.time = datetime.datetime.now()

class Effort:

    def __init__(self, task):

        self.task = None
        self.time = None


# Record
def addTime(task, hours=None, minutes=None, now=True):
    # If no duration was entered
    if hours is None and minutes is None:
        # Print warning
        print("Warning: No duration was entered for this effort. Include hours= and/or minutes= in addTime() call.")
        # Exit without further action
        return
    # Create effort object
    newEffort = Effort(task)
    # If now was the time to log the effort
    if now is True:
        # Set time in the effort to now
        newEffort.time = datetime.datetime.now()

def generateProjectID(existing=None):

    project_id = ''

    while len(project_id) < 6:
        project_id += (random.choice([random.choice(string.ascii_uppercase), str(random.randint(0, 9))]))

    print(project_id)

generateProjectID()

def generateTaskID(existing=None):

    project_id = ''

    while len(project_id) < 4:
        project_id += (random.choice([random.choice(string.ascii_uppercase), str(random.randint(0, 9))]))

    print(project_id)

generateProjectID()
generateTaskID()