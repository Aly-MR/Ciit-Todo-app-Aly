from flask import Flask, render_template, request, redirect, url_for, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from zoneinfo import ZoneInfo
import io, csv

app = Flask(__name__)

# Define the Hong Kong timezone
hong_kong_tz = ZoneInfo("Asia/Hong_Kong")

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///task.db?check_same_thread=False"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "connect_args": {"timeout": 30}
}

db = SQLAlchemy(app)

# Task model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(hong_kong_tz))
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(hong_kong_tz),
        onupdate=lambda: datetime.now(hong_kong_tz),
        index=True
    )

@app.route("/download_csv", methods=["GET"])
def download_csv():
    tasks = Task.query.order_by(Task.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Task", "Completed", "Created At", "Updated At"])

    for task in tasks:
        writer.writerow([
            task.id,
            task.task,
            bool(task.done),
            task.created_at.isoformat(),
            task.updated_at.isoformat()
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=list_of_tasks.csv"}
    )
    
    
@app.route("/upload_csv", methods=["POST"])
def upload_csv():
    file = request.files.get("csv_file")
   
    if not file or file.filename == "":
        return redirect(url_for('home'))
   
    batch_created_at = datetime.now(hong_kong_tz)
   
    raw = file.read()
   
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
       
    new_tasks = []
    reader = csv.reader(io.StringIO(text))
   
    for item, row in enumerate(reader):
        if not row:
            continue
        first_col = (row[0] or "").strip()
        if not first_col:
            continue
       
        # skip header if present
        if item == 0 and first_col.lower() in ("task", "text", "todo"):
            continue
       
        # FIX: use `task` (not `text`)
        new_tasks.append(Task(task=first_col, done=False, created_at=batch_created_at))
       
    if new_tasks:
        db.session.add_all(new_tasks)
        db.session.commit()
           
    return redirect(url_for('home'))

@app.route('/', methods=["GET", "POST"])
def home():
    if request.method == "POST":
        text = (request.form.get("task") or "").strip()
        if text:
            db.session.add(Task(task=text))
            db.session.commit()
        return redirect(url_for('home'))
    
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    return render_template("index.html", tasks=tasks)

@app.route("/delete/<int:id>", methods=["POST"])
def delete_task(id):
    try:
        task = Task.query.get_or_404(id)
        db.session.delete(task)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return redirect(url_for('home'))

@app.route("/edit/<int:id>", methods=["POST"])
def edit_task(id):
    new_text = (request.form.get("new_task") or "").strip()
    if new_text:
        try:
            task = Task.query.get_or_404(id)
            task.task = new_text            
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
    return redirect(url_for('home'))

@app.route("/toggle/<int:id>", methods=["POST"])
def toggle_task(id):
    try:
        task = Task.query.get_or_404(id)
        task.done = not task.done
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return ("", 204)

@app.route("/about")
def about():
    return render_template("about.html")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(port=8080, debug=True, threaded=False, use_reloader=False)
