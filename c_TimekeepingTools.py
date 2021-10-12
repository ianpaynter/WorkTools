import random
import numpy as np
from datetime import datetime
import os
import pickle
import string


class Timekeeper:

    def __init__(self):

        self.projects = {}

    def getProjectIDs(self):
        # Return the project IDs as a set of keys
        return self.projects.keys()

    def addProject(self, project_id=None, project_name=None):
        # If the project has a specified ID
        if project_id is not None:
            # Check if the project id already exists
            if project_id in self.getProjectIDs():
                # Reference the project and return it
                return self.projects[project_id]
            # Otherwise
            else:
                # Create a new project
                currProject = Project(self, name=project_name)
                # File the project under its ID
                self.projects[currProject.id] = currProject
                # Return it
                return currProject

    def get_new_project_id(self):
        # Unique id switch
        unique_id = False
        # While the ID is not unique
        while unique_id is False:
            project_id = ''
            while len(project_id) < 6:
                project_id += (random.choice([random.choice(string.ascii_uppercase), str(random.randint(0, 9))]))
            # If the project id is not the id keys
            if project_id not in self.getProjectIDs():
                # Switch to unique
                unique_id = True
        # Return the project id
        return project_id


class Feeling:

    def __init__(self, feeling_type, feeling_intensity):

        self.creation_date = datetime.now()
        self.feeling_type = feeling_type
        self.feeling_intensity = feeling_intensity

class Project:

    def __init__(self, timekeeper, name=None, project_id=None):

        self.timekeeper = timekeeper
        self.creation_date = datetime.now()
        self.id = project_id
        self.name = name
        self.tasks = {}

    def get_task_names(self):
        # Task name list
        task_names = []
        # For each task
        for task in self.tasks:
            # Append name to task list
            pass

class Task:

    def __init__(self, project, name=None, task_id=None):

        self.project = project
        self.timekeeper = project.timekeeper
        self.creation_date = None
        self.id = task_id
        self.name = name
        self.instigators = []
        self.originator = None
        self.efforts = []
        self.tags = []
        self.feelings = []

class Person:

  def __init__(self):

    self.name = None
    self.id = None
    self.tasks = []
    self.projects = []

class Effort:

    def __init__(self, task):

        self.project = task.project
        self.task = task
        self.timekeeper = task.project.timekeeper
        self.date = None
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.notes = None
        self.instigator = None
        self.instigation = None

class Interruption:

    def __init__(self, interrupted_task, interrupting_task):

        self.interrupted_task = interrupted_task
        self.interrupting_task = interrupting_task
        self.datetime = datetime.now()


# Check if there is a pickled TimeKeeper in the Files directory
def checkForSavedTK():
  # Change working directory to the Files directory
  os.chdir("F:/USRA/WorkTools/venv/Files/")
  # If there is a saved timekeeper file in the Files
  if os.path.exists(f"{os.getcwd()}TKPickle"):
    # Return true
    return True
  # Otherwise (no saved TK)
  else:
    # Return False
    return False


def main():
  # If there is a pickled TK
  if checkForSavedTK() is True:
    # Open it and unpickle
    currTK = pickle.load(open(f"{os.getcwd()}TKPickle", 'rb'))
  # Otherwise (no pickled TK)
  else:
    # Create a new TK object
    currTK = Timekeeper()


if __name__ == "__main__":

  main()