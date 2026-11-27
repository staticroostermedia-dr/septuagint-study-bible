/* Gallicantus workbook — progress, shuffle, and scoring (no DOM). */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.GallicantusEngine = api;
})(typeof window !== "undefined" ? window : globalThis, function () {
  "use strict";

  function permute(arr, seed) {
    const out = [...arr];
    let h = 2166136261;
    for (let i = 0; i < seed.length; i += 1) h = Math.imul(h ^ seed.charCodeAt(i), 16777619);
    for (let i = out.length - 1; i > 0; i -= 1) {
      h = (Math.imul(h, 1664525) + 1013904223) | 0;
      const j = (h >>> 0) % (i + 1);
      const tmp = out[i];
      out[i] = out[j];
      out[j] = tmp;
    }
    return out;
  }

  function derange(arr, seed, same) {
    const eq = same || ((a, b) => a === b);
    if (arr.length < 2) return [...arr];
    let out = permute(arr, seed);
    let n = 0;
    while (n < 16 && out.some((item, i) => eq(item, arr[i]))) {
      n += 1;
      out = permute(arr, `${seed}:d${n}`);
    }
    if (out.some((item, i) => eq(item, arr[i]))) out = [...arr.slice(1), arr[0]];
    return out;
  }

  function tilesInTargetOrder(bank, target) {
    if (!target || target.length === 0) return false;
    const need = [...target];
    const seq = [];
    for (const tile of bank) {
      const at = need.indexOf(tile);
      if (at >= 0) {
        seq.push(tile);
        need.splice(at, 1);
      }
    }
    return seq.length === target.length && seq.every((word, i) => word === target[i]);
  }

  function shuffleTiles(tiles, target, seed) {
    if (tiles.length < 2) return [...tiles];
    let out = permute(tiles, seed);
    let n = 0;
    while (n < 16 && tilesInTargetOrder(out, target)) {
      n += 1;
      out = permute(tiles, `${seed}:t${n}`);
    }
    if (tilesInTargetOrder(out, target)) {
      const shift = Math.min(2, tiles.length - 1);
      out = [...tiles.slice(shift), ...tiles.slice(0, shift)];
      if (tilesInTargetOrder(out, target)) out = [...tiles].reverse();
    }
    return out;
  }

  function sameWords(a, b) {
    return a.length === b.length && a.every((word, i) => word === b[i]);
  }

  function sequentialOrder(count) {
    return Array.from({ length: count }, (_, i) => i);
  }

  function shuffledOrder(count) {
    const arr = sequentialOrder(count);
    for (let i = arr.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      const temp = arr[i];
      arr[i] = arr[j];
      arr[j] = temp;
    }
    return arr;
  }

  function emptyLesson(steps) {
    return {
      step: 1,
      done: Array.from({ length: steps }, () => false),
      answers: {},
      bestScore: 0,
      lastScore: 0,
      firstCompletedAt: null,
      lastCompletedAt: null,
      attempts: 0,
      finalized: false,
      revealed: false,
    };
  }

  function emptyPractice(count) {
    return {
      order: sequentialOrder(count),
      step: 1,
      answers: {},
      bestScore: 0,
      lastScore: 0,
      firstCompletedAt: null,
      lastCompletedAt: null,
      attempts: 0,
      finalized: false,
    };
  }

  function clamp(value, max) {
    if (value < 1) return 1;
    if (value > max) return max;
    return value;
  }

  function scoreOf(lesson, keys) {
    return keys.reduce((sum, key) => sum + (lesson.answers[key]?.correct ? 1 : 0), 0);
  }

  function quizzesDone(lesson, keys) {
    return keys.every((key) => lesson.answers[key] !== undefined);
  }

  function practiceScore(state, items) {
    return items.reduce((sum, item) => sum + (state.answers[item.id]?.correct ? 1 : 0), 0);
  }

  function formatStamp(iso) {
    const text = new Date(iso).toLocaleString("en-US", {
      timeZone: "America/Los_Angeles",
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
    return `${text} PT`;
  }

  function finalize(lesson, keys, steps) {
    if (lesson.finalized || !quizzesDone(lesson, keys) || !lesson.revealed) return lesson;
    const lastScore = scoreOf(lesson, keys);
    const done = [...lesson.done];
    done[steps - 1] = true;
    const completedAt = new Date().toISOString();
    return {
      ...lesson,
      done,
      lastScore,
      bestScore: lastScore > lesson.bestScore ? lastScore : lesson.bestScore,
      firstCompletedAt: lesson.firstCompletedAt ?? completedAt,
      lastCompletedAt: completedAt,
      attempts: lesson.attempts + 1,
      finalized: true,
    };
  }

  function finalizePractice(state, items) {
    if (state.finalized) return state;
    if (items.some((item) => state.answers[item.id] === undefined)) return state;
    const lastScore = practiceScore(state, items);
    const completedAt = new Date().toISOString();
    return {
      ...state,
      lastScore,
      bestScore: lastScore > state.bestScore ? lastScore : state.bestScore,
      firstCompletedAt: state.firstCompletedAt ?? completedAt,
      lastCompletedAt: completedAt,
      attempts: state.attempts + 1,
      finalized: true,
    };
  }

  function isLessonState(value) {
    return !!value && typeof value === "object" && "step" in value;
  }

  function isPracticeState(value) {
    return !!value && typeof value === "object" && "order" in value && "answers" in value;
  }

  function padDone(done, steps, finalized) {
    const next = [...(done ?? [])];
    while (next.length < steps) next.push(!!finalized);
    return next.slice(0, steps);
  }

  function migrateInsertedWhy(lesson, steps) {
    const prevLen = Array.isArray(lesson.done) ? lesson.done.length : 0;
    if (prevLen !== steps - 1) {
      return { ...lesson, step: clamp(lesson.step, steps), done: padDone(lesson.done, steps, lesson.finalized) };
    }
    let step = lesson.step;
    if (step >= 3) step += 1;
    const whyDone = !!(lesson.finalized || lesson.step >= 3);
    const done = [...lesson.done.slice(0, 2), whyDone, ...lesson.done.slice(2)];
    return { ...lesson, step: clamp(step, steps), done: padDone(done, steps, lesson.finalized) };
  }

  function mergeLesson(saved, steps) {
    const base = emptyLesson(steps);
    if (!isLessonState(saved)) return base;
    return { ...base, ...saved, step: clamp(saved.step, steps), done: Array.isArray(saved.done) ? saved.done : base.done };
  }

  function mergePractice(saved, count) {
    const base = emptyPractice(count);
    if (!isPracticeState(saved)) return base;
    const orderOk = Array.isArray(saved.order) && saved.order.length === count;
    if (!orderOk) {
      return {
        ...base,
        firstCompletedAt: saved.firstCompletedAt ?? null,
        lastCompletedAt: saved.lastCompletedAt ?? null,
        attempts: saved.attempts ?? 0,
      };
    }
    return { ...base, ...saved, step: clamp(saved.step, count + 1) };
  }

  function recordOnly(saved, steps) {
    return {
      ...emptyLesson(steps),
      bestScore: saved.bestScore ?? 0,
      lastScore: saved.lastScore ?? 0,
      firstCompletedAt: saved.firstCompletedAt ?? null,
      lastCompletedAt: saved.lastCompletedAt ?? null,
      attempts: saved.attempts ?? 0,
    };
  }

  function recordOnlyPractice(saved, count) {
    return {
      ...emptyPractice(count),
      bestScore: 0,
      lastScore: 0,
      firstCompletedAt: saved.firstCompletedAt ?? null,
      lastCompletedAt: saved.lastCompletedAt ?? null,
      attempts: saved.attempts ?? 0,
    };
  }

  function readyLessonIds(data) {
    return Object.keys(data.lessons).sort((a, b) => Number(a) - Number(b));
  }

  function practiceFor(data, id) {
    if (id === "eimi") return data.eimi.practice || [];
    return data.lessons[id]?.practice || [];
  }

  function emptyProgress(data) {
    const ids = readyLessonIds(data);
    const lessons = {};
    const practice = {};
    for (const id of ids) {
      const steps = data.lessons[id].kind === "review" && data.lessons[id].steps ? data.lessons[id].steps : data.lessonSteps;
      lessons[id] = emptyLesson(steps);
      practice[id] = emptyPractice(practiceFor(data, id).length);
    }
    practice.eimi = emptyPractice(practiceFor(data, "eimi").length);
    return {
      v: 8,
      tab: "Lesson",
      view: "map",
      lessonId: ids[0] || "1",
      lessons,
      eimi: emptyLesson(data.eimiSteps),
      practice,
    };
  }

  function readStore(data, storage) {
    try {
      if (!storage) return null;
      const raw = storage.getItem(data.storageKey);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (parsed === null || typeof parsed !== "object") return null;
      if (parsed.v !== 4 && parsed.v !== 5 && parsed.v !== 6 && parsed.v !== 7 && parsed.v !== 8) return null;
      const next = emptyProgress(data);
      const tabOk =
        parsed.tab === "Practice" || parsed.tab === "Charts" || parsed.tab === "Words" || parsed.tab === "Lesson";
      next.tab = tabOk ? parsed.tab : "Lesson";
      if ((parsed.v === 6 || parsed.v === 7 || parsed.v === 8) && (parsed.view === "map" || parsed.view === "lesson" || parsed.view === "eimi")) {
        next.view = parsed.view;
      } else next.view = "map";
      const ids = readyLessonIds(data);
      if (ids.includes(parsed.lessonId)) next.lessonId = parsed.lessonId;
      next.eimi = migrateInsertedWhy(mergeLesson(parsed.eimi, data.eimiSteps), data.eimiSteps);
      if ((parsed.v === 6 || parsed.v === 7 || parsed.v === 8) && parsed.lessons) {
        for (const id of ids) {
          const steps = data.lessons[id].kind === "review" && data.lessons[id].steps ? data.lessons[id].steps : data.lessonSteps;
          next.lessons[id] = migrateInsertedWhy(mergeLesson(parsed.lessons[id], steps), steps);
        }
      } else if (isLessonState(parsed.john) && next.lessons["1"]) {
        next.lessons["1"] = recordOnly(parsed.john, data.lessonSteps);
      }
      if ((parsed.v === 7 || parsed.v === 8) && parsed.practice && typeof parsed.practice === "object" && !("order" in parsed.practice)) {
        const packs = parsed.practice;
        for (const id of ids) next.practice[id] = mergePractice(packs[id], practiceFor(data, id).length);
        next.practice.eimi = mergePractice(packs.eimi, practiceFor(data, "eimi").length);
      } else if (parsed.v === 6 && parsed.practice && typeof parsed.practice === "object" && !("order" in parsed.practice)) {
        const packs = parsed.practice;
        for (const id of ids) {
          if (isPracticeState(packs[id])) next.practice[id] = recordOnlyPractice(packs[id], practiceFor(data, id).length);
        }
      } else if (parsed.practice && isPracticeState(parsed.practice) && next.practice["1"]) {
        next.practice["1"] = recordOnlyPractice(parsed.practice, practiceFor(data, "1").length);
      }
      return next;
    } catch {
      return null;
    }
  }

  function writeStore(data, progress, storage) {
    try {
      if (!storage) return false;
      storage.setItem(data.storageKey, JSON.stringify(progress));
      return true;
    } catch {
      return false;
    }
  }

  function sectionLabel(step) {
    if (step === 1) return "Read";
    if (step === 2) return "Pattern";
    if (step === 3) return "Why?";
    if (step === 4 || step === 5) return "English";
    if (step === 6 || step === 7) return "Write";
    return "Look again";
  }

  function eimiSectionLabel(step) {
    if (step === 1) return "Read";
    if (step === 2) return "Pattern";
    if (step === 3) return "Why?";
    if (step === 4) return "Ask";
    return "Look again";
  }

  function tokenLabel(token) {
    const mark = (token.after || "").trim();
    return mark === "," || mark === "." ? token.word + mark : token.word;
  }

  function enrich(token, glossParse) {
    const extra = (glossParse || {})[token.word];
    return {
      word: token.word,
      lemma: extra?.lemma ?? token.word,
      meaning: token.gloss,
      parse: extra?.parse,
    };
  }

  return {
    permute,
    derange,
    tilesInTargetOrder,
    shuffleTiles,
    sameWords,
    sequentialOrder,
    shuffledOrder,
    emptyLesson,
    emptyPractice,
    emptyProgress,
    clamp,
    scoreOf,
    quizzesDone,
    practiceScore,
    formatStamp,
    finalize,
    finalizePractice,
    migrateInsertedWhy,
    mergeLesson,
    mergePractice,
    readyLessonIds,
    practiceFor,
    readStore,
    writeStore,
    sectionLabel,
    eimiSectionLabel,
    tokenLabel,
    enrich,
  };
});
