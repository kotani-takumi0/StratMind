/* StratMind Frontend - Dual Pane Workshop UI
 *
 * 役割:
 * - タブ切り替え (Review Questions / Reference Cases)
 * - 「AIレビューを更新する」ボタンクリックでダミーデータを描画
 * - 問いカードの「企画書に反映」ボタンで左ペインのテキストエリアに追記
 */

// 即時実行関数
(() => {
  "use strict";

  function showMessage(type, text) {
    const el = document.getElementById("global-message");
    if (!el) return;

    el.className = "global-message";

    if (!text) {
      el.style.display = "none";
      el.textContent = "";
      return;
    }

    let cls = "message--info";
    if (type === "success") cls = "message--success";
    else if (type === "error") cls = "message--error";

    el.style.display = "block";
    el.classList.add(cls);
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

    questionsTab.classList.toggle("tab--active", isQuestions);
    questionsTab.setAttribute("aria-selected", isQuestions ? "true" : "false");
    questionsPanel.classList.toggle("tab-panel--active", isQuestions);
    questionsPanel.toggleAttribute("hidden", !isQuestions);

    casesTab.classList.toggle("tab--active", !isQuestions);
    casesTab.setAttribute("aria-selected", !isQuestions ? "true" : "false");
    casesPanel.classList.toggle("tab-panel--active", !isQuestions);
    casesPanel.toggleAttribute("hidden", isQuestions);
  }

  function setupTabs() {
    const questionsTab = document.getElementById("tab-questions");
    const casesTab = document.getElementById("tab-cases");
    if (!questionsTab || !casesTab) return;

    questionsTab.addEventListener("click", () => activateTab("questions"));
    casesTab.addEventListener("click", () => activateTab("cases"));
  }

  // Editor helper

  function appendToIdeaBody(text) {
    // idea-bodyというidに入っているエレメントをtextareaという変数に代入
    const textarea = document.getElementById("idea-body");
    // textareがnull（画面上で入力エリアが空）だとこの変数を抜け出す
    if (!textarea) return;

    // textareaにすでに文章が入っているなら改行を二つ入れる。空なら何も入れない（三項演算子を使用）
    const separator = textarea.value ? "\n\n" : "";
    // 元の分に改行とテキスト（AIレビューによる提案文章）を結合
    textarea.value = `${textarea.value}${separator}${text}`;
    
    //「企画書に反映する」というボタンを押したときにtextare（企画書本文）にカーソルが合わせられる。（入力がすぐに始めれる）
    textarea.focus();

    //カーソルをどこから始めてどこを終わりにするか（入力をどこから始めるか）を決める
    //ここでは初めと終わりが同じなので、文章の末尾にカーソルを合わせるという挙動になる
    textarea.selectionStart = textarea.value.length;
    textarea.selectionEnd = textarea.value.length;
  }

  // Question Cards

  function createQuestionCard(question) {
    const card = document.createElement("article");
    card.className = "question-card";
    card.dataset.questionId = question.id;

    const header = document.createElement("div");
    header.className = "question-card__header";

    const label = document.createElement("span");
    label.className = "question-card__label";
    label.textContent = "Review Question";

    const meta = document.createElement("span");
    meta.className = "question-card__meta";
    meta.textContent = question.meta || "";

    // 上で作成したlabel、metaをheaderの子要素とし、headerをcardの子要素とした
    header.appendChild(label);
    header.appendChild(meta);
    card.appendChild(header);

    const body = document.createElement("p");
    body.className = "question-card__body";
    body.textContent = question.text;
    card.appendChild(body);

    const controls = document.createElement("div");
    controls.className = "question-card__controls";

    const reflectButton = document.createElement("button");
    reflectButton.type = "button";
    reflectButton.className = "button button--ghost";
    reflectButton.textContent = "企画書に反映する";
    reflectButton.addEventListener("click", () => {
      const snippet =
        question.reflectSnippet ||
        `【問いへの応答メモ】\n${question.text}\n- `;
      appendToIdeaBody(snippet);
    });

    const status = document.createElement("label");
    status.className = "question-card__status";
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    const statusText = document.createElement("span");
    statusText.textContent = "この問いは検討済みにする";
    // チェックされたら　=>　以降の処理を実行する
    // changeはどのような状態になったら以下の処理が実装されるかを指す
    checkbox.addEventListener("change", () => {
      if (checkbox.checked) {
        statusText.textContent = "検討済み";
        //チェックボタンが押されたら少し薄くなる
        card.style.opacity = "0.7";
      } else {
        statusText.textContent = "この問いは検討済みにする";
        card.style.opacity = "1";
      }
    });

    status.appendChild(checkbox);
    status.appendChild(statusText);

    controls.appendChild(reflectButton);
    controls.appendChild(status);
    card.appendChild(controls);

    return card;
  }

  function renderQuestions(questions) {
    const container = document.getElementById("questions-list");
    if (!container) return;

    container.innerHTML = "";

    if (!Array.isArray(questions) || questions.length === 0) {
      const p = document.createElement("p");
      p.className = "placeholder-text";
      p.textContent =
        "まだ問いは生成されていません。AIレビューを更新してみてください。";
      container.appendChild(p);
      return;
    }

    questions.forEach((q) => {
      const card = createQuestionCard(q);
      container.appendChild(card);
    });
  }

  // Reference Cases

  function createCaseCard(c) {
    const card = document.createElement("article");
    card.className = "case-card";

    const header = document.createElement("div");
    header.className = "case-card__header";

    const title = document.createElement("h3");
    title.className = "case-card__title";
    title.textContent = c.title;

    const badge = document.createElement("span");
    badge.className = "case-card__badge";
    const status = (c.status || "").toLowerCase();
    if (status === "adopted" || status === "採用") {
      badge.classList.add("case-card__badge--adopted");
      badge.textContent = c.status || "adopted";
    } else if (status === "rejected" || status === "不採用") {
      badge.classList.add("case-card__badge--rejected");
      badge.textContent = c.status || "rejected";
    } else {
      badge.textContent = c.status || "unknown";
    }

    header.appendChild(title);
    header.appendChild(badge);
    card.appendChild(header);

    const summary = document.createElement("p");
    summary.className = "case-card__summary";
    summary.textContent = c.summary || "";
    card.appendChild(summary);

    const reason = document.createElement("p");
    reason.className = "case-card__reason";
    reason.textContent = c.main_reason
      ? `主な判断理由: ${c.main_reason}`
      : "";
    card.appendChild(reason);

    return card;
  }

  function renderCases(cases) {
    const container = document.getElementById("cases-list");
    if (!container) return;

    container.innerHTML = "";

    if (!Array.isArray(cases) || cases.length === 0) {
      const p = document.createElement("p");
      p.className = "placeholder-text";
      p.textContent =
        "類似する過去の意思決定ケースはまだ表示されていません。";
      container.appendChild(p);
      return;
    }

    cases.forEach((c) => {
      const card = createCaseCard(c);
      container.appendChild(card);
    });
  }

  async function createIdeas() {
    const titleInput = document.getElementById("data-title");
    const bodyTextarea = document.getElementById("idea-body");

    //送信データ作成
    const sendData = {
      new_idea: {
        title: titleInput.value,
        content: bodyTextarea.value,
      },
      is_domo: true
    };

    try{
      //常に同じURLへPOSTする
      //Fast APIのfetchを使用することで、簡単な呼び出しでHTTPリクエストを発行できる
      //対応するエンドポイントのアクセス先（URL）とHTTPメソッドを指定することでデータを送れる
      // 11/28 16:58 アクセス先のタイポの修正　reveiew_sessions -> review_sessions
      const response = await fetch("http://localhost:8000/api/review_sessions",{
        method: "POST",
        //このリクエストの本文はJSON形式であることを明記
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify(sendData)
      });

      const result = await response.json();
    }
  }

  // Dummy Data & Review Trigger

  function buildQuestions(ideaTitle, ideaBody) {
    const titlePart = ideaTitle || "この企画";
    const lengthHint =
      ideaBody && ideaBody.length > 400
        ? "既にボリュームは十分です。"
        : "まだ書ける余地がありそうです。";

    return [
      {
        id: "q1",
        text: `${titlePart} の「誰のどんな行動を変えるのか」が一文で説明できる状態になっていますか？`,
        meta: "視点: ユーザー価値 / 行動変容",
        reflectSnippet:
          "【行動変容の定義】\n- 対象ユーザー:\n- 現状の行動:\n- 変えたい行動:\n- その結果得られる価値:\n",
      },
      {
        id: "q2",
        text: "主要なユースケースを 3 つに絞り込んだとき、それぞれにとっての「導入前後のビフォー/アフター」はどう変わりますか？",
        meta: "視点: ユースケース / ストーリー",
        reflectSnippet:
          "【主要なユースケース 3 つ】\n1. \n   - 導入前: \n   - 導入後: \n2. \n   - 導入前: \n   - 導入後: \n3. \n   - 導入前: \n   - 導入後: \n",
      },
      {
        id: "q3",
        text: `${lengthHint} いまの企画書からは、最初の 6 ヶ月間で「どの数字を追うのか」が読み取れますか？`,
        meta: "視点: 成長指標 / 初期フェーズ",
        reflectSnippet:
          "【最初の 6 ヶ月で追う指標】\n- 利用: \n- 価値: \n- 収益: \n- 学習: \n",
      },
    ];
  }

  function buildCases() {
    return [
      {
        id: "c1",
        title: "SaaS型ダッシュボードのベータ版提供",
        status: "adopted",
        summary:
          "限定された既存顧客にだけベータ提供し、料金は無料だがフィードバックを重視する方針を採用した。",
        main_reason:
          "技術的不確実性が高く、実運用に耐えうるかの検証を学習目標としたため。",
      },
      {
        id: "c2",
        title: "全機能一括リリース案の見送り",
        status: "rejected",
        summary:
          "全ての機能を一度に出す案は、開発負荷と運用リスクが高く、保守困難と判断された。",
        main_reason:
          "ユーザー価値の 80% を生む中核機能だけに絞った MVP 戦略を優先した。",
      },
    ];
  }

  function runReview() {
    const titleInput = document.getElementById("idea-title");
    const bodyTextarea = document.getElementById("idea-body");
    const title = titleInput ? titleInput.value.trim() : "";
    const body = bodyTextarea ? bodyTextarea.value.trim() : "";

    showMessage("info", "ダミーデータでレビュー結果を更新しました。");

    //現在はここから事前に作成している質問文の配列をquestionsに渡しているが将来的にはLLMが生成した質問を入れたいと考えている
    //これをバックであるPython
    // const questions = buildQuestions(title, body);
    //  const cases = buildCases();

    const idea = createIdeas();

    renderQuestions(questions);
    renderCases(cases);
    activateTab("questions");
  }

  // Init

  document.addEventListener("DOMContentLoaded", () => {
    setupTabs();

    const updateReviewBtn = document.getElementById("update-review-btn");
    if (updateReviewBtn) {
      updateReviewBtn.addEventListener("click", runReview);
    }
  });
})();
