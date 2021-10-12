import PySimpleGUI
import PySimpleGUI as sg
import datetime
from sqlalchemy.orm import sessionmaker
import c_TKDB

# Create an engine instance for the database
engine = c_TKDB.create_engine('postgresql+psycopg2://tk_timekeeper:tk_timekeeper_password@localhost:5432/timekeeper')
# Bind this engine to the Session class
Session = sessionmaker(bind=engine)
# Create a session
sessionOne = Session()

# Class
class tk_ref_holder:

    def __init__(self):

        self.curr_project = None
        self.curr_task = None
        self.ongoing_effort = None
        self.prev_effort = None
        self.prospective_project = None
        self.prospective_task = None

# Function borrowed from PSG dev.
def place(elem):
    '''
    Places element provided into a Column element so that its placement in the layout is retained.
    :param elem: the element to put into the layout
    :return: A column element containing the provided element
    '''
    return sg.Column([[elem]], pad=(0, 0))


def make_invisible(current_window, elements):
    if isinstance(elements, list) is False:
        elements = [elements]
    for element in elements:
        current_window.Element(element).Update(visible=False)


def make_visible(current_window, elements):
    if isinstance(elements, list) is False:
        elements = [elements]
    for element in elements:
        current_window.Element(element).Update(visible=True)


def enable(current_window, elements):
    if isinstance(elements, list) is False:
        elements = [elements]
    for element in elements:
        current_window.Element(element).Update(disabled=False)


def disable(current_window, elements):
    if isinstance(elements, list) is False:
        elements = [elements]
    for element in elements:
        current_window.Element(element).Update(disabled=True)


# Start a new task
def start_task_window(main_window, currRefs):

    start_task_layout = [

        [sg.Text('Select project',
                 size=(11, 1),
                 key="-T_PROJ_SEL-"),
         sg.Combo(sorted([proj.name for proj in sessionOne.query(c_TKDB.Project).with_entities(c_TKDB.Project.name)]),
                  size=(50, 1),
                  enable_events=True,
                  key="-C_PROJ_SEL-"),
         sg.Button('New Project',
                   key="-B_NEW_PROJ-"),
         place(sg.Text('Type Name:',
                       key="-T_NEW_PROJ_NAME-",
                       visible=False)),
         place(sg.InputText(size=(40, 1),
                            key="-I_NEW_PROJ_NAME-",
                            visible=False))],

        [sg.Text('Select task',
                 size=(11, 1),
                 key="-T_TASK_SEL-"),
         sg.Combo([],
                  size=(50, 1),
                  enable_events=True,
                  key="-C_TASK_SEL-",
                  disabled=True),
         sg.Button('New Task',
                   key="-B_NEW_TASK-",
                   disabled=True),
         place(sg.Text('Type Name:',
                       key="-T_NEW_TASK_NAME-",
                       visible=False)),
         place(sg.InputText(size=(40, 1),
                            key="I_NEW_TASK_NAME",
                            visible=False))],

        [sg.Button('Confirm', key="-B_CONFIRM-", button_color="black on lime green", disabled=True),
         sg.Button('Cancel', key="-B_CANCEL-", button_color="black on light coral")]

    ]

    # If there is a current task
    if main_window["-B_START_SWITCH_TASK-"].ButtonText == "Switch Task":
        # Add interrupt checkbox to beginning
        start_task_layout.insert(0, [sg.Checkbox("This is an unexpected interruption to current task.",
                                                 default=False,
                                                 key="-CB_INTERRUPTION-")])

    # Make a new window
    task_window = sg.Window("Start Task", start_task_layout, modal=True)

    # Start listening loop for new window
    while True:
        event, values = task_window.read()
        if event == "Exit" or event == sg.WIN_CLOSED or event == "-B_CANCEL-":
            # Clear the prospective project and task
            currRefs.prospective_project = None
            currRefs.prospective_task = None
            # Roll back any changes (new projects/tasks) without committing
            sessionOne.rollback()
            # Close the window
            task_window.close()
            break
        # If the event is a "new project" button press
        elif event == "-B_NEW_PROJ-":
            # Clear any tasks from a previously selected project
            task_window['-C_TASK_SEL-'].update(values=[])
            # Disable confirm button
            disable(task_window, "-B_CONFIRM-")
            # New project window
            start_new_proj_window(task_window, currRefs)
        # If the event is an update to the project name field
        elif event == "-C_PROJ_SEL-":
            # If the length of the proj name is greater than 0
            if len(values["-C_PROJ_SEL-"]) > 0:
                # Enable the task select and new task button
                enable(task_window, ["-C_TASK_SEL-", "-B_NEW_TASK-"])
                # Get the project object from the database and set as prospective project
                currRefs.prospective_project = sessionOne.query(c_TKDB.Project).filter(c_TKDB.Project.name == values["-C_PROJ_SEL-"]).first()
                # Get the task names for the project from the database
                taskNames = sorted([task.name for task in sessionOne.query(c_TKDB.Task).join(c_TKDB.Project).filter(c_TKDB.Project.name == values["-C_PROJ_SEL-"])])
                print(taskNames)
                # Update the task select with the tasks from the project, setting the first as the current value
                task_window['-C_TASK_SEL-'].update(values=taskNames, value=taskNames[0])
                # Get the task object from the database and set as current task
                currRefs.prospective_task = sessionOne.query(c_TKDB.Task).filter(
                    c_TKDB.Task.name == taskNames[0]).filter(c_TKDB.Task.project_id == currRefs.prospective_project.id).first()
                # Make the confirm button available
                enable(task_window, "-B_CONFIRM-")
        # If the event is a task selection
        elif event == "-C_TASK_SEL-":
            # Get the task object from the database and set as current task
            currRefs.prospective_task = sessionOne.query(c_TKDB.Task).filter(
                c_TKDB.Task.name == values["-C_TASK_SEL-"]).filter(
                c_TKDB.Task.project_id == currRefs.prospective_project.id).first()
            # Enable the confirm button
            enable(task_window, "-B_CONFIRM-")
        # If the event is a "new task" button press
        elif event == "-B_NEW_TASK-":
            # New task window
            start_new_task_window(task_window, currRefs)
        # If the event is a "confirm" button press
        elif event == "-B_CONFIRM-":
            # If there is an ongoing effort
            if currRefs.ongoing_effort is not None:
                # Give it an end time
                currRefs.ongoing_effort.end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Flush to get IDs for new projects/tasks
            sessionOne.flush()
            # Make an Effort object
            newEffort = c_TKDB.Effort(project_id=currRefs.prospective_project.id,
                                      task_id=currRefs.prospective_task.id,
                                      start_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            # Add to session
            sessionOne.add(newEffort)
            # If there is an ongoing effort
            if currRefs.ongoing_effort is not None:
                # If the interruption box is set to true
                if values["-CB_INTERRUPTION-"] is True:
                    # Create an Interruption in the effort
                    newEffort.interruptees.append(currRefs.ongoing_effort)
            # Reference new effort as the ongoing effort
            currRefs.ongoing_effort = newEffort
            # Commit any new projects/tasks to the database
            sessionOne.commit()
            # Retrieve project and task
            taskName = values["-C_TASK_SEL-"]
            projName = values["-C_PROJ_SEL-"]
            # Push the project and task to the main window
            main_window.Element("-TASK-").Update(f"{taskName}")
            main_window.Element("-PROJECT-").Update(f"{projName}")
            # Set the current project and task to the prospective project and task, and clear prospective
            currRefs.curr_project = currRefs.prospective_project
            currRefs.prospective_project = None
            currRefs.curr_task = currRefs.prospective_task
            currRefs.prospective_task = None
            # Retrieve time
            currTime = datetime.datetime.now().strftime("%H:%M, %m/%d/%y")
            # Set the active since time
            main_window['-ACTIVE_SINCE-'].update(f"{currTime}")
            # Make the pause, description, tags, and feelings buttons visible
            make_visible(main_window, ["-PAUSE-",
                                       "-B_DESCRIPTION-",
                                       "-B_TAGS-",
                                       "-T_FEELINGS-",
                                       "-C_FEELINGS-",
                                       "-LTHISTASK-",
                                       "-FTHISTASK-",
                                       "-CONFUZZLED-",
                                       "-DREADLOCKED-"])
            # Set the pause button to pause (in case it's on resume)
            main_window["-PAUSE-"].update("Pause Task", button_color="black on light coral")
            # Recolor the description and tags buttons
            main_window["-B_DESCRIPTION-"].update(button_color="black on yellow")
            main_window["-B_TAGS-"].update(button_color="black on yellow")
            # Switch the "Start task" to "Switch task" Button
            main_window["-B_START_SWITCH_TASK-"].update("Switch Task")
            # Close the window
            task_window.close()
    # Close the window
    task_window.close()


# Start new project window
def start_new_proj_window(task_window, currRefs):

    new_proj_layout = [

        [sg.Text('Name your project:',
                 size=(15, 1),
                 key="-T_PROJ_SEL-",
                 enable_events=True),
         sg.InputText(size=(40, 1),
                      key="-I_NEW_PROJ_NAME-",
                      enable_events=True)
         ],

        [sg.Button('Confirm', key="-B_CONFIRM-", button_color="black on lime green", disabled=True),
         sg.Button('Cancel', key="-B_CANCEL-", button_color="black on light coral"),
         sg.Text('', key="-T_WARNING-", text_color='Red')]

    ]

    # Project list
    project_list = []
    # Query the tags
    results = sessionOne.query(c_TKDB.Project).with_entities(c_TKDB.Project.name)
    # For each project
    for project in results:
        # Append name to list
        project_list.append(project.name.casefold())
    # Convert list to set for rapid search
    project_list = set(project_list)

    # Make a new window
    proj_window = sg.Window("New Project", new_proj_layout, modal=True)

    # Start listening loop for new window
    while True:
        event, values = proj_window.read()
        print(event)
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        # If the event is cancel
        if event == "-B_CANCEL-":
            # Close the window
            proj_window.close()
        # If the event is a "new project" button press
        if event == "-I_NEW_PROJ_NAME-":
            # Reset the warning
            proj_window["-T_WARNING-"].update("")
            # If the length of the name is greater than 0
            if len(values["-I_NEW_PROJ_NAME-"]) > 0:
                # Enable the confirm button
                enable(proj_window, "-B_CONFIRM-")
            # Otherwise (nothing in the box)
            else:
                # Disable the confirm button
                disable(proj_window, "-B_CONFIRM-")
        # If the event is confirm
        if event == "-B_CONFIRM-":
            # If the project name is in the list
            if values["-I_NEW_PROJ_NAME-"].casefold() in project_list:
                # Set the warning
                proj_window["-T_WARNING-"].update("A project with this name already exists.")
            # Otherwise
            else:
                # Create a project object
                newProj = c_TKDB.Project(name=values["-I_NEW_PROJ_NAME-"],
                                         datetime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                # Add to the DB
                sessionOne.add(newProj)
                # Reference in the ref holder
                currRefs.prospective_project = newProj
                # Pass the value from the project name to the project name field in the main task window
                task_window.Element("-C_PROJ_SEL-").Update(newProj.name)
                # Enable the New Task button
                enable(task_window, "-B_NEW_TASK-")
                # Close the window
                proj_window.close()

    proj_window.close()


# Start new task window
def start_new_task_window(task_window, currRefs):

    new_task_layout = [

        [sg.Text('Name your task:',
                 size=(15, 1),
                 key="-T_TASK_SEL-",
                 enable_events=True),
         sg.InputText(size=(40, 1),
                      key="-I_NEW_TASK_NAME-",
                      enable_events=True),
         sg.Text('', key="-T_WARNING-", text_color='red')
         ],

        [sg.Button('Confirm', key="-B_CONFIRM-", button_color="black on lime green", disabled=True),
         sg.Button('Cancel', key="-B_CANCEL-", button_color="black on light coral")]

    ]

    # Task list
    task_list = []
    # For each task in the project
    for task in currRefs.prospective_project.tasks:
        # Append name to list
        task_list.append(task.name.casefold())
    # Convert list to set for rapid search
    task_list = set(task_list)

    # Make a new window
    new_task_window = sg.Window("New Task", new_task_layout, modal=True)

    # Start listening loop for new window
    while True:
        event, values = new_task_window.read()
        print(event)
        if event == "Exit" or event == sg.WIN_CLOSED or event == "-B_CANCEL-":
            # Close the window
            new_task_window.close()
            break
        # If the event is a "new project" button press
        elif event == "-I_NEW_TASK_NAME-":
            # Reset warning
            new_task_window["-T_WARNING-"].update('')
            # If the length of the name is greater than 0
            if len(values["-I_NEW_TASK_NAME-"]) > 0:
                # Enable the confirm button
                enable(new_task_window, "-B_CONFIRM-")
            # Otherwise (nothing in the box)
            else:
                # Disable the confirm button
                disable(new_task_window, "-B_CONFIRM-")
        # If the event is confirm
        elif event == "-B_CONFIRM-":
            # If the proposed name already exists as a task in the project
            if values["-I_NEW_TASK_NAME-"].casefold() in task_list:
                # Update warning
                new_task_window["-T_WARNING-"].update(f"Task with this name already exists in {currRefs.prospective_project.name}")
            # Otherwise
            else:
                # Create a task object
                newTask = c_TKDB.Task(name=values["-I_NEW_TASK_NAME-"],
                                      project=currRefs.prospective_project,
                                      datetime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                # Add to the DB
                sessionOne.add(newTask)
                # Reference
                currRefs.prospective_task = newTask
                # Pass the value from the project name to the project name field in the main task window
                task_window.Element("-C_TASK_SEL-").Update(newTask.name)
                # Make visible the Confirm button
                enable(task_window, "-B_CONFIRM-")
                # Close the window
                new_task_window.close()

    new_task_window.close()

# Start description window
def start_description_window(main_window, currRefs):

    # Get current effort description, if any
    if currRefs.ongoing_effort.description is not None:
        currDescription = currRefs.ongoing_effort.description
    # Otherwise (no description)
    else:
        # Empty string
        currDescription = ''

    description_layout = [

        [sg.Text('Enter the description for this effort:',
                 size=(15, 1),
                 key="-T_DESCRIPTION-",
                 enable_events=True)],
         [sg.InputText(currDescription,
                      size=(80, 1),
                      key="-I_DESCRIPTION-",
                      enable_events=True)
         ],

        [sg.Button('Confirm', key="-B_CONFIRM-", button_color="black on lime green", disabled=True),
         sg.Button('Cancel', key="-B_CANCEL-", button_color="black on light coral")]

    ]

    # Make a new window
    description_window = sg.Window("New Task", description_layout, modal=True)

    # Start listening loop for new window
    while True:
        event, values = description_window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        # If the event is cancel
        if event == "-B_CANCEL-":
            # Close the window
            description_window.close()
        # If the event is a change in the description
        if event == "-I_DESCRIPTION-":
            # If the length of the description is great than 0
            if len(values["-I_DESCRIPTION-"]):
                # Enable the confirm button
                enable(description_window, "-B_CONFIRM-")
            # Otherwise (length 0), disable the confirm button
            else:
                disable(description_window, "-B_CONFIRM-")
        # If the event is confirm
        if event == "-B_CONFIRM-":
            # Make the efforts description equal the value in the box
            currRefs.ongoing_effort.description = values["-I_DESCRIPTION-"]
            # Recolor the main window button
            main_window["-B_DESCRIPTION-"].update(button_color="black on dark turquoise")
            # Commit the changes
            sessionOne.commit()
            # Close the window
            description_window.close()


# Start tag window
def start_tag_window(main_window, currRefs):

    # Get all the tags from the database
    results = sessionOne.query(c_TKDB.Tag)

    tag_layout = [ [sg.Text("Select tags below, or inherit from previous:"),
                    sg.Button("Efforts in Task",
                              key="-B_PREV_EFFORT-"),
                    sg.Button("Tasks in Project",
                              key="-B_PREV_TASK-")]
    ]

    # Tag dictionary (to reference object with button as key)
    tag_dict = {}
    # Tag count
    tag_count = 0
    # Checkbox row
    checkbox_row = []
    # For each tag
    for tag in results:
        # Iterate tag count
        tag_count += 1
        # If it's time to move onto a new row
        if tag_count == 6:
            # Append the row
            tag_layout.append(checkbox_row)
            # New blank row
            checkbox_row = []
            # Reset count
            tag_count = 1
        # Create a checkbox
        newCheckbox = sg.Checkbox(tag.name,
                                  size=(15, 1),
                                  enable_events=True,
                                  default=False,
                                  key=f"-{tag.name}-")
        # Reference the tag object by the checkbox key
        tag_dict[newCheckbox.Key] = tag
        # Append the checkbox to checkbox row
        checkbox_row.append(newCheckbox)
    # If there are any leftover tags
    if len(checkbox_row) > 0:
        # Append the last row
        tag_layout.append(checkbox_row)
    # Append the confirm and cancel buttons
    tag_layout.append([sg.Button('Confirm', key="-B_CONFIRM-", button_color="black on lime green", disabled=True),
                       sg.Button('Cancel', key="-B_CANCEL-", button_color="black on light coral"),
                       sg.Button('New Tag', key="-B_NEW_TAG-")])

    # Open the window
    tag_window = sg.Window('Tags', tag_layout, modal=True, finalize=True)

    # Query any existing tags for the effort
    if len(currRefs.ongoing_effort.tags) > 0:
        # For each tag
        for tag in currRefs.ongoing_effort.tags:
            # Make the tag value true in the tags window
            tag_window[f'-{tag.name}-'].update(True)

    # Start listening loop for new window
    while True:

        event, values = tag_window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            # Roll back any changes
            sessionOne.rollback()
            break
        # If the event is cancel
        elif event == "-B_CANCEL-":
            # Roll back any changes
            sessionOne.rollback()
            # Close the window
            tag_window.close()
        # If the event is confirm
        elif event == "-B_CONFIRM-":
            # Tag list
            tag_list = []
            # For each checkbox
            for checkbox in tag_dict.keys():
                print(values[checkbox])
                # If the checkbox is ticked
                if values[checkbox] is True:
                    # Append the tag object to the list
                    tag_list.append(tag_dict[checkbox])
            # If there is at least one tag
            if len(tag_list) > 0:
                # Replace the list in the effort object
                currRefs.ongoing_effort.tags = tag_list
            # Otherwise (no tags)
            else:
                # Replace the tags with None in the effort object
                currRefs.ongoing_effort.tags = []
            # Recolor the main window button
            main_window["-B_TAGS-"].update(button_color="black on dark turquoise")
            # Commit any changes
            sessionOne.commit()
            # Close the window
            tag_window.close()
        # If the event if that the "Inherit from Previous Effort in Task" button is pressed
        elif event == "-B_PREV_EFFORT-":
            # Tag list
            tag_list = []
            # For each effort
            for effort in currRefs.curr_task.efforts:
                # For each tag
                for tag in effort.tags:
                    # If the tag is not in the list
                    if tag not in tag_list:
                        # Append to list
                        tag_list.append(tag)
            # If the tag list has entries
            if len(tag_list) > 0:
                # For each tag in the list
                for tag in tag_list:
                    # Make the tag value true in the tags window
                    tag_window[f'-{tag.name}-'].update(True)
                    # Enable confirm button
                    enable(tag_window, "-B_CONFIRM-")
        # If the event if that the "Inherit from Previous Tasks in Project" button is pressed
        elif event == "-B_PREV_TASK-":
            # Tag list
            tag_list = []
            # For each effort
            for task in currRefs.curr_project.tasks:
                # For each effort in the task
                for effort in task.efforts:
                    # For each tag
                    for tag in effort.tags:
                        # If the tag is not in the list
                        if tag not in tag_list:
                            # Append to list
                            tag_list.append(tag)
            # If the tag list has entries
            if len(tag_list) > 0:
                # For each tag in the list
                for tag in tag_list:
                    # Make the tag value true in the tags window
                    tag_window[f'-{tag.name}-'].update(True)
                    # Enable confirm button
                    enable(tag_window, "-B_CONFIRM-")
        # Otherwise, if the event is pressing "New tag" button
        elif event == "-B_NEW_TAG-":
            # Start a new tag window
            start_new_tag_window(main_window, tag_window, currRefs)
        # Otherwise (event is one of the tags)
        else:
            # Enable the confirm button
            enable(tag_window, "-B_CONFIRM-")

# Start new tag window
def start_new_tag_window(main_window, tag_window, currRefs):

    new_tag_layout = [ [sg.Text("Name new tag:"),
                        sg.InputText(key="-I_NEW_TAG-",
                                     enable_events=True)],
                       [sg.Button('Confirm', key="-B_CONFIRM-", button_color="black on lime green", disabled=True),
                        sg.Button('Cancel', key="-B_CANCEL-", button_color="black on light coral"),
                        sg.Text('', key="-T_WARNING-")]
                       ]

    # Tag list
    tag_list = []
    # Query the tags
    results = sessionOne.query(c_TKDB.Tag).with_entities(c_TKDB.Tag.name)
    # For each tag
    for tag in results:
        # Append name to list
        tag_list.append(tag.name.casefold())
    # Convert list to set for rapid search
    tag_list = set(tag_list)

    # Make the window
    new_tag_window = sg.Window('New Tag', new_tag_layout, modal=True)

    # Start listening loop for new window
    while True:

        event, values = new_tag_window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            # Roll back any changes
            sessionOne.rollback()
            break
        # If the event is cancel
        elif event == "-B_CANCEL-":
            # Roll back any changes
            sessionOne.rollback()
            # Close the window
            new_tag_window.close()
        # If the event is confirm
        elif event == "-B_CONFIRM-":
            # If the tag is in the DB already
            if values["-I_NEW_TAG-"].casefold() in tag_list:
                # Create warning
                new_tag_window["-T_WARNING-"].update("This tag already exists.", text_color='red')
            # Otherwise (truly a new tag)
            else:
                # Create a tag object and append to ongoing effort
                currRefs.ongoing_effort.tags.append(c_TKDB.Tag(name=values["-I_NEW_TAG-"]))
                # Confirm changes
                sessionOne.commit()
                # Close the tag window
                tag_window.close()
                # Reopen the tag window (to include new tag)
                start_tag_window(main_window, currRefs)
                # Close the window
                new_tag_window.close()
        # If the event is a change in the text box
        elif event == "-I_NEW_TAG-":
            # Clear the warning
            new_tag_window["-T_WARNING-"].update('')
            # If the length of the text is greater than 0
            if len(values["-I_NEW_TAG-"]) > 0:
                # Enable the confirm button
                enable(new_tag_window, "-B_CONFIRM-")
            # Otherwise (length 0)
            else:
                # Disable confirm
                disable(new_tag_window, "-B_CONFIRM-")

    new_tag_window.close()

# Start resume (after pause) window
def start_resume_window(main_window, currRefs):

    resume_layout = [[sg.Text("On resume, inherit description and tags from previous effort?"),
                   sg.Button("Yes",
                             key="-B_YES-"),
                   sg.Button("No",
                             key="-B_NO-")]
                  ]

    # Open the window
    resume_window = sg.Window('Resuming Task with new Effort', resume_layout, modal=True)

    # Start listening loop for new window
    while True:

        event, values = resume_window.read()
        if event == "Exit" or event == sg.WIN_CLOSED or event == "-B_NO-":
            break
        # If the event is "yes" button pushed
        elif event == "-B_YES-":
            # Transfer the description and tags to the ongoing effort
            currRefs.ongoing_effort.description = currRefs.prev_effort.description
            currRefs.ongoing_effort.tags = currRefs.prev_effort.tags
            # Recolor the description and tag buttons
            main_window["-B_DESCRIPTION-"].update(button_color="black on dark turquoise")
            main_window["-B_TAGS-"].update(button_color="black on dark turquoise")
            # Close the window
            resume_window.close()

    resume_window.close()

# Start main window
def start_main_window():

    # Make a reference holder object
    currRefs = tk_ref_holder()

    # Layout for the main window
    main_layout = [

        [sg.Text(f'Active Task:', size=(10, 1), background_color="DodgerBlue4", text_color="CadetBlue1"),
         sg.Text(size=(30, 1), key='-TASK-', background_color="DodgerBlue4", text_color="CadetBlue1"),
         sg.Text('Project:', background_color="DodgerBlue4", text_color="CadetBlue1"),
         sg.Text(size=(30, 1), key="-PROJECT-", background_color="DodgerBlue4", text_color="CadetBlue1")],

        [sg.Text(f'Active Since:',
                 size=(10, 1),
                 key="-T_ACTIVE_SINCE-",
                 background_color="DodgerBlue4",
                 text_color="CadetBlue1"),
         sg.Text(f'',
                 key="-ACTIVE_SINCE-",
                 size=(20, 1),
                 background_color="DodgerBlue4",
                 text_color="CadetBlue1"),
         place(sg.Button("Description",
                         key="-B_DESCRIPTION-",
                         visible=False)),
         place(sg.Button("Tags",
                         key="-B_TAGS-",
                         visible=False))
         ],

        [place(sg.Button('Pause Task',
                   size=(12, 1),
                   key="-PAUSE-",
                   button_color='black on light coral',
                   visible=False)),
         place(sg.Text('At this moment, I am feeling',
                       key="-T_FEELINGS-",
                       visible=False)),
         place(sg.Combo(['moderate', 'mild', 'profound'],
                  default_value='moderate',
                  key="-C_FEELINGS-",
                  visible=False)),
         place(sg.Button('Joy',
                   key="-LTHISTASK-",
                   button_color="blue",
                   visible=False)),
         place(sg.Button('Rage',
                   key="-FTHISTASK-",
                   button_color='firebrick1',
                   visible=False)),
         place(sg.Button('Confusion',
                   key="-CONFUZZLED-",
                   button_color='dim gray',
                   visible=False)),
         place(sg.Button('Dread',
                   key="-DREADLOCKED-",
                   button_color='black',
                   visible=False))],

        [sg.Text(f'Functions:')],

        [sg.Button('Start Task',
                   key="-B_START_SWITCH_TASK-"),
         sg.Button('View Records',
                   key="-B_VIEW_RECORDS-")]

    ]

    # Create the main window
    window = sg.Window('Timekeeper', main_layout)

    # Event loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()

        print(f"Main window: {event}")

        if event == sg.WIN_CLOSED or event == 'Cancel':
            # If there is an ongoing event
            if currRefs.ongoing_effort is not None:
                # Give it an end time
                currRefs.ongoing_effort.end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Commit any changes
            sessionOne.commit()
            sessionOne.close()
            # Break the While loop
            break

        # If Start task is selected
        if event == "-B_START_SWITCH_TASK-":
            # Activate the Start Task window
            start_task_window(window, currRefs)

        if event == '-PAUSE-':
            if window['-PAUSE-'].ButtonText == 'Resume Task':
                window['-PAUSE-'].update('Pause Task', button_color='black on light coral')
                # Make an Effort object
                newEffort = c_TKDB.Effort(project_id=currRefs.curr_project.id,
                                          task_id=currRefs.curr_task.id,
                                          start_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                # Reference ongoing as previous effort
                currRefs.prev_effort = currRefs.ongoing_effort
                # Reference as ongoing effort
                currRefs.ongoing_effort = newEffort
                # Add to session
                sessionOne.add(newEffort)
                # Recolor the description and tags buttons
                window["-B_DESCRIPTION-"].update(button_color="black on yellow")
                window["-B_TAGS-"].update(button_color="black on yellow")
                # Open the inherit tags/description window
                start_resume_window(window, currRefs)
            else:
                # Give the ongoing effort an end time
                currRefs.ongoing_effort.end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                window['-PAUSE-'].update('Resume Task', button_color='black on lime green')
            # Commit the changes
            sessionOne.commit()
        # If the edit record is called
        if event == "-B_EDIT_RECORD-":
            # Make the edit options visible
            make_visible(window, ["-B_ADD_EFFORT-", "-B_EDIT_EFFORT-", "-B_DELETE_EFFORT-"])

        # If the task changes
        if event == "-TASK-":
            # Get time
            currTime = datetime.datetime.now().strftime("%H:%M, %m/%d/%y")
            # Set the active since time
            window['-ACTIVE_SINCE-'].update(f"{currTime}")

        # If one of the feelings buttons are pressed
        if event == "-LTHISTASK-" or event == "-FTHISTASK-" or event == "-CONFUZZLED-" or event == "-DREADLOCKED-":
            # Get feeling
            currFeeling = window[event].ButtonText
            # Get severity
            currSeverity = values["-C_FEELINGS-"]
            # Add feeling to current effort
            currRefs.ongoing_effort.feelings.append(c_TKDB.Feeling(name=window[event].ButtonText,
                                                                   severity=values["-C_FEELINGS-"],
                                                                   datetime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                                   effort_id=currRefs.ongoing_effort.id,
                                                                   task_id=currRefs.curr_task.id,
                                                                   project_id=currRefs.curr_project.id))
            # Commit changes
            sessionOne.commit()
            # Print update
            #print(f"This is where we would write a {currSeverity} {currFeeling} Feeling to the DB")

        # If the "description" button is pressed
        if event == "-B_DESCRIPTION-":
            # Start a description window
            start_description_window(window, currRefs)

        # If the "tags" button is pressed
        if event == "-B_TAGS-":
            # Start tags window
            start_tag_window(window, currRefs)


    window.close()