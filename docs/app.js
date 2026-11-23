/* CITS Skill Gap Analyzer — static demo.
 *
 * Runs entirely in the browser (no build step, no server) so it can be hosted
 * directly on GitHub Pages.  The scoring, gap detection and recommendation
 * logic mirrors ml/analyzer.py from the Flask project; the prediction step is
 * a lightweight stand-in for the trained RandomForest model.
 */

const REPO_URL = "https://github.com/mukeshbtech989-png/cits-skill-gap-analyzer";
const STORAGE_KEY = "cits-skill-gap-demo-v1";

const EXPECTED = 60;
const SKILLS = ["Python", "Java", "MySQL", "HTML/CSS", "JavaScript", "C/C++", "MS Office", "Soft Skills"];
const METRIC_KEYS = ["attendance", "theory_marks", "practical_marks", "test_score", "project_score"];
const METRIC_LABELS = ["Att.", "Theory", "Practical", "Tests", "Project"];
const WEIGHTS = {
  attendance: 0.10,
  theory_marks: 0.20,
  practical_marks: 0.25,
  test_score: 0.20,
  project_score: 0.15,
  skill_avg: 0.10,
};

const RECOMMENDATIONS = {
  "Python": "Practise loops, functions, OOP, file handling and small console projects.",
  "Java": "Revise classes, inheritance, interfaces, exception handling and collections.",
  "MySQL": "Practise SELECT/JOIN, GROUP BY, sub-queries and normalisation exercises.",
  "HTML/CSS": "Build two responsive pages using semantic HTML, Flexbox and CSS Grid.",
  "JavaScript": "Practise DOM manipulation, events, arrays/objects and small fetch-based apps.",
  "C/C++": "Strengthen pointers, arrays, structures and function decomposition with daily drills.",
  "MS Office": "Complete practical tasks in Word, Excel (formulas, charts) and PowerPoint.",
  "Soft Skills": "Join group discussions, mock interviews and short technical presentations.",
};

const SAMPLE_STUDENTS = [
  { id: 1, roll_no: "CITS26CSA001", name: "Aarav Sharma", attendance: 92, theory_marks: 78, practical_marks: 85, test_score: 74, project_score: 88, skills: { "Python": 72, "Java": 84, "MySQL": 78, "HTML/CSS": 80, "JavaScript": 70, "C/C++": 65, "MS Office": 85, "Soft Skills": 80 } },
  { id: 2, roll_no: "CITS26CSA002", name: "Priya Verma", attendance: 88, theory_marks: 82, practical_marks: 90, test_score: 86, project_score: 92, skills: { "Python": 88, "Java": 90, "MySQL": 84, "HTML/CSS": 86, "JavaScript": 80, "C/C++": 78, "MS Office": 90, "Soft Skills": 88 } },
  { id: 3, roll_no: "CITS26CSA003", name: "Rohit Kumar", attendance: 64, theory_marks: 52, practical_marks: 58, test_score: 48, project_score: 55, skills: { "Python": 42, "Java": 55, "MySQL": 50, "HTML/CSS": 60, "JavaScript": 38, "C/C++": 45, "MS Office": 62, "Soft Skills": 58 } },
  { id: 4, roll_no: "CITS26CSA004", name: "Sneha Gupta", attendance: 76, theory_marks: 68, practical_marks: 74, test_score: 66, project_score: 72, skills: { "Python": 58, "Java": 72, "MySQL": 68, "HTML/CSS": 74, "JavaScript": 52, "C/C++": 60, "MS Office": 78, "Soft Skills": 70 } },
  { id: 5, roll_no: "CITS26CSA005", name: "Aditya Singh", attendance: 81, theory_marks: 74, practical_marks: 80, test_score: 70, project_score: 76, skills: { "Python": 65, "Java": 78, "MySQL": 72, "HTML/CSS": 70, "JavaScript": 62, "C/C++": 68, "MS Office": 80, "Soft Skills": 66 } },
  { id: 6, roll_no: "CITS26CSA006", name: "Fatima Khan", attendance: 95, theory_marks: 88, practical_marks: 92, test_score: 90, project_score: 94, skills: { "Python": 92, "Java": 86, "MySQL": 88, "HTML/CSS": 90, "JavaScript": 84, "C/C++": 80, "MS Office": 92, "Soft Skills": 90 } },
  { id: 7, roll_no: "CITS26CSA007", name: "Vivek Yadav", attendance: 58, theory_marks: 46, practical_marks: 52, test_score: 42, project_score: 50, skills: { "Python": 35, "Java": 48, "MySQL": 44, "HTML/CSS": 55, "JavaScript": 32, "C/C++": 40, "MS Office": 58, "Soft Skills": 50 } },
  { id: 8, roll_no: "CITS26CSA008", name: "Anjali Mishra", attendance: 84, theory_marks: 76, practical_marks: 82, test_score: 78, project_score: 80, skills: { "Python": 70, "Java": 74, "MySQL": 80, "HTML/CSS": 78, "JavaScript": 68, "C/C++": 62, "MS Office": 82, "Soft Skills": 76 } },
];

/* ------------------------------------------------------------------ utils */
const clamp = (value) => Math.max(0, Math.min(100, Number(value) || 0));
const round1 = (value) => Math.round(value * 10) / 10;
const mean = (values) => (values.length ? values.reduce((a, b) => a + b, 0) / values.length : 0);
const clone = (value) => JSON.parse(JSON.stringify(value));

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]
  ));
}

function levelFor(score) {
  if (score >= 85) return "Excellent";
  if (score >= 70) return "Good";
  if (score >= 55) return "Average";
  return "Needs Improvement";
}

function slug(text) {
  return text.toLowerCase().replace(/\s+/g, "-");
}

/* --------------------------------------------------------------- analysis */
function analyze(student) {
  const skills = {};
  SKILLS.forEach((skill) => {
    skills[skill] = round1(clamp(student.skills ? student.skills[skill] : 0));
  });

  const metrics = METRIC_KEYS.map((key) => clamp(student[key]));
  const values = Object.values(skills);
  const avgSkill = mean(values);
  const minSkill = Math.min(...values);

  const rule = round1(
    WEIGHTS.attendance * metrics[0] +
    WEIGHTS.theory_marks * metrics[1] +
    WEIGHTS.practical_marks * metrics[2] +
    WEIGHTS.test_score * metrics[3] +
    WEIGHTS.project_score * metrics[4] +
    WEIGHTS.skill_avg * avgSkill
  );

  // Stand-in for the trained RandomForest: reward a high average skill level
  // and penalise a weak minimum skill, then blend with the rule score.
  const predicted = round1(clamp(rule + (avgSkill - 60) * 0.05 + (minSkill - 50) * 0.04));
  const overall = round1(0.7 * predicted + 0.3 * rule);

  const gaps = [];
  const strengths = [];
  Object.entries(skills).forEach(([skill, score]) => {
    if (score < EXPECTED) {
      const gap = round1(EXPECTED - score);
      gaps.push({
        skill,
        score,
        gap,
        severity: gap >= 20 ? "critical" : gap >= 10 ? "moderate" : "minor",
      });
    }
    if (score >= 75) strengths.push({ skill, score });
  });
  gaps.sort((a, b) => b.gap - a.gap);
  strengths.sort((a, b) => b.score - a.score);

  const recommendations = gaps.slice(0, 3).map((gap) => ({
    skill: gap.skill,
    current: gap.score,
    target: EXPECTED,
    priority: gap.severity,
    action: RECOMMENDATIONS[gap.skill] || "Revise the basics and take a short self-test every week.",
  }));

  if (!recommendations.length) {
    recommendations.push({
      skill: "Overall",
      current: overall,
      target: 85,
      priority: "stretch",
      action: "All tracked skills are at or above the expected level. Move on to advanced topics and real project work.",
    });
  }

  const level = levelFor(overall);
  const attendance = metrics[0];
  const risk = overall < 55 || attendance < 60 ? "High" : overall < 70 || attendance < 75 ? "Medium" : "Low";

  const strongText = strengths.length
    ? "Strongest areas: " + strengths.slice(0, 3).map((item) => item.skill).join(", ") + "."
    : "No skill is above 75 yet.";
  const gapText = gaps.length
    ? "Priority improvement areas: " + gaps.slice(0, 3).map((item) => item.skill).join(", ") + "."
    : "All tracked skills are at or above the expected level.";
  const summary = `${student.name}'s overall performance is at the ${level} level ` +
    `(AI score ${overall}/100). ${strongText} ${gapText}`;

  return {
    student,
    overall,
    predicted,
    rule,
    level,
    risk,
    skills,
    avgSkill: round1(avgSkill),
    gaps,
    strengths,
    recommendations,
    components: metrics.map(round1),
    summary,
  };
}

function cohortSummary(analyses) {
  if (!analyses.length) {
    return { total: 0, average: 0, atRisk: 0, weakest: null, skills: [] };
  }

  const skills = SKILLS.map((skill) => {
    const scores = analyses.map((item) => item.skills[skill]);
    return {
      skill,
      average: round1(mean(scores)),
      below: scores.filter((score) => score < EXPECTED).length,
    };
  }).sort((a, b) => a.average - b.average);

  return {
    total: analyses.length,
    average: round1(mean(analyses.map((item) => item.overall))),
    atRisk: analyses.filter((item) => item.risk === "High").length,
    weakest: skills[0] || null,
    skills,
  };
}

/* ------------------------------------------------------------------ state */
function loadStudents() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw !== null) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) return parsed;
    }
  } catch (error) {
    /* storage unavailable (private mode / file://) — fall back to memory */
  }
  return clone(SAMPLE_STUDENTS);
}

function saveStudents() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state.students));
  } catch (error) {
    /* ignore quota / privacy errors */
  }
}

const state = {
  students: loadStudents(),
  selectedId: null,
};

const analyses = () => state.students.map(analyze);

/* ----------------------------------------------------------------- render */
const els = {
  kpiTotal: document.getElementById("kpiTotal"),
  kpiAverage: document.getElementById("kpiAverage"),
  kpiAverageNote: document.getElementById("kpiAverageNote"),
  kpiRisk: document.getElementById("kpiRisk"),
  kpiWeakest: document.getElementById("kpiWeakest"),
  kpiWeakestNote: document.getElementById("kpiWeakestNote"),
  cohortChart: document.getElementById("cohortChart"),
  studentRows: document.getElementById("studentRows"),
  emptyState: document.getElementById("emptyState"),
  detailPanel: document.getElementById("detailPanel"),
  dialog: document.getElementById("addDialog"),
  form: document.getElementById("addForm"),
  formError: document.getElementById("formError"),
  skillInputs: document.getElementById("skillInputs"),
};

function barClass(score) {
  if (score < 50) return "is-low";
  if (score < 65) return "is-mid";
  return "is-high";
}

function renderStats(summary) {
  els.kpiTotal.textContent = summary.total;
  els.kpiAverage.textContent = summary.total ? summary.average : "—";
  els.kpiAverageNote.textContent = summary.total ? `${levelFor(summary.average)} overall` : "No data yet";
  els.kpiRisk.textContent = summary.atRisk;
  els.kpiWeakest.textContent = summary.weakest ? summary.weakest.skill : "—";
  els.kpiWeakestNote.textContent = summary.weakest
    ? `Class average ${summary.weakest.average}/100`
    : "No data yet";
}

function renderCohort(summary) {
  if (!summary.skills.length) {
    els.cohortChart.innerHTML = '<p class="muted">No data yet.</p>';
    return;
  }
  els.cohortChart.innerHTML = summary.skills.map((skill) => `
    <div class="bar-row">
      <span class="bar-label">${esc(skill.skill)}</span>
      <div class="bar-track">
        <div class="bar-fill ${barClass(skill.average)}" style="width:${skill.average}%"></div>
        <span class="bar-target" style="left:${EXPECTED}%"></span>
      </div>
      <span class="bar-value">${skill.average}<small>${skill.below} below</small></span>
    </div>
  `).join("");
}

function renderTable(items) {
  els.emptyState.hidden = items.length > 0;
  if (!items.length) {
    els.studentRows.innerHTML = "";
    return;
  }

  const sorted = [...items].sort((a, b) => b.overall - a.overall);
  els.studentRows.innerHTML = sorted.map((item) => {
    const student = item.student;
    const topGap = item.gaps[0];
    return `
      <tr data-id="${student.id}" tabindex="0" class="${student.id === state.selectedId ? "is-selected" : ""}">
        <td><span class="avatar">${esc(student.name.slice(0, 1).toUpperCase())}</span><span class="cell-name">${esc(student.name)}</span></td>
        <td class="mono">${esc(student.roll_no)}</td>
        <td class="num">${Math.round(item.components[0])}%</td>
        <td class="num"><strong>${item.overall}</strong></td>
        <td><span class="badge ${slug(item.level)}">${item.level}</span></td>
        <td>${topGap ? `${esc(topGap.skill)} <small class="muted">(−${topGap.gap})</small>` : '<span class="muted">None</span>'}</td>
        <td><span class="risk risk-${item.risk.toLowerCase()}">${item.risk}</span></td>
      </tr>
    `;
  }).join("");
}

function renderDetail() {
  const item = analyses().find((entry) => entry.student.id === state.selectedId);
  if (!item) {
    els.detailPanel.innerHTML = `
      <div class="detail-placeholder">
        <span class="pill">Student report</span>
        <h2>Select a student</h2>
        <p class="muted">Choose any row to see the AI summary, skill levels, gaps and a personalised learning plan.</p>
      </div>`;
    return;
  }

  const student = item.student;
  const gapsHtml = item.gaps.length
    ? `<ul class="gap-list">${item.gaps.map((gap) => `
        <li class="gap-item">
          <span><strong>${esc(gap.skill)}</strong><span class="severity ${gap.severity}">${gap.severity}</span></span>
          <span>${gap.score} → ${EXPECTED} <small>(−${gap.gap})</small></span>
        </li>`).join("")}</ul>`
    : '<p class="muted">Every tracked skill is at or above the expected level.</p>';

  const skillsHtml = Object.entries(item.skills).map(([skill, score]) => `
    <div class="bar-row">
      <span class="bar-label">${esc(skill)}</span>
      <div class="bar-track">
        <div class="bar-fill ${barClass(score)}" style="width:${score}%"></div>
        <span class="bar-target" style="left:${EXPECTED}%"></span>
      </div>
      <span class="bar-value">${score}</span>
    </div>`).join("");

  const recoHtml = item.recommendations.map((reco) => `
    <article class="reco">
      <div class="reco-head">
        <h3>${esc(reco.skill)}</h3>
        <span class="severity ${reco.priority}">${reco.priority}</span>
      </div>
      <p class="reco-score">${reco.current} → target ${reco.target}</p>
      <p>${esc(reco.action)}</p>
      <p class="reco-resource"><strong>Practice:</strong> ask your trainer for a worksheet on this topic.</p>
    </article>`).join("");

  const miniStats = item.components.map((value, index) => `
    <div class="mini-stat"><span>${METRIC_LABELS[index]}</span><strong>${Math.round(value)}</strong></div>`).join("");

  els.detailPanel.innerHTML = `
    <div class="detail-head">
      <span class="avatar avatar-lg">${esc(student.name.slice(0, 1).toUpperCase())}</span>
      <div>
        <h2>${esc(student.name)}</h2>
        <p class="muted">${esc(student.roll_no)} · Batch 2026-27</p>
      </div>
      <div class="score-ring ${slug(item.level)}" style="--pct:${item.overall}">
        <div class="score-ring-inner"><strong>${item.overall}</strong><span>${item.level}</span></div>
      </div>
    </div>

    <div class="ai-summary">
      <span class="pill pill-light">AI summary</span>
      <p>${esc(item.summary)}</p>
      <div class="ai-meta">
        <span>Model <strong>${item.predicted}</strong></span>
        <span>Rule score <strong>${item.rule}</strong></span>
        <span>Risk <strong>${item.risk}</strong></span>
      </div>
    </div>

    <div class="mini-stats">${miniStats}</div>

    <h3>Skill levels</h3>
    <div class="bars">${skillsHtml}</div>

    <h3 style="margin-top:16px">Skill gaps</h3>
    ${gapsHtml}

    <h3>Learning plan</h3>
    <div class="reco-list">${recoHtml}</div>

    <div class="detail-actions">
      <button class="btn btn-danger" type="button" data-action="delete">Delete record</button>
    </div>`;
}

function render() {
  const items = analyses();
  const summary = cohortSummary(items);
  renderStats(summary);
  renderCohort(summary);
  renderTable(items);
  renderDetail();
}

/* --------------------------------------------------------------- actions */
function selectStudent(id) {
  state.selectedId = id;
  renderTable(analyses());
  renderDetail();
  if (window.innerWidth < 1080) {
    els.detailPanel.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function deleteStudent() {
  const item = analyses().find((entry) => entry.student.id === state.selectedId);
  if (!item) return;
  if (!window.confirm(`Remove ${item.student.name} from the demo records?`)) return;
  state.students = state.students.filter((student) => student.id !== state.selectedId);
  state.selectedId = null;
  saveStudents();
  render();
}

function resetDemo() {
  state.students = clone(SAMPLE_STUDENTS);
  state.selectedId = null;
  saveStudents();
  render();
}

function exportCsv() {
  const header = [
    "Roll no", "Name", ...METRIC_LABELS, ...SKILLS,
    "AI score", "Level", "Risk", "Top gap",
  ];
  const rows = analyses()
    .sort((a, b) => b.overall - a.overall)
    .map((item) => [
      item.student.roll_no,
      item.student.name,
      ...item.components.map((value) => Math.round(value)),
      ...SKILLS.map((skill) => item.skills[skill]),
      item.overall,
      item.level,
      item.risk,
      item.gaps[0] ? `${item.gaps[0].skill} (-${item.gaps[0].gap})` : "None",
    ]);

  const cell = (value) => {
    const text = String(value ?? "");
    return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
  };
  const csv = [header, ...rows].map((row) => row.map(cell).join(",")).join("\r\n");
  const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `cits-skill-gap-report-${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

/* ------------------------------------------------------------------- form */
function buildSkillInputs() {
  els.skillInputs.innerHTML = SKILLS.map((skill) => `
    <label>${esc(skill)}
      <input type="number" min="0" max="100" step="1" value="${EXPECTED}" data-skill="${esc(skill)}">
    </label>`).join("");
}

function openDialog() {
  els.formError.hidden = true;
  els.form.reset();
  els.skillInputs.querySelectorAll("input").forEach((input) => { input.value = EXPECTED; });
  if (typeof els.dialog.showModal === "function") {
    els.dialog.showModal();
  } else {
    els.dialog.setAttribute("open", "");
  }
}

function closeDialog() {
  if (typeof els.dialog.close === "function") {
    els.dialog.close();
  } else {
    els.dialog.removeAttribute("open");
  }
}

function showFormError(message) {
  els.formError.textContent = message;
  els.formError.hidden = false;
}

function handleSubmit(event) {
  event.preventDefault();
  const data = new FormData(els.form);
  const rollNo = String(data.get("roll_no") || "").trim();
  const name = String(data.get("name") || "").trim();

  if (!rollNo || !name) {
    showFormError("Roll number and student name are required.");
    return;
  }
  if (state.students.some((student) => student.roll_no.toLowerCase() === rollNo.toLowerCase())) {
    showFormError(`Roll number ${rollNo} already exists.`);
    return;
  }

  const skills = {};
  els.skillInputs.querySelectorAll("input").forEach((input) => {
    skills[input.dataset.skill] = clamp(input.value);
  });

  const student = {
    id: Date.now(),
    roll_no: rollNo,
    name,
    attendance: clamp(data.get("attendance")),
    theory_marks: clamp(data.get("theory_marks")),
    practical_marks: clamp(data.get("practical_marks")),
    test_score: clamp(data.get("test_score")),
    project_score: clamp(data.get("project_score")),
    skills,
  };

  state.students.push(student);
  state.selectedId = student.id;
  saveStudents();
  render();
  closeDialog();
}

/* ------------------------------------------------------------------- init */
function init() {
  const repoLink = document.getElementById("repoLink");
  if (repoLink) repoLink.href = REPO_URL;

  buildSkillInputs();

  document.getElementById("openAdd").addEventListener("click", openDialog);
  document.getElementById("openAdd2").addEventListener("click", openDialog);
  document.getElementById("closeAdd").addEventListener("click", closeDialog);
  document.getElementById("cancelAdd").addEventListener("click", closeDialog);
  document.getElementById("resetDemo").addEventListener("click", resetDemo);
  document.getElementById("resetEmpty").addEventListener("click", resetDemo);
  document.getElementById("exportCsv").addEventListener("click", exportCsv);
  els.form.addEventListener("submit", handleSubmit);

  els.studentRows.addEventListener("click", (event) => {
    const row = event.target.closest("tr[data-id]");
    if (row) selectStudent(Number(row.dataset.id));
  });
  els.studentRows.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    const row = event.target.closest("tr[data-id]");
    if (row) {
      event.preventDefault();
      selectStudent(Number(row.dataset.id));
    }
  });

  els.detailPanel.addEventListener("click", (event) => {
    if (event.target.closest('[data-action="delete"]')) deleteStudent();
  });

  render();
}

init();
