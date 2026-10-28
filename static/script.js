// Handles the form: adding/removing entries, the live preview, sample data,
// the completeness meter and the light/dark switch.
// All preview text is inserted with textContent, never innerHTML, so user
// input can never inject HTML into the page.

const form = document.getElementById("resume-form");
const preview = document.getElementById("preview");
const SECTIONS = ["experience", "projects", "education", "certificates"];

/* ---------- Repeatable entries ---------- */

function addEntry(section, values = {}) {
  const blueprint = document.getElementById(`tpl-${section}`);
  const entry = blueprint.content.firstElementChild.cloneNode(true);
  entry.querySelectorAll("[data-f]").forEach((input) => {
    if (values[input.dataset.f] !== undefined) input.value = values[input.dataset.f];
  });
  document.getElementById(`list-${section}`).appendChild(entry);
}

function clearEntries(section) {
  document.getElementById(`list-${section}`).replaceChildren();
}

function readEntries(section) {
  const entries = [];
  document.querySelectorAll(`#list-${section} .entry`).forEach((box) => {
    const item = {};
    box.querySelectorAll("[data-f]").forEach((input) => {
      item[input.dataset.f] = input.value.trim();
    });
    if (Object.values(item).some(Boolean)) entries.push(item);
  });
  return entries;
}

/* ---------- Small DOM helpers ---------- */

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

function bulletList(text) {
  const ul = el("ul");
  text.split("\n")
    .map((line) => line.replace(/^[\s\-•]+/, "").trim())
    .filter(Boolean)
    .forEach((line) => ul.appendChild(el("li", "", line)));
  return ul;
}

function row(bold, rest, right) {
  const wrap = el("div", "p-row");
  const left = el("div");
  left.appendChild(el("strong", "", bold));
  if (rest) left.appendChild(document.createTextNode(", " + rest));
  wrap.appendChild(left);
  wrap.appendChild(el("div", "p-date", right));
  return wrap;
}

const sectionTitle = (title) => el("div", "p-section", title.toUpperCase());
const commaList = (text) => text.split(",").map((s) => s.trim()).filter(Boolean);

/* ---------- Live preview ---------- */

function render() {
  const get = (name) => form.elements[name].value.trim();
  preview.dataset.theme = get("template") || "classic";
  preview.replaceChildren();

  const experience = readEntries("experience");
  const projects = readEntries("projects");
  const education = readEntries("education");
  const certificates = readEntries("certificates");
  updateStrength(get, [experience, projects, education, certificates]);

  if (!get("name")) {
    preview.appendChild(el("p", "empty", "Start typing your name and your resume appears here."));
    return;
  }

  const head = el("div", "p-head");
  head.appendChild(el("div", "p-name", get("name")));
  if (get("headline")) head.appendChild(el("div", "p-headline", get("headline")));
  const contact = [get("email"), get("phone"), get("location")].filter(Boolean).join("  |  ");
  if (contact) head.appendChild(el("div", "p-contact", contact));
  const links = commaList(get("links")).join("  |  ");
  if (links) head.appendChild(el("div", "p-contact links", links));
  preview.appendChild(head);

  if (get("summary")) {
    preview.appendChild(sectionTitle("Summary"));
    preview.appendChild(el("p", "", get("summary")));
  }

  const skills = commaList(get("skills"));
  if (skills.length) {
    preview.appendChild(sectionTitle("Skills"));
    preview.appendChild(el("p", "", skills.join(" • ")));
  }

  if (experience.length) {
    preview.appendChild(sectionTitle("Experience"));
    experience.forEach((job) => {
      preview.appendChild(row(job.role, job.company, job.dates));
      preview.appendChild(bulletList(job.details || ""));
    });
  }

  if (projects.length) {
    preview.appendChild(sectionTitle("Projects"));
    projects.forEach((proj) => {
      preview.appendChild(row(proj.title, "", ""));
      if (proj.link) preview.appendChild(el("div", "p-link", proj.link));
      preview.appendChild(bulletList(proj.description || ""));
    });
  }

  if (education.length) {
    preview.appendChild(sectionTitle("Education"));
    education.forEach((edu) => preview.appendChild(row(edu.degree, edu.school, edu.year)));
  }

  if (certificates.length) {
    preview.appendChild(sectionTitle("Certifications"));
    certificates.forEach((c) => preview.appendChild(row(c.name, c.issuer, c.year)));
  }

  const languages = commaList(get("languages"));
  if (languages.length) {
    preview.appendChild(sectionTitle("Languages"));
    preview.appendChild(el("p", "", languages.join(" • ")));
  }
}

/* ---------- Completeness meter ---------- */

function updateStrength(get, lists) {
  const checks = [
    get("name"), get("headline"), get("email"), get("phone"),
    get("summary"), get("skills"), get("languages"),
    ...lists.map((list) => list.length > 0),
  ];
  const percent = Math.round((100 * checks.filter(Boolean).length) / checks.length);
  document.getElementById("strength-fill").style.width = percent + "%";
  document.getElementById("strength-label").textContent = percent + "% complete";
}

/* ---------- Sample data ---------- */

const SAMPLE = {
  fields: {
    name: "Jane Doe",
    headline: "Computer Science Student | Python Developer",
    email: "jane.doe@example.com",
    phone: "+91 98765 43210",
    location: "Hyderabad, India",
    links: "https://github.com/janedoe, https://linkedin.com/in/janedoe",
    summary: "Final-year CS student who enjoys building practical web apps with Flask and Python. Looking for a developer internship.",
    skills: "Python, Flask, SQL, Git, HTML/CSS, JavaScript",
    languages: "English (Fluent), Hindi (Native), Telugu (Native)",
  },
  experience: [{
    role: "Python Developer Intern",
    company: "ABC Tech",
    dates: "Jun 2026 - Aug 2026",
    details: "Built a REST API used by 200+ students\nWrote unit tests that raised coverage to 85%",
  }],
  projects: [{
    title: "Certificate Verification System",
    link: "https://github.com/janedoe/certificate-verification",
    description: "Generates QR-coded certificates with PDF download\nVerifies certificates online by scanning the QR code",
  }],
  education: [{
    degree: "B.Tech in Computer Science",
    school: "Example Institute of Technology",
    year: "2023 - 2027",
  }],
  certificates: [{
    name: "Python for Everybody",
    issuer: "Coursera",
    year: "2025",
  }],
};

function loadSample() {
  Object.entries(SAMPLE.fields).forEach(([name, value]) => {
    form.elements[name].value = value;
  });
  SECTIONS.forEach((section) => {
    clearEntries(section);
    SAMPLE[section].forEach((values) => addEntry(section, values));
  });
  render();
}

/* ---------- Light / dark interface ---------- */

function setUi(mode) {
  document.documentElement.dataset.ui = mode;
  try { localStorage.setItem("resumegen-ui", mode); } catch (e) { /* storage blocked */ }
}

function initUi() {
  let saved = null;
  try { saved = localStorage.getItem("resumegen-ui"); } catch (e) { /* ignore */ }
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  setUi(saved || (prefersDark ? "dark" : "light"));
}

/* ---------- Wire everything up ---------- */

document.addEventListener("click", (event) => {
  const add = event.target.closest("[data-add]");
  if (add) {
    addEntry(add.dataset.add);
    render();
  }
  const remove = event.target.closest("[data-remove]");
  if (remove) {
    remove.closest(".entry").remove();
    render();
  }
});

// Listen on the whole page, not just the form: the template radio buttons sit
// in the preview panel (outside the <form> tag) and would be missed otherwise.
document.addEventListener("input", render);
document.addEventListener("change", render);
document.getElementById("load-sample").addEventListener("click", loadSample);
document.getElementById("ui-toggle").addEventListener("click", () => {
  setUi(document.documentElement.dataset.ui === "dark" ? "light" : "dark");
});

initUi();
SECTIONS.forEach((section) => addEntry(section));
render();
