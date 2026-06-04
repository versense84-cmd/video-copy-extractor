const urlForm = document.querySelector("#urlForm");
const uploadForm = document.querySelector("#uploadForm");
const statusDot = document.querySelector("#statusDot");
const statusText = document.querySelector("#statusText");
const progressList = document.querySelector("#progressList");
const resultPanel = document.querySelector("#resultPanel");
const resultText = document.querySelector("#resultText");
const copyBtn = document.querySelector("#copyBtn");
const viewTabs = Array.from(document.querySelectorAll(".view-tab"));
let currentJobId = null;
let currentResult = null;
let currentView = "paragraph_text";
let pollTimer = null;

function setStatus(status, message) {
  statusDot.className = `dot ${status || ""}`;
  statusText.textContent = message || "处理中";
}

function renderProgress(items = []) {
  progressList.innerHTML = "";
  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    progressList.appendChild(li);
  });
}

function showResult(result, jobId) {
  currentResult = result;
  resultPanel.classList.remove("hidden");
  renderView();
  document.querySelector("#downloadTxt").href = `/api/download/${jobId}/txt`;
  document.querySelector("#downloadSrt").href = `/api/download/${jobId}/srt`;
  document.querySelector("#downloadMd").href = `/api/download/${jobId}/md`;
  document.querySelector("#downloadJson").href = `/api/download/${jobId}/json`;
}

function renderView() {
  if (!currentResult) return;
  resultText.value = currentResult[currentView] || "";
}

async function startPolling(jobId) {
  currentJobId = jobId;
  if (pollTimer) clearInterval(pollTimer);

  const poll = async () => {
    const response = await fetch(`/api/jobs/${jobId}`);
    const job = await response.json();
    setStatus(job.status, job.message);
    renderProgress(job.progress || []);

    if (job.status === "done") {
      clearInterval(pollTimer);
      showResult(job.result, jobId);
    }
    if (job.status === "error") {
      clearInterval(pollTimer);
      resultPanel.classList.add("hidden");
    }
  };

  await poll();
  pollTimer = setInterval(poll, 1500);
}

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((item) => item.classList.remove("active"));
    tab.classList.add("active");
    const isUrl = tab.dataset.mode === "url";
    urlForm.classList.toggle("hidden", !isUrl);
    uploadForm.classList.toggle("hidden", isUrl);
  });
});

urlForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(urlForm);
  setStatus("running", "提交任务");
  renderProgress([]);
  resultPanel.classList.add("hidden");
  const response = await fetch("/api/extract", { method: "POST", body: formData });
  if (!response.ok) {
    const error = await response.json();
    setStatus("error", error.detail || "提交失败");
    return;
  }
  const data = await response.json();
  startPolling(data.job_id);
});

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(uploadForm);
  setStatus("running", "上传文件");
  renderProgress([]);
  resultPanel.classList.add("hidden");
  const response = await fetch("/api/upload", { method: "POST", body: formData });
  if (!response.ok) {
    const error = await response.json();
    setStatus("error", error.detail || "上传失败");
    return;
  }
  const data = await response.json();
  startPolling(data.job_id);
});

viewTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    viewTabs.forEach((item) => item.classList.remove("active"));
    tab.classList.add("active");
    currentView = tab.dataset.view;
    renderView();
  });
});

copyBtn.addEventListener("click", async () => {
  await navigator.clipboard.writeText(resultText.value);
  copyBtn.textContent = "已复制";
  setTimeout(() => {
    copyBtn.textContent = "复制";
  }, 1200);
});
