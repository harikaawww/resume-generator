"""Flask web app that turns a form into a professional PDF resume."""
import re

from flask import Flask, render_template, request, send_file

from pdf_generator import THEMES, build_resume_pdf

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # reject requests over 1 MB

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Single-value text fields in the form.
FIELDS = [
    "name", "headline", "email", "phone", "location",
    "links", "summary", "skills", "languages",
]

# Each repeatable section and the form fields inside one entry of it.
SECTIONS = {
    "experience": ["role", "company", "dates", "details"],
    "projects": ["title", "link", "description"],
    "education": ["degree", "school", "year"],
    "certificates": ["name", "issuer", "year"],
}


def collect_entries(section):
    """Read the repeated inputs of one section into a list of dicts."""
    fields = SECTIONS[section]
    columns = [request.form.getlist(f"{section}_{f}[]") for f in fields]
    entries = []
    for values in zip(*columns):
        entry = dict(zip(fields, (v.strip() for v in values)))
        if any(entry.values()):  # skip completely empty entries
            entries.append(entry)
    return entries


@app.route("/")
def index():
    return render_template("index.html", themes=THEMES)


@app.route("/download", methods=["POST"])
def download():
    data = {field: request.form.get(field, "").strip() for field in FIELDS}
    for section in SECTIONS:
        data[section] = collect_entries(section)

    if not data["name"]:
        return "Please enter your full name.", 400
    if data["email"] and not EMAIL_PATTERN.match(data["email"]):
        return "Please enter a valid email address.", 400

    theme = request.form.get("template", "classic")
    pdf = build_resume_pdf(data, theme)
    return send_file(
        pdf,
        as_attachment=True,
        download_name="resume.pdf",
        mimetype="application/pdf",
    )


if __name__ == "__main__":
    app.run(debug=True)
