# One time script to import the tab-delimited legacy file from excel version of timekeeping
import os
import c_TKDB
import datetime
import pickle
from sqlalchemy.orm import sessionmaker

# Change directory
os.chdir("F:/USRA/WorkTools/venv/Files/")

# Project id
# project_id = 0
# # Task id
# task_id = 0
# # Tag id
# tag_id = 0

# Project dictionary
project_dict = {}
# Task dictionary
task_dict = {}
# Tag dictionary
tag_dict = {}

# Create an engine instance for the database
engine = c_TKDB.create_engine('postgresql+psycopg2://tk_timekeeper:tk_timekeeper_password@localhost:5432/timekeeper')
# Bind this engine to the Session class
Session = sessionmaker(bind=engine)
# Create a session
sessionOne = Session()

# Open the tab-delimited file of legacy records
with open(f"{os.getcwd()}/TKLegacyData.txt", 'r') as f:
    # First line
    first_line = True
    # For each line
    for line in f:
        # If first line
        if first_line is True:
            # Switch it off
            first_line = False
            # Skip the line
            continue
        # Split on tabs
        split_line = line.split('\t')
        # Check the length of the line
        if len(split_line) != 14:
            # Print warning
            print(f"Following line is funky (not 14 fields).")
            print(split_line)
            # Exit the code
            exit()
        # Make a datetime object
        currDT = datetime.datetime.strptime(f"{split_line[0]}-{split_line[1]}", "%m/%d/%Y-%H:%M")
        # If there is a project with the ID in the TK projects
        if split_line[5] in project_dict.keys():
            # Reference the project
            currProject = project_dict[split_line[5]][0]
            # If there is a task in the project
            if split_line[7] in project_dict[split_line[5]][1].keys():
                # Reference the task
                currTask = project_dict[split_line[5]][1][split_line[7]]
            # Otherwise (new task needed)
            else:
                # Make a new task
                currTask = c_TKDB.Task(project_id=currProject.id,
                                       name=split_line[7],
                                       datetime=currDT.strftime("%Y-%m-%d %H:%M:00"))
                # Add to the dictionary
                project_dict[currProject.name][1][currTask.name] = currTask
                # Add to the session
                sessionOne.add(currTask)
        # Otherwise (no project)
        else:
            # Make a new project
            currProject = c_TKDB.Project(name=split_line[5],
                                         datetime=currDT.strftime("%Y-%m-%d %H:%M:00"))
            # Add to the session
            sessionOne.add(currProject)
            # Flush to secure id
            sessionOne.flush()
            # Add to the dictionary
            project_dict[currProject.name] = [currProject, {}]
            # Make a new task
            currTask = c_TKDB.Task(project_id=currProject.id,
                                   name=split_line[7].strip('"'),
                                   datetime=currDT.strftime("%Y-%m-%d %H:%M:00"))
            # Add to the dictionary
            project_dict[currProject.name][1][currTask.name] = currTask
            # Add to the DB
            sessionOne.add(currTask)
        # Form an datetime object for the effort endtime
        effort_end = datetime.datetime.strptime(f"{split_line[0]}-{split_line[2]}", "%m/%d/%Y-%H:%M")
        # Make a new Effort
        currEffort = c_TKDB.Effort(start_time=currDT.strftime("%Y-%m-%d %H:%M:00"),
                                   project_id=currProject.id,
                                   task_id=currTask.id,
                                   end_time=effort_end.strftime("%Y-%m-%d %H:%M:00"),
                                   description=split_line[13].strip('"'))
        # Add to the session
        sessionOne.add(currEffort)
        # For each tag
        for tag in split_line[12].split(','):
            # Strip any remaining quotes and spaces from the tag
            tag = tag.strip('"')
            tag = tag.strip()
            # If the tag is in the dictionary
            if tag in tag_dict.keys():
                # Reference the tag
                currTag = tag_dict[tag]
            # Otherwise (new tag needed)
            else:
                # Make new tag object
                currTag = c_TKDB.Tag(name=tag)
                # Add to dictionary
                tag_dict[currTag.name] = currTag
                # Add to the session
                sessionOne.add(currTag)
            # Reference in the effort (this will populate the tag_effort many to many)
            currEffort.tags.append(currTag)

sessionOne.commit()
sessionOne.close()