from flask import Flask, request, redirect, render_template, url_for

app = Flask(__name__)
TASK_FILE = "tasks.txt"

def add_numbers(a, b):
    return a + b

def write_task(task):
    with open(TASK_FILE, "a") as doc:
        doc.write(task + "\n")

def write_tasks(tasks):
    with open(TASK_FILE, "w") as f:
        f.write("\n".join(tasks))
           
def read_tasks():
    try:
        with open(TASK_FILE, "r") as f:
            return f.read().splitlines()
    except FileNotFoundError:
        return []

@app.route('/', methods=["GET", "POST"])
def home():
    tasks = read_tasks()

    if request.method == "POST" and "task" in request.form:
        task = request.form.get("task")
        if task:
            tasks.append(task)
            write_tasks(tasks)
        return redirect("/")

    edit_index = request.args.get("edit", default=None, type=int)
    return render_template("index.html", tasks=tasks, edit_index=edit_index)

@app.route("/edit/<int:task_id>")
def edit_task(task_id):
    return redirect(url_for("home", edit=task_id))

@app.route("/update", methods=["POST"])
def update_task():
    tasks = read_tasks()
    task_id = int(request.form.get("task_id"))
    updated_text = request.form.get("updated_task")

    if 0 <= task_id < len(tasks) and updated_text:
        tasks[task_id] = updated_text
        write_tasks(tasks)

    return redirect("/")

@app.route("/delete", methods=["POST"])
def delete_task():
    task_to_delete = request.form.get("task_to_delete")
    tasks = read_tasks()
    updated_tasks = [task for task in tasks if task != task_to_delete]
    write_tasks(updated_tasks)
    return redirect("/")

@app.route("/about")
def about():
    return render_template("about.html")
 
if __name__ == '__main__':
    app.run(debug=True)