from typing import Annotated

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, StringConstraints

app = FastAPI(
    title="Task API",
    version="1.0",
    description="A tiny in-memory to-do list API.",
)

tasks = [
    {"id": 1, "title": "Learn what an API is", "done": True},
    {"id": 2, "title": "Build a CRUD API", "done": False},
    {"id": 3, "title": "Push it to GitHub", "done": False},
]
next_id = 4

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class TaskCreate(BaseModel):
    title: Title


class TaskUpdate(BaseModel):
    title: Title | None = None
    done: bool | None = None


def not_found(task_id: int) -> JSONResponse:
    return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})


def bad_request(message: str) -> JSONResponse:
    return JSONResponse(status_code=400, content={"error": message})


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    messages = []
    for err in exc.errors():
        field = ".".join(str(part) for part in err["loc"][1:]) or "body"
        messages.append(f"{field}: {err['msg']}")
    return bad_request("; ".join(messages))


@app.get("/", summary="Describe the API")
def index():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health", summary="Health check")
def health():
    return {"status": "ok"}


@app.get("/tasks", summary="List all tasks")
def list_tasks():
    return tasks


@app.get("/tasks/{task_id}", summary="Get one task by id")
def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    return not_found(task_id)


@app.post("/tasks", status_code=201, summary="Create a task")
def create_task(body: TaskCreate):
    global next_id
    new_task = {"id": next_id, "title": body.title, "done": False}
    next_id += 1
    tasks.append(new_task)
    return new_task


@app.put("/tasks/{task_id}", summary="Update a task's title and/or done")
def update_task(task_id: int, body: TaskUpdate):
    if body.title is None and body.done is None:
        return bad_request("Send at least one of: title, done")
    for task in tasks:
        if task["id"] == task_id:
            if body.title is not None:
                task["title"] = body.title
            if body.done is not None:
                task["done"] = body.done
            return task
    return not_found(task_id)


@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task")
def delete_task(task_id: int):
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            del tasks[i]
            return Response(status_code=204)
    return not_found(task_id)
