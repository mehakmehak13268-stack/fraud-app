const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");
const fname = document.getElementById("fname");
const uploadBtn = document.getElementById("upload-btn");
const loadingNote = document.getElementById("loading-note");
const errorBox = document.getElementById("error-box");
const resultsPanel = document.getElementById("results-panel");

let selectedFile = null;

["dragover", "dragenter"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.add("is-drag");
  })
);
["dragleave", "drop"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.remove("is-drag");
  })
);
dropzone.addEventListener("drop", (e) => {
  if (e.dataTransfer.files.length) setFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener("change", (e) => {
  if (e.target.files.length) setFile(e.target.files[0]);
});

function setFile(file) {
  selectedFile = file;
  fname.textContent = file.name;
  uploadBtn.disabled = false;
}

uploadBtn.addEventListener("click", async () => {
  if (!selectedFile) return;
  errorBox.classList.remove("is-visible");
  uploadBtn.disabled = true;
  loadingNote.style.display = "inline";

  const formData = new FormData();
  formData.append("file", selectedFile);

  try {
    const res = await fetch("/batch/upload", { method: "POST", body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Upload failed.");
    renderResults(data);
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.classList.add("is-visible");
  } finally {
    uploadBtn.disabled = false;
    loadingNote.style.display = "none";
  }
});

function renderResults(data) {
  document.getElementById("sum-rows").textContent = data.summary.n_rows;
  document.getElementById("sum-flagged").textContent = data.summary.n_flagged;
  document.getElementById("sum-rate").textContent =
    Math.round(data.summary.flag_rate * 1000) / 10 + "%";

  const rows = data.rows || [];
  const head = document.getElementById("table-head");
  const body = document.getElementById("table-body");
  head.innerHTML = "";
  body.innerHTML = "";

  if (rows.length === 0) {
    resultsPanel.style.display = "block";
    return;
  }

  const cols = Object.keys(rows[0]);
  cols.forEach((c) => {
    const th = document.createElement("th");
    th.textContent = c;
    head.appendChild(th);
  });

  rows.forEach((row) => {
    const tr = document.createElement("tr");
    if (row.is_flagged) tr.classList.add("flagged");
    cols.forEach((c) => {
      const td = document.createElement("td");
      td.textContent = row[c];
      tr.appendChild(td);
    });
    body.appendChild(tr);
  });

  resultsPanel.style.display = "block";
}
