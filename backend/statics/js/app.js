/* global document, window, fetch */

(() => {
  "use strict";

  let currentSessionId = null;

  function parseTags(raw) {
    if (!raw) return [];
    return raw
      .split(",")
      .map((t) => t.trim())
      .filter((t) => t.length > 0);
  }

  function showMessage(type, text) {
    const el = document.getElementById("global-message");
    if (!el) return;

    el.className = "";
    el.textContent = "";

    if (!text) {
      el.style.display = "none";
      return;
    }

    let cls = "message--info";
    if (type === "success") cls = "message--success";
    else if (type === "error") cls = "message--error";

    el.classList.add(cls);
    el.textContent = text;
  }

  function createQuestionCard(question) {
    const card = document.createElement("div");
    card.className = "question-card";
    card.dataset.questionId = question.id;

    // ヘッダー（レイヤー・テーマ）
    const header = document.createElement("div");
    header.className = "question-header";

    const layerSpan = document.createElement("span");
    layerSpan.className = "question-layer";
    layerSpan.textContent = `L${question.layer}`;

    const themeSpan = document.createElement("span");
    themeSpan.className = "question-theme";
    themeSpan.textContent = question.theme || "";

    header.appendChild(layerSpan);
    header.appendChild(themeSpan);
    card.appendChild(header);

    // 問い本文
    const textP = document.createElement("p");
    textP.className = "question-text";
    textP.textContent = question.question;
    card.appendChild(textP);

    // 関連ケースボタン
    const relatedDiv = document.createElement("div");
    relatedDiv.className = "related-cases";

    if (Array.isArray(question.based_on_case_ids) && question.based_on_case_ids.length > 0) {
      question.based_on_case_ids.forEach((caseId) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "view-case-btn";
        btn.dataset.caseId = caseId;
        btn.textContent = `関連ケースを見る (${caseId})`;
        btn.addEventListener("click", () => handleCaseDetailClick(caseId));
        relatedDiv.appendChild(btn);
      });
    }

    card.appendChild(relatedDiv);

    // フィードバック入力エリア
    const feedbackDiv = document.createElement("div");
    feedbackDiv.className = "feedback-controls";

    const labelScore = document.createElement("label");
    labelScore.textContent = "この問いはあなたの企画のブラッシュアップに役立ちましたか？（1〜5）";
    feedbackDiv.appendChild(labelScore);

    const select = document.createElement("select");
    select.className = "usefulness-score";
    const emptyOpt = document.createElement("option");
    emptyOpt.value = "";
    emptyOpt.textContent = "評価を選択";
    select.appendChild(emptyOpt);
    for (let i = 1; i <= 5; i += 1) {
      const opt = document.createElement("option");
      opt.value = String(i);
      opt.textContent = String(i);
      select.appendChild(opt);
    }
    feedbackDiv.appendChild(select);

    const labelApplied = document.createElement("label");
    labelApplied.textContent = "この問いをきっかけに企画内容を修正・追記しましたか？";
    feedbackDiv.appendChild(labelApplied);

    const appliedCheckbox = document.createElement("input");
    appliedCheckbox.type = "checkbox";
    appliedCheckbox.className = "applied-checkbox";
    feedbackDiv.appendChild(appliedCheckbox);

    const labelNote = document.createElement("label");
    labelNote.textContent = "どのような修正・追記をしたか、簡単にメモしてください（任意）。";
    feedbackDiv.appendChild(labelNote);

    const noteTextarea = document.createElement("textarea");
    noteTextarea.className = "feedback-note";
    feedbackDiv.appendChild(noteTextarea);

    card.appendChild(feedbackDiv);

    return card;
  }

  function renderQuestions(questions) {
    const section = document.getElementById("questions-section");
    if (!section) return;

    section.innerHTML = "";

    if (!Array.isArray(questions) || questions.length === 0) {
      section.textContent =
        "問いを生成できませんでした。入力内容を見直してもう一度お試しください。";
      return;
    }

    questions.forEach((q) => {
      const card = createQuestionCard(q);
      section.appendChild(card);
    });
  }

  function renderCases(cases) {
    const section = document.getElementById("cases-section");
    if (!section) return;

    section.innerHTML = "";

    if (!Array.isArray(cases) || cases.length === 0) {
      section.textContent = "類似する過去の意思決定ケースは見つかりませんでした。";
      return;
    }

    cases.forEach((c) => {
      const card = document.createElement("div");
      card.className = "case-card";

      const titleEl = document.createElement("h3");
      titleEl.className = "case-title";
      titleEl.textContent = c.title;
      card.appendChild(titleEl);

      const statusEl = document.createElement("span");
      statusEl.className = "case-status";
      statusEl.textContent = c.status;
      card.appendChild(statusEl);

      const tagsEl = document.createElement("div");
      tagsEl.className = "case-tags";
      if (Array.isArray(c.tags)) {
        tagsEl.textContent = c.tags.join(", ");
      }
      card.appendChild(tagsEl);

      const summaryEl = document.createElement("p");
      summaryEl.className = "case-summary";
      summaryEl.textContent = c.summary || "";
      card.appendChild(summaryEl);

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "case-detail-btn";
      btn.dataset.caseId = c.id;
      btn.textContent = "詳細を見る";
      btn.addEventListener("click", () => handleCaseDetailClick(c.id));
      card.appendChild(btn);

      section.appendChild(card);
    });
  }

  async function handleCaseDetailClick(caseId) {
    const modal = document.getElementById("case-detail-modal");
    if (!modal) return;

    modal.textContent = "読み込み中...";

    try {
      const res = await fetch(`/api/decision_cases/${encodeURIComponent(caseId)}`);
      if (!res.ok) {
        let msg = "ケース詳細の取得に失敗しました";
        try {
          const err = await res.json();
          if (err && err.message) msg = err.message;
        } catch (e) {
          // ignore
        }
        showMessage("error", msg);
        modal.textContent = msg;
        return;
      }

      const data = await res.json();
      modal.innerHTML = "";

      const title = document.createElement("h3");
      title.textContent = `${data.id} / ${data.title}`;
      modal.appendChild(title);

      const status = document.createElement("p");
      status.textContent = `ステータス: ${data.status}`;
      modal.appendChild(status);

      const dateLevel = document.createElement("p");
      const datePart = data.decision_date ? `決定日: ${data.decision_date}` : "";
      const levelPart = data.decision_level ? ` / 決裁レベル: ${data.decision_level}` : "";
      dateLevel.textContent = `${datePart}${levelPart}`;
      modal.appendChild(dateLevel);

      const tags = document.createElement("p");
      tags.textContent = Array.isArray(data.tags)
        ? `タグ: ${data.tags.join(", ")}`
        : "";
      modal.appendChild(tags);

      const summary = document.createElement("p");
      summary.textContent = data.summary || "";
      modal.appendChild(summary);

      const reason = document.createElement("p");
      reason.textContent = data.main_reason ? `main_reason: ${data.main_reason}` : "";
      modal.appendChild(reason);
    } catch (err) {
      console.error(err);
      showMessage("error", "ケース詳細の取得に失敗しました");
      modal.textContent = "ケース詳細の取得に失敗しました";
    }
  }

  async function submitNewIdea(event) {
    event.preventDefault();

    const titleInput = document.getElementById("idea-title");
    const purposeInput = document.getElementById("idea-purpose");
    const targetInput = document.getElementById("idea-target");
    const valueInput = document.getElementById("idea-value");
    const modelInput = document.getElementById("idea-model");
    const memoInput = document.getElementById("idea-memo");
    const tagsInput = document.getElementById("idea-tags");
    const startBtn = document.getElementById("start-review-btn");

    if (!titleInput || !startBtn) return;

    const payload = {
      new_idea: {
        title: titleInput.value || "",
        purpose: purposeInput ? purposeInput.value : "",
        target: targetInput ? targetInput.value : "",
        value: valueInput ? valueInput.value : "",
        model: modelInput ? modelInput.value : "",
        memo: memoInput ? memoInput.value : "",
      },
      tags: parseTags(tagsInput ? tagsInput.value : ""),
    };

    startBtn.disabled = true;
    const originalLabel = startBtn.textContent;
    startBtn.textContent = "送信中…";
    showMessage("info", "自己レビューの問いを生成しています…");

    try {
      const res = await fetch("/api/review_sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        let msg = "自己レビューの開始に失敗しました。";
        try {
          const err = await res.json();
          if (err && err.message) msg = err.message;
        } catch (e) {
          // ignore
        }
        showMessage("error", msg);
        return;
      }

      const data = await res.json();
      currentSessionId = data.session_id || null;

      renderQuestions(data.questions || []);
      renderCases(data.similar_cases || []);

      showMessage("success", "自己レビュー用の問いを生成しました。");
    } catch (err) {
      console.error(err);
      showMessage("error", "自己レビューの開始に失敗しました。ネットワーク状況を確認してください。");
    } finally {
      startBtn.disabled = false;
      startBtn.textContent = originalLabel;
    }
  }

  async function submitFeedback() {
    const btn = document.getElementById("submit-feedback-btn");
    if (!btn) return;

    if (!currentSessionId) {
      showMessage("error", "先に自己レビューを開始してください。");
      return;
    }

    const cards = Array.from(document.querySelectorAll(".question-card"));
    if (cards.length === 0) {
      showMessage("error", "送信できる問いがありません。");
      return;
    }

    const feedbacks = cards.map((card) => {
      const questionId = card.dataset.questionId;
      const scoreSelect = card.querySelector(".usefulness-score");
      const appliedCheckbox = card.querySelector(".applied-checkbox");
      const noteTextarea = card.querySelector(".feedback-note");

      return {
        question_id: questionId,
        usefulness_score: scoreSelect && scoreSelect.value ? Number(scoreSelect.value) : null,
        applied: !!(appliedCheckbox && appliedCheckbox.checked),
        note: noteTextarea && noteTextarea.value ? noteTextarea.value : "",
      };
    });

    btn.disabled = true;
    const originalLabel = btn.textContent;
    btn.textContent = "送信中…";
    showMessage("info", "フィードバックを送信しています…");

    try {
      const res = await fetch(
        `/api/review_sessions/${encodeURIComponent(currentSessionId)}/feedback`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ feedbacks }),
        }
      );

      if (!res.ok) {
        let msg = "フィードバックの送信に失敗しました。";
        try {
          const err = await res.json();
          if (err && err.message) msg = err.message;
        } catch (e) {
          // ignore
        }
        showMessage("error", msg);
        return;
      }

      showMessage("success", "フィードバックを保存しました。ありがとうございました。");
    } catch (err) {
      console.error(err);
      showMessage("error", "フィードバックの送信に失敗しました。ネットワーク状況を確認してください。");
    } finally {
      btn.disabled = false;
      btn.textContent = originalLabel;
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("new-idea-form");
    const feedbackBtn = document.getElementById("submit-feedback-btn");

    if (form) {
      form.addEventListener("submit", submitNewIdea);
    }

    if (feedbackBtn) {
      feedbackBtn.addEventListener("click", submitFeedback);
    }
  });
})();
