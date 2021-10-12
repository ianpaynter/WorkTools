from sqlalchemy import Column, Integer, Numeric, String, ForeignKey, Table, create_engine, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

# Form a declarative base for the metadata
Base = declarative_base()

# Numeric defaults to importing as Decimal type, so this overrides it.
Numeric = Numeric(asdecimal=False)

# Many to many link tables
tag_effort = Table(
    "tag_effort",
    Base.metadata,
    Column("tag_id", Integer, ForeignKey("tag.id")),
    Column("effort_id", Integer, ForeignKey("effort.id"))

)

# Many to many link tables
interruptions = Table(
    "interruptions",
    Base.metadata,
    Column("interruptor_id", Integer, ForeignKey("effort.id"), primary_key=True),
    Column("interruptee_id", Integer, ForeignKey("effort.id"), primary_key=True),
    Column("datetime", TIMESTAMP)

)


class Project(Base):
    __tablename__ = "project"
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    # Attributes
    name = Column(String)
    datetime = Column(TIMESTAMP)
    # Collections
    tasks = relationship("Task", back_populates="project")
    efforts = relationship("Effort", back_populates="project")
    feelings = relationship("Feeling", back_populates="project")


class Task(Base):
    __tablename__ = "task"
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    # Attributes
    name = Column(String)
    datetime = Column(TIMESTAMP)
    # Foreign Keys
    project_id = Column(Integer, ForeignKey("project.id"))
    # Relationships (I am one of many)
    project = relationship("Project", back_populates="tasks")
    # Collections (I am one, they are many)
    efforts = relationship("Effort", back_populates="task")
    feelings = relationship("Feeling", back_populates="task")

class Effort(Base):
    __tablename__ = "effort"
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    # Attributes
    description = Column(String)
    start_time = Column(TIMESTAMP)
    end_time = Column(TIMESTAMP)
    # Foreign Keys
    project_id = Column(Integer, ForeignKey("project.id"))
    task_id = Column(Integer, ForeignKey("task.id"))
    # Relationships (I am one of many)
    project = relationship("Project", back_populates="efforts")
    task = relationship("Task", back_populates="efforts")
    # Collections (I am one, they are many)
    feelings = relationship("Feeling", back_populates="effort")
    # Many to many
    tags = relationship("Tag", secondary=tag_effort, back_populates="efforts")
    interruptors = relationship("Effort",
                                secondary=interruptions,
                                primaryjoin=id == interruptions.c.interruptee_id,
                                secondaryjoin=id == interruptions.c.interruptor_id,
                                backref="interruptees")
    #interruptees = relationship("Effort", secondary=interruptions, back_populates="interuptors")


class Tag(Base):
    __tablename__ = "tag"
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    # Attributes
    name = Column(String)
    # Many to many
    efforts = relationship("Effort", secondary=tag_effort, back_populates="tags")


class Feeling(Base):
    __tablename__ = "feeling"
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    # Attributes
    name = Column(String)
    severity = Column(String)
    datetime = Column(TIMESTAMP)
    # Foreign Keys
    effort_id = Column(Integer, ForeignKey("effort.id"))
    task_id = Column(Integer, ForeignKey("task.id"))
    project_id = Column(Integer, ForeignKey("project.id"))
    # Relationships (I am one of many)
    effort = relationship("Effort", back_populates="feelings")
    task = relationship("Task", back_populates="feelings")
    project = relationship("Project", back_populates="feelings")


if __name__ == "__main__":

    print('Creating Database')
    # Create a database as the specified path
    engine = create_engine('postgresql+psycopg2://tk_timekeeper:tk_timekeeper_password@localhost:5432/timekeeper')
    # Create the engine
    Base.metadata.create_all(engine)