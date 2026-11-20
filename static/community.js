// community.js - the "Check a contact" and "Report a scam contact" forms.

const $ = (id) => document.getElementById(id);

async function postJSON(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return { ok: res.ok, data: await res.json() };
}

$("check-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const box = $("check-result");
  box.hidden = false;
  box.className = "check-result";
  box.textContent = "Checking...";
  try {
    const res = await fetch("/api/community/check?q=" + encodeURIComponent($("check-q").value));
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    if (data.reports === 0) {
      box.className = "check-result safe";
      box.textContent = "No reports for this contact yet. That does not prove it is safe, so still verify it.";
    } else {
      box.className = "check-result " + (data.reports >= 3 ? "danger" : "warning");
      const reasons = data.categories.map((c) => `${c.label} (${c.count})`).join(", ");
      box.textContent = `Reported ${data.reports} time${data.reports === 1 ? "" : "s"}. ${reasons}.`;
    }
  } catch (err) {
    box.className = "check-result warning";
    box.textContent = err.message || "Something went wrong.";
  }
});

$("report-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const msg = $("report-msg");
  msg.textContent = "";
  try {
    const { ok, data } = await postJSON("/api/community/report", {
      values: [$("report-q").value],
      category: $("report-cat").value,
    });
    msg.textContent = ok ? data.message : data.error;
    if (ok && data.added) $("report-q").value = "";
  } catch (err) {
    msg.textContent = "Something went wrong.";
  }
});