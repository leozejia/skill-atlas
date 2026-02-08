const state = {
  view: 'all-time',
  limit: 80,
  summary: null,
};

const $ = (id) => document.getElementById(id);

const summaryView = $('summary-view');
const limitInput = $('limit-input');
const syncButton = $('sync-btn');
const refreshButton = $('refresh-btn');
const reportButton = $('report-btn');
const jobStatus = $('job-status');
const logBox = $('log-box');
const skillsList = $('skills-list');
const installedCount = $('installed-count');
const installedTopCount = $('installed-top-count');
const missingCount = $('missing-count');
const customPath = $('custom-path');
const sharedPath = $('shared-path');
const customCopy = $('custom-copy');
const sharedCopy = $('shared-copy');

let jobPoller = null;

async function fetchSummary() {
  const view = summaryView.value;
  const limit = Number(limitInput.value) || 80;
  const res = await fetch(`/api/summary?view=${encodeURIComponent(view)}&limit=${limit}`);
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || '加载失败');
  }
  const data = await res.json();
  state.summary = data;
  renderSummary();
}

function renderSummary() {
  if (!state.summary) return;
  const { skills, counts } = state.summary;
  installedCount.textContent = counts.installedTotal;
  installedTopCount.textContent = counts.installedTop;
  missingCount.textContent = counts.missingTop;

  skillsList.innerHTML = '';
  const header = document.createElement('div');
  header.className = 'row header';
  header.innerHTML = `
    <div>#</div>
    <div>Skills</div>
    <div class="source">Source</div>
    <div class="status">状态</div>
  `;
  skillsList.appendChild(header);

  skills.forEach((skill, index) => {
    const row = document.createElement('div');
    row.className = 'row';
    const statusClass = skill.status === 'installed' ? 'tag' : 'tag missing';
    const statusLabel = skill.status === 'installed' ? '已安装' : '未安装';
    row.innerHTML = `
      <div class="mono">${index + 1}</div>
      <div>
        <div class="mono">${skill.name}</div>
        <div class="mono" style="color: #5d6a66; font-size: 12px;">${skill.installs} installs</div>
      </div>
      <div class="source mono">${skill.topSource}</div>
      <div class="status"><span class="${statusClass}">${statusLabel}</span></div>
    `;
    skillsList.appendChild(row);
  });
}

async function startInstall(refresh = false) {
  jobStatus.textContent = '启动中...';
  const payload = {
    view: summaryView.value,
    limit: Number(limitInput.value) || 80,
    resolveMissing: true,
    refresh,
  };
  const res = await fetch('/api/install', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (data.status === 'running') {
    jobStatus.textContent = '任务已在运行';
    return;
  }
  jobStatus.textContent = '任务已启动';
  pollJob();
}

async function pollJob() {
  if (jobPoller) {
    clearTimeout(jobPoller);
  }
  const res = await fetch('/api/job');
  const data = await res.json();
  if (data.running) {
    jobStatus.textContent = `运行中 (PID ${data.pid})`;
    await fetchLog();
    jobPoller = setTimeout(pollJob, 3000);
  } else if (data.pid) {
    jobStatus.textContent = '任务完成，正在刷新列表...';
    await fetchLog();
    await fetchSummary();
  } else {
    jobStatus.textContent = '暂无任务';
  }
}

async function fetchLog() {
  const res = await fetch('/api/log?lines=120');
  if (!res.ok) return;
  const text = await res.text();
  logBox.textContent = text || '暂无日志';
}

async function openReport() {
  const res = await fetch('/api/report');
  if (!res.ok) {
    jobStatus.textContent = '暂无报告';
    return;
  }
  const data = await res.json();
  const payload = JSON.stringify(data, null, 2);
  logBox.textContent = payload;
  jobStatus.textContent = '已加载最新报告';
}

function initCopyButton(btn) {
  if (!btn) return;
  btn.addEventListener('click', () => {
    const value = btn.getAttribute('data-copy');
    if (!value) return;
    navigator.clipboard.writeText(value);
    btn.textContent = '已复制';
    setTimeout(() => {
      btn.textContent = '复制路径';
    }, 1500);
  });
}

async function fetchPaths() {
  const res = await fetch('/api/paths');
  if (!res.ok) return;
  const data = await res.json();
  if (customPath && data.custom) customPath.textContent = data.custom;
  if (sharedPath && data.shared) sharedPath.textContent = data.shared;
  if (customCopy && data.custom) customCopy.setAttribute('data-copy', data.custom);
  if (sharedCopy && data.shared) sharedCopy.setAttribute('data-copy', data.shared);
}

summaryView.addEventListener('change', fetchSummary);
limitInput.addEventListener('change', fetchSummary);
syncButton.addEventListener('click', () => startInstall(false));
refreshButton.addEventListener('click', () => startInstall(true));
reportButton.addEventListener('click', openReport);

initCopyButton(customCopy);
initCopyButton(sharedCopy);
fetchSummary().catch((err) => {
  jobStatus.textContent = `加载失败：${err.message}`;
});
pollJob();
fetchPaths();
