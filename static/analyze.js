// analyze.js - only loaded on the "Check a job" page.
// Sends the form to the Flask API, draws the result, and handles reporting + the complaint draft.

const $ = (id) => document.getElementById(id);

const EXAMPLES = {
  fake: {
    title: "Work From Home Data Entry",
    company: "Top global firm. Contact hr.jobs2024@gmail.com or call +91 98765 43210 on WhatsApp.",
    description:
      "Earn Rs 50000 per week working only 2 hours a day from your mobile. No interview needed. " +
      "Pay a registration fee of Rs 999 (refundable) to confirm your seat. Share your Aadhaar and bank account details. Hurry, limited seats!!!",
    requirements: "No qualification required. Anyone can apply.",
    benefits: "Daily payment, unlimited earning, guaranteed bonus.",
  },
  real: {
    title: "Data Analyst",
    company: "Finlytics builds analytics software for banks, with offices in Pune and Bengaluru.",
    description:
      "You will analyse business data, build dashboards and present insights to stakeholders each month. " +
      "You will work with engineering and product teams and take part in sprint planning and code reviews.",
    requirements: "BCA or B.Tech with SQL and Excel knowledge. Internship experience is a plus.",
    benefits: "Health insurance, paid leave, learning budget and hybrid work.",
  },
};

const NEXT_STEPS = {
  danger: ["Do not continue with this offer.",
           "Never pay or share ID or bank details. Check the company on its official website and report the posting."],
  warning: ["Proceed with caution.",
            "Verify the company and recruiter independently, use official email only, and do not pay anything."],
  safe: ["No major red flags found.",
         "Still verify the company on its official website, and remember that real employers never ask you to pay."],
};

const KIND_LABEL = { phone: "Phone", email: "Email", domain: "Website" };

let lastReport = "";
let lastResult = null;
let lastForm = null;

function fill(example) {
  for (const key of Object.keys(example)) $(key).value = example[key];
}

function readForm() {
  return {
    title: $("title").value,
    company: $("company").value,
    description: $("description").value,
    requirements: $("requirements").value,
    benefits: $("benefits").value,
  };
}

// Build DOM nodes with textContent (never innerHTML) so pasted text cannot inject HTML/JS (XSS safety).
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function show(state) {            // state: "empty" | "loading" | "result"
  $("empty").hidden = state !== "empty";
  $("loading").hidden = state !== "loading";
  $("result").hidden = state !== "result";
  $("copy").hidden = state !== "result";
}

function renderEntities(entities) {
  const list = $("entities");
  list.replaceChildren();
  if (entities.length === 0) {
    list.append(el("li", "none", "No phone numbers, emails or websites found in the text."));
    return;
  }
  for (const e of entities) {
    const li = el("li");
    li.append(el("span", "kind", KIND_LABEL[e.kind] || e.kind));
    li.append(el("span", "val", e.value));
    const status = e.reports === 0 ? "Not reported yet" : `Reported ${e.reports} time${e.reports === 1 ? "" : "s"}`;
    li.append(el("span", "badge " + (e.reports >= 3 ? "danger" : e.reports > 0 ? "warning" : "safe"), status));
    list.append(li);
  }
}

function render(r) {
  show("result");

  const colors = { safe: "--safe", warning: "--warning", danger: "--danger" };
  const gauge = $("gauge");
  gauge.style.setProperty("--c", `var(${colors[r.level]})`);
  gauge.style.setProperty("--p", 0);
  requestAnimationFrame(() => requestAnimationFrame(() => gauge.style.setProperty("--p", r.risk_percent)));
  $("pct").textContent = r.risk_percent + "%";

  const verdict = $("verdict");
  verdict.textContent = r.verdict;
  verdict.className = "verdict " + r.level;
  $("breakdown").textContent =
    `ML model: ${Math.round(r.ml_probability * 100)}%  |  Rules: ${Math.round(r.rule_score * 100)}%`;

  const next = $("next");
  next.className = "next " + r.level;
  next.replaceChildren(el("strong", "", NEXT_STEPS[r.level][0]), document.createTextNode(NEXT_STEPS[r.level][1]));

  const flags = $("flags");
  flags.replaceChildren();
  if (r.red_flags.length === 0) {
    flags.append(el("li", "none", "No known scam patterns detected."));
  } else {
    for (const f of r.red_flags) {
      const li = el("li");
      li.append(el("div", "fname", f.name));
      li.append(el("div", "fmatch", `Matched: "${f.matched}"`));
      li.append(el("div", "fadvice", f.advice));
      flags.append(li);
    }
  }

  const words = $("words");
  words.replaceChildren();
  if (r.suspicious_words.length === 0) {
    words.append(el("span", "chip none", "None"));
  } else {
    for (const w of r.suspicious_words) words.append(el("span", "chip", w.word));
  }

  renderEntities(r.entities);
  $("report-box").hidden = r.entities.length === 0;
  $("report-msg").textContent = "";
  $("report").disabled = false;
  $("draft").hidden = r.level === "safe";   // a complaint only makes sense for a risky posting
  $("complaint").hidden = true;

  lastReport =
    `JobShield report\nVerdict: ${r.verdict} (${r.risk_percent}% risk)\n` +
    `Red flags: ${r.red_flags.length ? r.red_flags.map((f) => f.name).join(", ") : "none"}\n` +
    `Suspicious words: ${r.suspicious_words.length ? r.suspicious_words.map((w) => w.word).join(", ") : "none"}`;
}

// ---------- complaint draft ----------
function buildComplaint(r, form) {
  const today = new Date().toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" });
  const summary = form.description.replace(/\s+/g, " ").trim().slice(0, 350);
  const flags = r.red_flags.map((f) => `- ${f.name} (matched: "${f.matched}")`).join("\n") || "- None detected";
  const contacts = r.entities.map((e) => `- ${KIND_LABEL[e.kind]}: ${e.value}`).join("\n") || "- [ADD THE PHONE / EMAIL / WEBSITE USED BY THE SENDER]";

  return [
    "Subject: Complaint about a fake job offer (online recruitment fraud)",
    "",
    "To,",
    "The Cyber Crime Cell / National Cyber Crime Reporting Portal",
    "",
    `Date: ${today}`,
    "Name: [YOUR FULL NAME]",
    "Phone: [YOUR PHONE]    Email: [YOUR EMAIL]",
    "",
    "I want to report a suspected fake job offer that I received through [WHATSAPP / TELEGRAM / LINKEDIN / EMAIL / WEBSITE NAME] on [DATE RECEIVED].",
    "",
    `Job title offered: ${form.title.trim() || "[JOB TITLE]"}`,
    `Summary of the offer: ${summary}${form.description.trim().length > 350 ? "..." : ""}`,
    "",
    "Suspicious points found in the offer:",
    flags,
    "",
    "Contact details used by the sender:",
    contacts,
    "",
    "Money paid / information shared: [AMOUNT, DATE, PAYMENT METHOD AND TRANSACTION ID, OR WHICH DOCUMENTS YOU SHARED. WRITE 'NONE' IF NOTHING]",
    "",
    "Evidence I can provide: screenshots of the chat and the posting, payment receipts, call details.",
    "",
    "I request that this matter be investigated and action be taken against the persons using the above contact details.",
    "",
    `Note: an automated pre-check by JobShield rated this posting ${r.risk_percent}% risk (${r.verdict}). This is guidance, not proof.`,
  ].join("\n");
}

$("draft").addEventListener("click", () => {
  $("complaint-text").value = buildComplaint(lastResult, lastForm);
  $("complaint").hidden = false;
  $("complaint").scrollIntoView({ behavior: "smooth", block: "nearest" });
});

async function copyWithFeedback(btn, text, original) {
  try {
    await navigator.clipboard.writeText(text);
    btn.textContent = "Copied!";
  } catch (e) {
    btn.textContent = "Copy failed";
  }
  setTimeout(() => (btn.textContent = original), 1800);
}

$("copy-draft").addEventListener("click", (e) =>
  copyWithFeedback(e.currentTarget, $("complaint-text").value, "Copy draft"));
$("copy").addEventListener("click", (e) => copyWithFeedback(e.currentTarget, lastReport, "Copy report"));

// ---------- report contacts to the community ----------
$("report").addEventListener("click", async () => {
  const btn = $("report");
  btn.disabled = true;
  try {
    const res = await fetch("/api/community/report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ values: lastResult.entities.map((e) => e.value), category: $("category").value }),
    });
    const data = await res.json();
    $("report-msg").textContent = res.ok ? data.message : data.error;
  } catch (err) {
    $("report-msg").textContent = "Something went wrong.";
    btn.disabled = false;
  }
});

// ---------- analyze ----------
$("form").addEventListener("submit", async (e) => {
  e.preventDefault();
  $("error").textContent = "";
  const btn = $("go");
  btn.disabled = true;
  btn.textContent = "Analyzing...";
  show("loading");
  try {
    const form = readForm();
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Something went wrong.");
    lastResult = data;
    lastForm = form;
    render(data);
  } catch (err) {
    show("empty");
    $("error").textContent = err.message;
  } finally {
    btn.disabled = false;
    btn.textContent = "Analyze posting";
  }
});

$("ex-fake").addEventListener("click", () => fill(EXAMPLES.fake));
$("ex-real").addEventListener("click", () => fill(EXAMPLES.real));