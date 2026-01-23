/* StratMind Frontend - Modern Logic (Japanese + Google Integration) */
(() => {
  "use strict";

  let currentSessionId = null;
  let isGoogleAuthenticated = false;

  function showMessage(type, text) {
    const el = document.getElementById("global-message");
    if (!el) return;

    if (!text) {
      el.style.display = "none";
      el.textContent = "";
      return;
    }

    let cls = "message--info";
    // if (type === "success") cls = "message--success";

    el.style.display = "block";
    el.className = `global-message ${cls}`;
    el.textContent = text;
  }

  // Tabs
  function activateTab(tabId) {
    const questionsTab = document.getElementById("tab-questions");
    const casesTab = document.getElementById("tab-cases");
    const questionsPanel = document.getElementById("panel-questions");
    const casesPanel = document.getElementById("panel-cases");

    if (!questionsTab || !casesTab || !questionsPanel || !casesPanel) return;

    const isQuestions = tabId === "questions";

    questionsTab.classList.toggle("tab-pill--active", isQuestions);
    questionsTab.setAttribute("aria-selected", isQuestions);

    casesTab.classList.toggle("tab-pill--active", !isQuestions);
    casesTab.setAttribute("aria-selected", !isQuestions);

    if (isQuestions) {
      questionsPanel.style.display = "block";
      casesPanel.style.display = "none";
    } else {
      questionsPanel.style.display = "none";
      casesPanel.style.display = "block";
    }
  }

  function setupTabs() {
    const questionsTab = document.getElementById("tab-questions");
    const casesTab = document.getElementById("tab-cases");
    if (!questionsTab || !casesTab) return;

    questionsTab.addEventListener("click", () => activateTab("questions"));
    casesTab.addEventListener("click", () => activateTab("cases"));
  }

  // Editor
  function appendToIdeaBody(text) {
    const textarea = document.getElementById("idea-body");
    if (!textarea) return;

    const separator = textarea.value ? "\n\n" : "";
    textarea.value = `${textarea.value}${separator}${text}`;
    textarea.focus();
    textarea.selectionStart = textarea.value.length;
    textarea.selectionEnd = textarea.value.length;
  }

  // Question Card
  function createQuestionCard(question) {
    const card = document.createElement("article");
    card.className = "question-card";
    card.dataset.questionId = question.id;

    // Header
    const header = document.createElement("div");
    header.className = "question-card__header";

    // Layer Badge
    const layerBadge = document.createElement("span");
    const layerNum = typeof question.layer === 'number' ? question.layer : 1;
    layerBadge.className = `question-card__layer question-card__layer--${layerNum}`;
    layerBadge.textContent = `Layer ${layerNum}`;

    // Meta
    const meta = document.createElement("span");
    meta.style.fontSize = "11px";
    meta.style.color = "#94a3b8";

    const themeMap = {
      "purpose_kpi": "目的・KPI",
      "target_scope": "ターゲット・範囲",
      "execution": "実行体制",
      "finance": "財務・コスト",
      "risk": "リスク",
      "differentiation": "差別化"
    };
    meta.textContent = themeMap[question.theme] || question.theme || "一般";

    header.appendChild(layerBadge);
    header.appendChild(meta);
    card.appendChild(header);

    // Body
    const body = document.createElement("div");
    body.className = "question-card__body";
    body.innerHTML = (question.question || "").replace(/\n/g, "<br>");
    card.appendChild(body);

    // Controls
    const controls = document.createElement("div");
    controls.className = "question-card__controls";

    // Reflect Button
    const reflectBtn = document.createElement("button");
    reflectBtn.className = "reflect-btn";
    reflectBtn.textContent = "本文に挿入";
    reflectBtn.onclick = () => {
      const snippet = question.reflectSnippet || `\n> 問い: ${question.question}\n- 回答: `;
      appendToIdeaBody(snippet);
    };

    // Feedback Checkbox
    const label = document.createElement("label");
    label.className = "feedback-label";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.className = "feedback-checkbox";

    const span = document.createElement("span");
    span.textContent = "この問いで修正した";

    checkbox.addEventListener("change", async () => {
      if (checkbox.checked) {
        card.classList.add("question-card--done");
        span.textContent = "修正/解決済み";

        // API Call
        if (currentSessionId) {
          try {
            await fetch(`http://localhost:8000/api/review_sessions/${currentSessionId}/feedback`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                feedbacks: [{
                  question_id: question.id,
                  usefulness_score: 5,
                  applied: true,
                  note: "Auto-saved via checkbox"
                }]
              })
            });
            console.log("Feedback saved.");
          } catch (e) { console.error(e); }
        }
      } else {
        card.classList.remove("question-card--done");
        span.textContent = "この問いで修正した";
      }
    });

    label.appendChild(checkbox);
    label.appendChild(span);

    controls.appendChild(reflectBtn);
    controls.appendChild(label);
    card.appendChild(controls);

    return card;
  }

  function renderQuestions(questions) {
    const container = document.getElementById("questions-list");
    if (!container) return;
    container.innerHTML = "";

    if (!questions || questions.length === 0) {
      container.innerHTML = `<div class="empty-state"><p>まだ問いは生成されていません。</p></div>`;
      return;
    }

    questions.forEach(q => {
      container.appendChild(createQuestionCard(q));
    });
  }

  // Case Card
  function createCaseCard(c) {
    const card = document.createElement("article");
    card.className = "case-card";
    card.dataset.status = c.status || "unknown"; // for CSS border color

    const title = document.createElement("h3");
    title.className = "case-card__title";
    title.textContent = c.title;

    const status = document.createElement("span");
    status.className = "case-card__status";
    // ステータスの日本語化
    let statusText = c.status;
    if (statusText === 'adopted') statusText = "採用";
    else if (statusText === 'rejected') statusText = "不採用";
    else if (statusText === 'pending') statusText = "保留";

    status.textContent = `${statusText} • ${c.decision_date || "日付不明"}`;

    const summary = document.createElement("p");
    summary.className = "case-card__summary";
    summary.textContent = c.summary ? c.summary.substring(0, 100) + "..." : "";

    card.appendChild(title);
    card.appendChild(status);
    card.appendChild(summary);
    return card;
  }

  function renderCases(cases) {
    const container = document.getElementById("cases-list");
    if (!container) return;
    container.innerHTML = "";

    if (!cases || cases.length === 0) {
      container.innerHTML = `<div class="empty-state"><p>類似事例は見つかりませんでした。</p></div>`;
      return;
    }

    cases.forEach(c => container.appendChild(createCaseCard(c)));
  }

  // API Interaction
  async function createIdeas() {
    const titleInput = document.getElementById("idea-title");
    const bodyTextarea = document.getElementById("idea-body");
    const isDemo = document.getElementById("demo-mode-checkbox").checked;

    const sendData = {
      new_idea: {
        title: titleInput ? titleInput.value : "",
        content: bodyTextarea ? bodyTextarea.value : "",
        purpose: "",
        target: "",
        value: "",
        model: "",
        memo: ""
      },
      is_demo: isDemo
    };

    try {
      showMessage("info", "AIレビューを生成中...");
      const response = await fetch("http://localhost:8000/api/review_sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(sendData)
      });

      if (!response.ok) throw new Error(response.status);
      const result = await response.json();
      showMessage(null, ""); // clear message
      return result;
    } catch (e) {
      console.error(e);
      showMessage("info", "エラー: サーバーに接続できませんでした。");
      return null;
    }
  }

  async function runReview() {
    const data = await createIdeas();
    if (!data) return;

    currentSessionId = data.session_id;
    const { questions, similar_cases } = data;

    renderQuestions(questions);
    renderCases(similar_cases);
    activateTab("questions");
  }

  async function saveSnapshot() {
    if (!currentSessionId) {
      alert("先にAIレビューを実行（セッション作成）してください。");
      return;
    }
    alert("現在のスナップショットを保存しました（デモ）。");
  }

  // --- Google Integration ---

  async function checkGoogleAuth() {
    try {
      const res = await fetch("/api/auth/status");
      if (res.ok) {
        const data = await res.json();
        isGoogleAuthenticated = data.is_authenticated;
      }
    } catch (e) {
      console.error("Auth check failed", e);
    }
  }

  async function openGoogleImport() {
    if (!isGoogleAuthenticated) {
      // Redirect to login
      window.location.href = "/api/auth/login";
      return;
    }

    // Show modal and fetch files
    const dialog = document.getElementById("drive-dialog");
    if (dialog) dialog.showModal();

    fetchDriveFiles();
  }

  async function fetchDriveFiles() {
    const listEl = document.getElementById("drive-files-list");
    if (!listEl) return;
    listEl.innerHTML = '<li class="loading">ファイルを読み込み中...</li>';

    try {
      const res = await fetch("/api/drive/files");
      if (!res.ok) throw new Error("Failed to fetch files");
      const data = await res.json();
      renderDriveFiles(data.files);
    } catch (e) {
      listEl.innerHTML = '<li class="loading" style="color:red">読み込み失敗</li>';
      console.error(e);
    }
  }

  function renderDriveFiles(files) {
    const listEl = document.getElementById("drive-files-list");
    if (!listEl) return;
    listEl.innerHTML = "";

    if (!files || files.length === 0) {
      listEl.innerHTML = '<li class="loading">Googleドキュメントが見つかりませんでした。</li>';
      return;
    }

    files.forEach(file => {
      const li = document.createElement("li");
      li.innerHTML = `
            <svg class="file-item__icon" viewBox="0 0 24 24" fill="currentColor">
               <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/>
            </svg>
            <span class="file-item__name">${file.name}</span>
          `;
      li.onclick = () => importDriveFile(file.id);
      listEl.appendChild(li);
    });
  }

  async function importDriveFile(fileId) {
    const dialog = document.getElementById("drive-dialog");
    // Show loading in dialog/close it? better close and show global loading
    if (dialog) dialog.close();
    showMessage("info", "ドキュメントをインポート中...");

    try {
      const res = await fetch(`/api/drive/import/${fileId}`);
      if (!res.ok) throw new Error("Import failed");
      const data = await res.json();

      const textArea = document.getElementById("idea-body");
      if (textArea) {
        textArea.value = data.content; // Overwrite or append? Overwrite seems logical for "Import"
      }
      showMessage(null, "");
    } catch (e) {
      console.error(e);
      showMessage("error", "インポートに失敗しました。");
    }
  }


  // Init
  document.addEventListener("DOMContentLoaded", () => {
    setupTabs();
    checkGoogleAuth();

    const btnUpdate = document.getElementById("update-review-btn");
    if (btnUpdate) btnUpdate.addEventListener("click", runReview);

    const btnSave = document.getElementById("save-snapshot-btn");
    if (btnSave) btnSave.addEventListener("click", saveSnapshot);

    const btnGoogle = document.getElementById("google-import-btn");
    if (btnGoogle) btnGoogle.addEventListener("click", openGoogleImport);

    const dialog = document.getElementById("drive-dialog");
    const closeBtn = document.getElementById("close-dialog-btn");
    if (closeBtn && dialog) {
      closeBtn.addEventListener("click", () => dialog.close());
    }
  });

})();
