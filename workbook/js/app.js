/* Gallicantus workbook UI — vanilla JS, data-driven from GALLICANTUS_DATA. */
(function () {
  "use strict";
  const E = window.GallicantusEngine;
  const $root = document.getElementById("app");

  function el(tag, attrs, ...children) {
    const node = document.createElement(tag);
    if (attrs) {
      for (const [key, value] of Object.entries(attrs)) {
        if (value == null || value === false) continue;
        if (key === "class") node.className = value;
        else if (key === "dataset") Object.assign(node.dataset, value);
        else if (key.startsWith("on") && typeof value === "function") node.addEventListener(key.slice(2).toLowerCase(), value);
        else if (key === "style" && typeof value === "object") Object.assign(node.style, value);
        else if (value === true) node.setAttribute(key, "");
        else node.setAttribute(key, String(value));
      }
    }
    for (const child of children.flat()) {
      if (child == null || child === false) continue;
      node.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
    }
    return node;
  }

  function text(s) { return el("p", null, s); }
  function h2(s) { return el("h2", null, s); }

  function button({ label, variant, onClick, disabled, greek }) {
    const cls = [variant || "", greek ? "greek" : ""].filter(Boolean).join(" ");
    return el("button", { type: "button", class: cls || undefined, disabled: !!disabled, onClick }, label);
  }

  function wrap(...children) {
    return el("div", { class: "wrap" }, ...children);
  }

  function table(columns, rows) {
    const thead = el("thead", null, el("tr", null, ...columns.map((c) => el("th", null, c))));
    const tbody = el(
      "tbody",
      null,
      ...rows.map((row) => el("tr", null, ...row.map((cell) => el("td", null, cell)))),
    );
    return el("table", { class: "data" }, thead, tbody);
  }

  function status(tone, message) {
    return el("div", { class: `status ${tone}`, role: "status" }, message);
  }

  function callout(lead, body) {
    return el("div", { class: "callout info" }, el("div", { class: "lead" }, lead), el("div", null, body));
  }

  function properties(items) {
    return el(
      "div",
      { class: "props" },
      ...items.map((item) =>
        el("div", { class: "row" }, el("div", { class: "label" }, item.label), el("div", { class: "value" }, item.value)),
      ),
    );
  }

  function section({ heading, caption, collapsible, open, children }) {
    if (collapsible) {
      return el(
        "details",
        { class: "section collapsible", open: open ? true : undefined },
        el("summary", null, heading),
        caption ? el("p", { class: "caption" }, caption) : null,
        ...children,
      );
    }
    return el("section", { class: "section" }, heading ? h2(heading) : null, caption ? el("p", { class: "caption" }, caption) : null, ...children);
  }

  function segmented(options, value, onChange) {
    const opts = options.map((opt) => (typeof opt === "string" ? { value: opt, label: opt } : opt));
    const buttons = opts.map((opt) => {
      const btn = button({
        label: opt.label,
        onClick: () => {
          if (opt.value !== value) onChange(opt.value);
        },
      });
      btn.setAttribute("aria-pressed", opt.value === value ? "true" : "false");
      return btn;
    });
    return el("div", { class: "seg", role: "tablist" }, ...buttons);
  }

  function stepper(step, count, onChange, noun) {
    return el(
      "div",
      { class: "stepper" },
      button({
        label: "←",
        onClick: () => onChange(step - 1),
        disabled: step <= 1,
      }),
      el("div", { class: "count" }, `${noun} ${step} of ${count}`),
      button({
        label: "→",
        onClick: () => onChange(step + 1),
        disabled: step >= count,
      }),
    );
  }

  function renderRules(cards) {
    return cards.map((card) =>
      section({
        heading: card.title,
        children: [
          text(card.rule),
          card.columns && card.rows ? table(card.columns, card.rows) : null,
          text(`From the verse: ${card.example}`),
          text(`Not this: ${card.notThis}`),
          text(`Use this: ${card.useThis}`),
          text(card.because),
        ],
      }),
    );
  }

  function getData() {
    if (window.GALLICANTUS_DATA) return Promise.resolve(window.GALLICANTUS_DATA);
    return fetch("data/unit1.json").then((res) => {
      if (!res.ok) throw new Error("Could not load data/unit1.json");
      return res.json();
    });
  }

  getData()
    .then(start)
    .catch((err) => {
      $root.replaceChildren(
        el("div", { class: "error" }, text("The workbook data did not load. Open this folder through a simple static server (see README.md), or make sure js/data.js is present."), el("pre", null, String(err))),
      );
    });

  function start(data) {
    const storage = typeof localStorage !== "undefined" ? localStorage : null;
    let progress = E.readStore(data, storage) || E.emptyProgress(data);
    let storageOn = E.writeStore(data, progress, storage);
    let needAnswer = false;
    let drafts = {};
    let opened = null;
    let chart = "present";
    let ruleView = "here";
    let practiceDraft = [];
    let practicePairs = {};
    let matchPick = null;
    let showModel = false;

    const setProgress = (next) => {
      progress = typeof next === "function" ? next(progress) : next;
      storageOn = E.writeStore(data, progress, storage);
      render();
    };

    function readyIds() {
      return E.readyLessonIds(data);
    }

    function builtLesson() {
      return data.lessons[progress.lessonId];
    }

    function lessonState() {
      return progress.view === "eimi" ? progress.eimi : progress.lessons[progress.lessonId];
    }

    function lessonSteps() {
      const les = builtLesson();
      if (progress.view === "eimi") return data.eimiSteps;
      if (les && les.kind === "review" && les.steps) return les.steps;
      return data.lessonSteps;
    }

    function quizKeys() {
      if (progress.view === "eimi") return data.eimiQuiz;
      const les = builtLesson();
      if (les && les.quizKeys) return les.quizKeys;
      return data.lessonQuiz;
    }

    function practiceKey() {
      return progress.view === "eimi" ? "eimi" : progress.lessonId;
    }

    function items() {
      return E.practiceFor(data, practiceKey());
    }

    function pack() {
      return progress.practice[practiceKey()];
    }

    function setTab(value) {
      needAnswer = false;
      setProgress((current) => ({ ...current, tab: value }));
    }

    function setLessonState(updater) {
      setProgress((current) => {
        if (current.view === "eimi") return { ...current, eimi: updater(current.eimi) };
        return { ...current, lessons: { ...current.lessons, [current.lessonId]: updater(current.lessons[current.lessonId]) } };
      });
    }

    function setPractice(updater) {
      const key = progress.view === "eimi" ? "eimi" : progress.lessonId;
      setProgress((current) => ({
        ...current,
        practice: { ...current.practice, [key]: updater(current.practice[key]) },
      }));
    }

    function quizKey() {
      const step = lessonState().step;
      if (progress.view === "eimi") return step === 4 ? "s0" : null;
      const les = builtLesson();
      if (les && les.quizAtStep) return les.quizAtStep[String(step)] || null;
      if (step === 4) return "c0";
      if (step === 5) return "c1";
      if (step === 6) return "w0";
      if (step === 7) return "w1";
      return null;
    }

    function canAdvance() {
      const step = lessonState().step;
      const key = quizKey();
      return step === lessonSteps() || key === null || lessonState().answers[key] !== undefined;
    }

    function canAdvancePractice() {
      const p = pack();
      const list = items();
      const screens = list.length + 1;
      const practiceItem = p.step <= list.length ? list[p.order[p.step - 1]] : null;
      return p.step >= screens || (practiceItem !== null && p.answers[practiceItem.id] !== undefined);
    }

    function goToStep(next) {
      const step = lessonState().step;
      const target = E.clamp(next, lessonSteps());
      if (target === step) return;
      if (target > step && !canAdvance()) {
        needAnswer = true;
        render();
        return;
      }
      needAnswer = false;
      opened = null;
      setLessonState((current) => {
        const done = [...current.done];
        if (target > step) done[step - 1] = true;
        return { ...current, step: target, done };
      });
    }

    function goToPracticeStep(next) {
      const p = pack();
      const list = items();
      const screens = list.length + 1;
      const target = E.clamp(next, screens);
      if (target === p.step) return;
      if (target > p.step && !canAdvancePractice()) {
        needAnswer = true;
        render();
        return;
      }
      needAnswer = false;
      practiceDraft = [];
      practicePairs = {};
      matchPick = null;
      showModel = false;
      setPractice((current) => {
        const nextState = { ...current, step: target };
        if (target === screens) return E.finalizePractice(nextState, list);
        return nextState;
      });
    }

    function lockAnswer(key, pick, correct) {
      needAnswer = false;
      setLessonState((current) => {
        if (current.answers[key]) return current;
        const done = [...current.done];
        done[current.step - 1] = true;
        return { ...current, done, answers: { ...current.answers, [key]: { pick, correct } } };
      });
    }

    function lockPractice(id, pick, correct) {
      needAnswer = false;
      setPractice((current) => {
        if (current.answers[id]) return current;
        return { ...current, answers: { ...current.answers, [id]: { pick, correct } } };
      });
    }

    function reveal() {
      const keys = quizKeys();
      const steps = lessonSteps();
      setLessonState((current) => {
        const done = [...current.done];
        done[steps - 1] = true;
        return E.finalize({ ...current, done, revealed: true }, keys, steps);
      });
    }

    function redoLesson() {
      needAnswer = false;
      drafts = {};
      opened = null;
      const steps = lessonSteps();
      setLessonState((current) => ({
        ...E.emptyLesson(steps),
        bestScore: current.bestScore,
        lastScore: current.lastScore,
        firstCompletedAt: current.firstCompletedAt,
        lastCompletedAt: current.lastCompletedAt,
        attempts: current.attempts,
      }));
    }

    function redoPractice() {
      needAnswer = false;
      practiceDraft = [];
      practicePairs = {};
      matchPick = null;
      showModel = false;
      const list = items();
      setPractice((current) => ({
        ...E.emptyPractice(list.length),
        order: E.shuffledOrder(list.length),
        bestScore: current.bestScore,
        lastScore: current.lastScore,
        firstCompletedAt: current.firstCompletedAt,
        lastCompletedAt: current.lastCompletedAt,
        attempts: current.attempts,
      }));
    }

    function openMap() {
      needAnswer = false;
      opened = null;
      setProgress((current) => ({ ...current, tab: "Lesson", view: "map" }));
    }

    function openLesson(id) {
      needAnswer = false;
      opened = null;
      drafts = {};
      const extra = data.lessons[id].chartExtra || [];
      chart = extra[0]?.value ?? "present";
      setProgress((current) => ({ ...current, tab: "Lesson", view: "lesson", lessonId: id }));
    }

    function openEimi() {
      needAnswer = false;
      opened = null;
      setProgress((current) => ({ ...current, tab: "Lesson", view: "eimi" }));
    }

    function tapTokens(tokens, offset) {
      return wrap(
        ...tokens.map((token, index) => {
          const id = offset + index;
          return button({
            label: E.tokenLabel(token),
            variant: opened === id ? "primary" : "quiet",
            greek: true,
            onClick: () => {
              opened = opened === id ? null : id;
              render();
            },
          });
        }),
      );
    }

    function glossCard(groups) {
      if (opened === null) return null;
      let cursor = 0;
      let token;
      for (const group of groups) {
        if (opened < cursor + group.length) {
          token = group[opened - cursor];
          break;
        }
        cursor += group.length;
      }
      if (!token) return null;
      const info = E.enrich(token, data.glossParse);
      return el(
        "div",
        { class: "gloss" },
        el(
          "div",
          null,
          el("div", { class: "word" }, info.word),
          el("div", { class: "meaning" }, info.meaning),
          el("div", { class: "meta" }, `lemma: ${info.lemma}${info.parse ? ` · ${info.parse}` : ""}`),
        ),
        button({ label: "×", variant: "quiet", onClick: () => { opened = null; render(); } }),
      );
    }

    function writeScreen(item) {
      const lesson = lessonState();
      const locked = lesson.answers[item.key];
      const builtWords = locked ? locked.pick.split(" ") : drafts[item.key] ?? [];
      const tileList = E.shuffleTiles(item.tiles, item.target, `${item.key}:tiles:${lesson.attempts}`);
      const remaining = tileList.filter((tile) => {
        const used = builtWords.filter((word) => word === tile).length;
        const total = item.tiles.filter((word) => word === tile).length;
        return used < total;
      });
      return section({
        heading: "Build the sentence",
        children: [
          text("Tap the tiles to build this sentence. Tap a word in your sentence to take it out."),
          text(item.english),
          builtWords.length
            ? wrap(
                ...builtWords.map((word, index) =>
                  button({
                    label: word,
                    variant: "primary",
                    greek: true,
                    onClick: () => {
                      if (locked) return;
                      drafts = { ...drafts, [item.key]: (drafts[item.key] ?? []).filter((_, i) => i !== index) };
                      render();
                    },
                  }),
                ),
              )
            : null,
          remaining.length && !locked
            ? wrap(
                ...remaining.map((tile, index) =>
                  button({
                    label: tile,
                    greek: true,
                    onClick: () => {
                      drafts = { ...drafts, [item.key]: [...(drafts[item.key] ?? []), tile] };
                      render();
                    },
                  }),
                ),
              )
            : null,
          !locked
            ? wrap(
                button({
                  label: "Check",
                  variant: "primary",
                  disabled: builtWords.length !== item.target.length,
                  onClick: () => {
                    if (builtWords.length !== item.target.length) return;
                    lockAnswer(item.key, builtWords.join(" "), E.sameWords(builtWords, item.target));
                  },
                }),
                button({
                  label: "Clear",
                  onClick: () => {
                    drafts = { ...drafts, [item.key]: [] };
                    render();
                  },
                }),
              )
            : null,
          locked?.correct ? status("success", `Yes. ${item.target.join(" ")}`) : null,
          locked && !locked.correct ? status("warning", `The sentence is ${item.target.join(" ")}.`) : null,
        ],
      });
    }

    function choiceScreen(item) {
      const lesson = lessonState();
      const picked = lesson.answers[item.key];
      return section({
        heading: "Choose the English",
        children: [
          text(item.greek),
          text(item.prompt),
          wrap(
            ...E.permute(item.options, `${item.key}:${lesson.attempts}`).map((opt) =>
              button({
                label: opt,
                variant: picked?.pick === opt ? "primary" : "quiet",
                onClick: () => lockAnswer(item.key, opt, opt === item.answer),
              }),
            ),
          ),
          picked?.correct ? status("success", item.yes) : null,
          picked && !picked.correct ? status("warning", item.no) : null,
        ],
      });
    }

    function recordBlock(state, keys, outOf, title) {
      const rows = [
        { label: "Lesson", value: state.finalized ? `Complete: ${title}` : "In progress" },
        { label: "This try", value: `${state.finalized ? state.lastScore : E.scoreOf(state, keys)} of ${outOf}` },
      ];
      if (state.bestScore > 0 || state.finalized) rows.push({ label: "Best score", value: `${state.bestScore} of ${outOf}` });
      if (state.attempts > 0) rows.push({ label: "Times completed", value: String(state.attempts) });
      if (state.firstCompletedAt) rows.push({ label: "First completed", value: E.formatStamp(state.firstCompletedAt) });
      if (state.lastCompletedAt) rows.push({ label: "Last completed", value: E.formatStamp(state.lastCompletedAt) });
      return [
        state.finalized ? status("success", `Lesson complete: ${title}.`) : null,
        properties(rows),
        text("You can redo this lesson at any time. Your first completed date and your best score stay in the record."),
        button({ label: "Redo lesson", variant: "primary", onClick: redoLesson }),
      ];
    }

    function johnBody() {
      const built = builtLesson();
      const lesson = lessonState();
      const step = lesson.step;
      if (step === 1) {
        let offset = 0;
        const blocks = [];
        for (const passage of built.passages) {
          blocks.push(text(passage.ref), tapTokens(passage.tokens, offset));
          offset += passage.tokens.length;
        }
        return section({
          heading: built.verses,
          children: [
            text("Tap a word to see its meaning. The list under the verses gathers the same words in one place."),
            ...blocks,
            glossCard(built.passages.map((p) => p.tokens)),
            table(["Greek", "Meaning"], built.words),
          ],
        });
      }
      if (step === 2) {
        return section({
          heading: built.patternHeading,
          children: [text(built.patternText), table(["Greek", "What it is doing"], built.patternRows)],
        });
      }
      if (step === 3) {
        return section({
          heading: "Grammar & Rules",
          children: [
            built.whyIntro ? text(built.whyIntro) : null,
            ...renderRules(built.rules || []),
          ],
        });
      }
      if (step === 4) return choiceScreen(built.choices[0]);
      if (step === 5) return choiceScreen(built.choices[1]);
      if (step === 6) return writeScreen(built.writes[0]);
      if (step === 7) return writeScreen(built.writes[1]);
      return section({
        heading: "Read it again",
        children: [
          text(`${built.verses}, without the glosses.`),
          ...(built.rereadGreek || []).map((line) => text(line)),
          !lesson.revealed ? button({ label: "Show the English", variant: "primary", onClick: reveal }) : null,
          lesson.revealed
            ? [
                ...(built.rereadEnglish || []).map((line) => text(line)),
                progress.lessonId === "1"
                  ? callout(
                      "The Word who was",
                      "John does not start with a teaching about the verb ἦν. He starts with the Word, who already was, who was with God, and who was God. Verse 2 says it again, slowly: this same one was in the beginning with God.",
                    )
                  : built.lookCallout
                    ? callout(built.lookCallout.lead, built.lookCallout.body)
                    : null,
                ...recordBlock(lesson, quizKeys(), quizKeys().length, `${built.title} in ${built.verses}`),
              ]
            : null,
        ].flat(),
      });
    }

    function eimiBody() {
      const eimi = data.eimi;
      const lesson = lessonState();
      const step = lesson.step;
      if (step === 1) {
        return section({
          heading: eimi.passages[0].ref,
          children: [
            text(eimi.intro),
            tapTokens(eimi.passages[0].tokens, 0),
            glossCard([eimi.passages[0].tokens]),
            text(eimi.holdText),
          ],
        });
      }
      if (step === 2) {
        return section({
          heading: eimi.pattern.heading,
          children: [text(eimi.pattern.text), table(["Greek", "English"], eimi.pattern.rows)],
        });
      }
      if (step === 3) {
        return section({
          heading: "Why these forms?",
          children: [text(eimi.whyIntro), ...renderRules(eimi.rules)],
        });
      }
      if (step === 4) {
        const picked = lesson.answers.s0;
        const ask = eimi.ask;
        return section({
          heading: "Other forms of to be",
          children: [
            ...ask.greekLines.map((line) => text(line)),
            text(ask.prompt),
            wrap(
              ...E.permute(ask.options, `s0:${lesson.attempts}`).map((opt) =>
                button({
                  label: opt,
                  variant: picked?.pick === opt ? "primary" : "quiet",
                  onClick: () => lockAnswer("s0", opt, opt === ask.answer),
                }),
              ),
            ),
            picked?.correct ? status("success", ask.yes) : null,
            picked && !picked.correct ? status("warning", ask.no) : null,
          ],
        });
      }
      return section({
        heading: "The verses again",
        children: [
          ...eimi.look.greek.map((line) => text(line)),
          !lesson.revealed ? button({ label: "Show the English", variant: "primary", onClick: reveal }) : null,
          lesson.revealed
            ? [
                ...eimi.look.english.map((line) => text(line)),
                ...recordBlock(lesson, data.eimiQuiz, data.eimiQuiz.length, "ἐστίν, present to be"),
                button({ label: "Back to the unit map", variant: "primary", onClick: openMap }),
              ]
            : null,
        ].flat(),
      });
    }

    function mapStatus(entry, index) {
      const roman = entry.lesson;
      const nums = "0 I II III IV V VI VII VIII IX X XI XII XIII XIV XV XVI XVII XVIII XIX XX XXI XXII XXIII XXIV XXV XXVI XXVII XXVIII XXIX XXX XXXI XXXII XXXIII XXXIV XXXV XXXVI XXXVII XXXVIII XXXIX XL XLI XLII XLIII XLIV XLV XLVI XLVII XLVIII XLIX L".split(" ");
      const n = String(nums.indexOf(roman));
      if (data.lessons[n]) return progress.lessons[n]?.finalized ? "Complete" : "Ready";
      if (roman === "I" || roman === "II" || roman === "III" || roman === "IV") {
        /* fallback */
      }
      return entry.status;
    }

    function mapBody() {
      const ids = readyIds();
      const readyDone = ids.filter((id) => progress.lessons[id]?.finalized).length;
      const nums = "0 I II III IV V VI VII VIII IX X XI XII XIII XIV XV XVI XVII XVIII XIX XX XXI XXII XXIII XXIV XXV XXVI XXVII XXVIII XXIX XXX XXXI XXXII XXXIII XXXIV XXXV XXXVI XXXVII XXXVIII XXXIX XL XLI XLII XLIII XLIV XLV XLVI XLVII XLVIII XLIX L".split(" ");
      const items = data.unitMap.map((row) => {
        const n = String(nums.indexOf(row.lesson));
        const done = !!progress.lessons[n]?.finalized;
        const hasLesson = !!data.lessons[n];
        return el(
          "button",
          {
            type: "button",
            class: "toc-row" + (done ? " done" : ""),
            disabled: !hasLesson,
            onClick: () => hasLesson && openLesson(n),
          },
          el("span", { class: "toc-num" }, row.lesson + (done ? " ✓" : "")),
          el(
            "span",
            { class: "toc-main" },
            el("span", { class: "toc-verses" }, row.verses),
            el("span", { class: "toc-about" }, row.about),
          ),
          el("span", { class: "toc-go", "aria-hidden": "true" }, "›"),
        );
      });
      const eimiDone = !!progress.eimi?.finalized;
      items.splice(
        1,
        0,
        el(
          "button",
          {
            type: "button",
            class: "toc-row toc-extra" + (eimiDone ? " done" : ""),
            onClick: openEimi,
          },
          el("span", { class: "toc-num" }, "★" + (eimiDone ? " ✓" : "")),
          el(
            "span",
            { class: "toc-main" },
            el("span", { class: "toc-verses greek" }, "ἐστίν “is” · 1 John 4:8"),
            el("span", { class: "toc-about" }, "Companion lesson on the present tense of “to be”"),
          ),
          el("span", { class: "toc-go", "aria-hidden": "true" }, "›"),
        ),
      );
      return section({
        heading: "Contents",
        children: [
          text("Read the Gospel of John in Greek from the first verse. Select any lesson to begin."),
          readyDone > 0 ? status("success", `${readyDone} of ${ids.length} lessons complete.`) : null,
          el("div", { class: "toc-list" }, ...items),
        ],
      });
    }

    function chartsBody() {
      const inEimi = progress.view === "eimi";
      const built = builtLesson();
      const extras = inEimi ? [] : built?.chartExtra || [];
      const chartOptions = [...extras.map((x) => ({ value: x.value, label: x.label })), ...data.standingCharts];
      const chartValue = chartOptions.some((o) => o.value === chart) ? chart : chartOptions[0].value;
      const extra = extras.find((item) => item.value === chartValue);
      const standing = data.standingChartTables[chartValue];
      const ruleKey = ruleView === "all" ? "all" : ruleView === "here" ? (inEimi ? "eimi" : progress.lessonId) : ruleView;
      let ruleCards;
      if (ruleKey === "all") {
        ruleCards = [...readyIds().flatMap((id) => data.lessons[id].rules || []), ...(data.eimi.rules || [])];
      } else if (ruleKey === "eimi") ruleCards = data.eimi.rules || [];
      else ruleCards = data.lessons[ruleKey]?.rules || [];
      const ruleOptions = [
        { value: "here", label: "This lesson" },
        ...readyIds().map((id) => ({ value: id, label: `Lesson ${id}` })),
        { value: "eimi", label: "Related" },
        { value: "all", label: "All" },
      ];
      return [
        section({
          heading: "Rules",
          children: [
            segmented(ruleOptions, ruleView, (v) => {
              ruleView = v;
              render();
            }),
            ...renderRules(ruleCards),
          ],
        }),
        section({
          heading: "Charts",
          children: [
            segmented(chartOptions, chartValue, (v) => {
              chart = v;
              render();
            }),
            extra ? table(extra.columns, extra.rows) : null,
            extra?.note ? text(extra.note) : null,
            standing ? table(standing.columns, standing.rows) : null,
            standing?.note ? text(standing.note) : null,
          ],
        }),
      ];
    }

    function wordsBody() {
      const inEimi = progress.view === "eimi";
      const built = builtLesson();
      const heading = inEimi ? "Words in this lesson" : `Words in ${built.verses}`;
      const rows = inEimi ? data.eimi.words : built.words;
      return section({
        heading,
        children: [
          table(["Greek", "Meaning"], rows),
          !inEimi && built.phrases
            ? [h2("Phrases"), table(["Greek", "English"], built.phrases)]
            : null,
        ].flat(),
      });
    }

    function practiceTiles(item, picked) {
      const target = item.target ?? [];
      const tileList = E.shuffleTiles(item.tiles ?? [], target, `${item.id}:tiles:${pack().attempts}`);
      const builtWords = picked ? picked.pick.split(" ") : practiceDraft;
      const remaining = tileList.filter((tile) => {
        const used = builtWords.filter((word) => word === tile).length;
        const total = tileList.filter((word) => word === tile).length;
        return used < total;
      });
      const greekish = !target[0] || /[ἀ-ὠἈ-Ὡά-ώΆ-Ώῖῦῆᾶῆΐΰᾳῃῳ]/.test(target.join(" ")) || /[Ͱ-Ͽἀ-῿]/.test(target.join(""));
      return [
        item.english ? el("div", { class: "prompt-card" }, item.english) : null,
        el(
          "div",
          { class: "answer-tray" + (builtWords.length ? "" : " empty") },
          ...(builtWords.length
            ? builtWords.map((word, index) =>
                button({
                  label: word,
                  variant: "primary",
                  greek: greekish,
                  onClick: () => {
                    if (picked) return;
                    practiceDraft = practiceDraft.filter((_, i) => i !== index);
                    render();
                  },
                }),
              )
            : [el("span", { class: "tray-placeholder" }, "Tap the tiles below to build your answer (tap a placed word to remove it)…")]),
        ),
        remaining.length && !picked
          ? wrap(
              ...remaining.map((tile) =>
                button({
                  label: tile,
                  greek: greekish,
                  onClick: () => {
                    practiceDraft = [...practiceDraft, tile];
                    render();
                  },
                }),
              ),
            )
          : null,
        !picked
          ? wrap(
              button({
                label: "Check",
                variant: "primary",
                disabled: builtWords.length !== target.length,
                onClick: () => {
                  if (builtWords.length !== target.length) return;
                  lockPractice(item.id, builtWords.join(" "), E.sameWords(builtWords, target));
                },
              }),
              button({
                label: "Clear",
                onClick: () => {
                  practiceDraft = [];
                  render();
                },
              }),
            )
          : null,
      ];
    }

    function practiceMatch(item, picked) {
      const pairs = item.pairs ?? [];
      const asId = (key, side) => {
        if (pairs.some((pair) => pair.id === key)) return key;
        return pairs.find((pair) => (side === "left" ? pair.greek === key : pair.english === key))?.id;
      };
      const labelOf = (id, side) => {
        const pair = pairs.find((p) => p.id === id);
        if (!pair) return id;
        return side === "left" ? pair.greek : pair.english;
      };
      let draft = practicePairs;
      if (picked) {
        try {
          const parsed = JSON.parse(picked.pick);
          const next = {};
          if (parsed && typeof parsed === "object") {
            for (const [key, value] of Object.entries(parsed)) {
              if (typeof value !== "string") continue;
              const left = asId(key, "left");
              const right = asId(value, "right");
              if (left && right) next[left] = right;
            }
          }
          draft = next;
        } catch {
          draft = {};
        }
      }
      const lefts = pairs;
      const rights = E.derange(pairs, `${item.id}:${pack().attempts}`, (a, b) => a.id === b.id);
      const usedL = new Set(Object.keys(draft));
      const usedR = new Set(Object.values(draft));
      const onLeft = (value) => {
        if (picked) return;
        if (usedL.has(value)) {
          const next = { ...draft };
          delete next[value];
          practicePairs = next;
          matchPick = null;
          render();
          return;
        }
        if (matchPick?.side === "right") {
          practicePairs = { ...draft, [value]: matchPick.value };
          matchPick = null;
          render();
          return;
        }
        matchPick = { side: "left", value };
        render();
      };
      const onRight = (value) => {
        if (picked) return;
        if (usedR.has(value)) {
          const next = { ...draft };
          for (const key of Object.keys(next)) if (next[key] === value) delete next[key];
          practicePairs = next;
          matchPick = null;
          render();
          return;
        }
        if (matchPick?.side === "left") {
          practicePairs = { ...draft, [matchPick.value]: value };
          matchPick = null;
          render();
          return;
        }
        matchPick = { side: "right", value };
        render();
      };
      const allPaired = pairs.every((pair) => !!draft[pair.id]);
      const allCorrect = pairs.every((pair) => draft[pair.id] === pair.id);
      return [
        text("Tap a Greek phrase, then the English that matches it. Tap a pair to undo it."),
        Object.keys(draft).length
          ? wrap(
              ...Object.entries(draft).map(([leftId, rightId]) =>
                button({
                  label: `${labelOf(leftId, "left")} — ${labelOf(rightId, "right")}`,
                  variant: "primary",
                  onClick: () => onLeft(leftId),
                }),
              ),
            )
          : null,
        el(
          "div",
          { class: "row-2" },
          el(
            "div",
            null,
            ...lefts
              .filter((pair) => !usedL.has(pair.id))
              .map((pair) =>
                button({
                  label: pair.greek,
                  variant: matchPick?.side === "left" && matchPick.value === pair.id ? "primary" : "quiet",
                  greek: true,
                  onClick: () => onLeft(pair.id),
                }),
              ),
          ),
          el(
            "div",
            null,
            ...rights
              .filter((pair) => !usedR.has(pair.id))
              .map((pair) =>
                button({
                  label: pair.english,
                  variant: matchPick?.side === "right" && matchPick.value === pair.id ? "primary" : "quiet",
                  onClick: () => onRight(pair.id),
                }),
              ),
          ),
        ),
        !picked
          ? button({
              label: "Check",
              variant: "primary",
              disabled: !allPaired,
              onClick: () => {
                if (!allPaired) return;
                lockPractice(item.id, JSON.stringify(draft), allCorrect);
              },
            })
          : null,
      ];
    }

    function practiceBody() {
      const key = practiceKey();
      const list = items();
      const p = pack();
      const heading =
        key === "eimi" ? `Practice · Related · ${data.eimi.practiceTitle}` : `Practice · Lesson ${key} · ${data.lessons[key].practiceTitle}`;
      const recordRows = [{ label: "This try", value: `${p.finalized ? p.lastScore : E.practiceScore(p, list)} of ${list.length}` }];
      if (p.bestScore > 0 || p.finalized) recordRows.push({ label: "Best score", value: `${p.bestScore} of ${list.length}` });
      if (p.attempts > 0) recordRows.push({ label: "Times completed", value: String(p.attempts) });
      if (p.firstCompletedAt) recordRows.push({ label: "First completed", value: E.formatStamp(p.firstCompletedAt) });
      if (p.lastCompletedAt) recordRows.push({ label: "Last completed", value: E.formatStamp(p.lastCompletedAt) });
      const practiceItem = p.step <= list.length ? list[p.order[p.step - 1]] : null;
      if (!practiceItem) {
        return section({
          heading,
          children: [
            p.finalized ? status("success", `This try: ${p.lastScore} of ${list.length}.`) : null,
            properties(recordRows),
            text("Practice is separate from the lesson. You can do it again at any time. Your best score stays in the record."),
            button({ label: "Practice again", variant: "primary", onClick: redoPractice }),
          ],
        });
      }
      const picked = p.answers[practiceItem.id];
      const kind = practiceItem.kind ?? "choose";
      const hideGreek =
        practiceItem.greek &&
        practiceItem.greek.replace(/[*.]/g, "").trim() === (practiceItem.answer ?? "").replace(/\./g, "").trim();
      return section({
        heading,
        children: [
          text(practiceItem.ref),
          practiceItem.greek && !hideGreek ? text(practiceItem.greek) : null,
          text(practiceItem.prompt),
          kind === "choose"
            ? wrap(
                ...E.permute(practiceItem.options ?? [], `${practiceItem.id}:${p.attempts}`).map((opt) =>
                  button({
                    label: opt,
                    variant: picked?.pick === opt ? "primary" : "quiet",
                    onClick: () => lockPractice(practiceItem.id, opt, opt === practiceItem.answer),
                  }),
                ),
              )
            : null,
          kind === "tiles" || kind === "capstone" ? practiceTiles(practiceItem, picked) : null,
          kind === "match" ? practiceMatch(practiceItem, picked) : null,
          picked?.correct ? status("success", practiceItem.yes) : null,
          picked && !picked.correct ? status("warning", practiceItem.no) : null,
          kind === "capstone" && picked
            ? showModel
              ? text(`Model: ${practiceItem.model}`)
              : button({ label: "Show a model translation", onClick: () => { showModel = true; render(); } })
            : null,
        ].flat(),
      });
    }

    function header() {
      if (progress.view === "eimi") {
        return section({
          heading: data.eimi.heading,
          children: [
            text(data.eimi.blurb),
            button({ label: "Back to the unit map", onClick: openMap }),
            progress.eimi.finalized ? status("success", "ἐστίν lesson complete.") : null,
          ],
        });
      }
      const built = builtLesson();
      const lesson = lessonState();
      return section({
        heading: `Lesson ${progress.lessonId}: ${built.title}`,
        children: [
          text(built.verses),
          button({ label: "Unit map", onClick: openMap }),
          progress.lessonId === "1"
            ? button({ label: "Related: ἐστίν “is” (1 John 4:8 and more)", onClick: openEimi })
            : null,
          lesson.finalized ? status("success", "Lesson complete.") : null,
        ],
      });
    }

    function sourcesBlock() {
      return section({
        heading: "Sources",
        collapsible: true,
        open: false,
        caption: storageOn
          ? "Your place and score are saved on this device."
          : "This browser would not save your place. Progress lasts only while the page is open.",
        children: [
          text(data.sources.text),
          el(
            "div",
            { class: "links" },
            ...data.sources.links.map((link) =>
              el("div", null, el("a", { href: link.href, target: "_blank", rel: "noopener noreferrer" }, link.title), el("span", { class: "site" }, link.site)),
            ),
          ),
        ],
      });
    }

    function render() {
      const { tab, view } = progress;
      const showLessonNav = tab === "Lesson" && view !== "map";
      const showPracticeNav = tab === "Practice";
      const lesson = lessonState();
      const p = pack();
      const list = items();
      const practiceItem = p.step <= list.length ? list[p.order[p.step - 1]] : null;
      const qk = quizKey();

      const body = [];
      body.push(segmented(["Lesson", "Charts", "Words", "Practice"], tab, setTab));
      if (tab === "Lesson" && view === "map") body.push(mapBody());
      if (tab === "Lesson" && view === "lesson") body.push(header(), johnBody());
      if (tab === "Lesson" && view === "eimi") body.push(header(), eimiBody());
      if (tab === "Charts") body.push(...chartsBody());
      if (tab === "Words") body.push(wordsBody());
      if (tab === "Practice") body.push(practiceBody());
      if (showLessonNav && needAnswer && !canAdvance()) body.push(el("p", { class: "hint" }, "Choose an answer, then use the arrow to go on."));
      if (showLessonNav && qk && lesson.answers[qk] && lesson.step !== lessonSteps()) {
        body.push(el("p", { class: "hint" }, "Use the arrow to go on to the next step."));
      }
      if (showPracticeNav && needAnswer && !canAdvancePractice()) {
        body.push(el("p", { class: "hint" }, "Answer this item, then use the arrow to go on."));
      }
      if (showPracticeNav && practiceItem && p.answers[practiceItem.id]) {
        body.push(el("p", { class: "hint" }, "Use the arrow to go on to the next step."));
      }
      if ((tab === "Lesson" && view !== "map") || tab === "Practice") body.push(el("div", { class: "stepper-space", "aria-hidden": "true" }));

      const float = [];
      if (showLessonNav) {
        const label = view === "eimi" ? E.eimiSectionLabel(lesson.step) : E.sectionLabel(lesson.step);
        float.push(
          el(
            "div",
            { class: "floating" },
            el("div", { class: "floating-inner" }, el("div", { class: "step-label" }, label), stepper(lesson.step, lessonSteps(), goToStep, "Step")),
          ),
        );
      }
      if (showPracticeNav) {
        const screens = list.length + 1;
        float.push(
          el(
            "div",
            { class: "floating" },
            el(
              "div",
              { class: "floating-inner" },
              el("div", { class: "step-label" }, p.step <= list.length ? "Item" : "Score"),
              stepper(p.step, screens, goToPracticeStep, "Step"),
            ),
          ),
        );
      }

      $root.replaceChildren(
        el("header", { class: "page-header" }, el("h1", null, data.title)),
        ...body,
        ...float,
      );
    }

    render();
    window.__gallicantus = { data, getProgress: () => progress, openLesson, openEimi, openMap, setTab };
  }
})();
