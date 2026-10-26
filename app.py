
import os
import uuid
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "local-development-key")

UPLOAD_FOLDER = Path(__file__).resolve().parent / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB


@app.route("/")
def home():
    files = []

    for file in UPLOAD_FOLDER.iterdir():
        if file.is_file():
            files.append({
                "name": file.name,
                "size": round(file.stat().st_size / 1024, 2)
            })

    files.sort(key=lambda item: item["name"].lower())
    return render_template("index.html", files=files)


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")

    if not file or not file.filename:
        flash("Please select a file.")
        return redirect(url_for("home"))

    filename = secure_filename(file.filename)

    if not filename:
        flash("Invalid file name.")
        return redirect(url_for("home"))

    # Unique names prevent overwriting existing files.
    stored_name = f"{uuid.uuid4().hex}_{filename}"
    file.save(UPLOAD_FOLDER / stored_name)

    flash("File uploaded successfully!")
    return redirect(url_for("home"))


@app.route("/download/<filename>")
def download(filename):
    if Path(filename).name != filename:
        flash("Invalid file name.")
        return redirect(url_for("home"))

    if not (UPLOAD_FOLDER / filename).is_file():
        flash("File not found.")
        return redirect(url_for("home"))

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename,
        as_attachment=True
    )


@app.route("/delete/<filename>", methods=["POST"])
def delete(filename):
    if Path(filename).name != filename:
        flash("Invalid file name.")
        return redirect(url_for("home"))

    file_path = UPLOAD_FOLDER / filename

    if file_path.is_file():
        file_path.unlink()
        flash("File deleted successfully!")
    else:
        flash("File not found.")

    return redirect(url_for("home"))


@app.errorhandler(413)
def file_too_large(error):
    flash("File is too large. Maximum size is 16 MB.")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
