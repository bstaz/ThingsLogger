#!/usr/bin/env -S uv run

from datetime import datetime
from time import sleep

import things
from rich import print
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings
from sqlmodel import Field, Session, SQLModel, create_engine, select
from jinja2 import Environment


class Settings(BaseSettings, case_sensitive=True):
    dbhost: str
    dbport: int
    dbname: str
    dbuser: str
    dbpass: str
    debug: bool = False
    log_output: str
    template_path: str

    def dsn(self) -> PostgresDsn:
        return f"postgresql://{self.dbuser}:{self.dbpass}@{self.dbhost}:{self.dbport}/{self.dbname}"


def connect(settings: Settings) -> Session:
    engine = None
    if settings.debug:
        engine = create_engine(str(settings.dsn()), echo=True)
    else:
        engine = create_engine(str(settings.dsn()))

    SQLModel.metadata.create_all(engine)

    return Session(engine)


class Task(SQLModel, table=True):
    uuid: str = Field(primary_key=True)
    title: str
    modified: datetime


def file_slug_from_title(title: str) -> str:
    keepcharacters = ("-", "_")
    cleaned = title.replace(" ", "-").lower()
    cleaned = "".join(c for c in cleaned if c.isalnum() or c in keepcharacters).rstrip()
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    if len(cleaned) > 30:
        return cleaned[0:29]

    return cleaned


def log_task(task, project=None, checklist_items=None):
    settings = Settings()
    slug = file_slug_from_title(task["title"])
    filename = f"{settings.log_output}/{slug}-{task['uuid'][-5:]}.md"
    task_dict = {
        "uuid": task["uuid"],
        "title": task["title"],
        "created": task["created"],
        "created_date": datetime.strftime(
            datetime.strptime(task["created"], "%Y-%m-%d %H:%M:%S"), "%Y-%m-%d"
        ),
        "modified": task["modified"],
        "modified_date": datetime.strftime(
            datetime.strptime(task["modified"], "%Y-%m-%d %H:%M:%S"), "%Y-%m-%d"
        ),
        "completed": task["stop_date"],
        "completed_date": datetime.strftime(
            datetime.strptime(task["stop_date"], "%Y-%m-%d %H:%M:%S"), "%Y-%m-%d"
        ),
        "notes": task["notes"],
        "thingslink": f"things:///show?id={task['uuid']}",
        "tags": task["tags"] if "tags" in task else None,
        "project": project,
        "checklist_items": checklist_items,
    }
    with open(settings.template_path, "r") as f:
        template = Environment().from_string(f.read())
    with open(filename, "w") as f:
        f.write(template.render(**task_dict))
        print(f'Logged task "{task["title"]}" to {filename}')


def main():
    settings = Settings()

    session: Session = connect(settings)
    all_tasks = things.tasks(status=None, type="to-do")

    # Enumerate projects and areas, first
    projects_list = {}
    projects = things.projects()
    for project in projects:
        if "area_title" in project:
            projects_list[project["uuid"]] = (
                f"{project['area_title']} / {project['title']}"
            )
        else:
            projects_list[project["uuid"]] = project["title"]

    for task in all_tasks:
        # print(task)
        db_task = session.exec(select(Task).where(Task.uuid == task["uuid"])).first()
        date_to_use = task["modified"] if task["modified"] else task["created"]
        task_modified: datetime = datetime.strptime(date_to_use, "%Y-%m-%d %H:%M:%S")
        if db_task:
            try:
                if db_task.modified < task_modified:
                    db_task.title = task["title"]
                    db_task.modified = task_modified
                    session.add(db_task)
                    print(f'Updated task "{db_task.title}"')
                    if task["stop_date"]:
                        print(f'Task "{db_task.title}" has been completed')
                        if "checklist" in task:
                            checklist_items = things.checklist_items(task["uuid"])
                        else:
                            checklist_items = None
                        if "project" in task:
                            log_task(
                                task,
                                project=projects_list[task["project"]],
                                checklist_items=checklist_items,
                            )
                        else:
                            log_task(task, checklist_items=checklist_items)
            except TypeError as e:
                print(e)
                print(task)
        else:
            print(f"New task {task['title']} added")
            db_task = Task(
                uuid=task["uuid"], title=task["title"], modified=task_modified
            )
            session.add(db_task)
    session.commit()


if __name__ == "__main__":
    while True:
        try:
            main()
            sleep(60)
        except KeyboardInterrupt:
            print("Exiting...")
            exit(0)
