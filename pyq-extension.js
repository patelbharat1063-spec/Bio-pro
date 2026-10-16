
(function () {
  "use strict";

  const URL =
    "https://raw.githubusercontent.com/AbuRaniya/bankofbiology-neet-quiz/main/Bank_of_Biology_NEET_Master_QuizReady.json";

  function pick(o, keys) {
    for (const k of keys) {
      if (o && o[k] != null && o[k] !== "") return o[k];
    }
    return "";
  }

  function text(v) {
    return typeof v === "string" || typeof v === "number"
      ? String(v).trim()
      : "";
  }

  function rows(data) {
    if (Array.isArray(data)) return data;
    if (!data || typeof data !== "object") return [];

    for (const k of [
      "questions", "bank", "mcqs", "items", "results",
      "previous_neet_questions", "question_bank"
    ]) {
      if (Array.isArray(data[k])) return data[k];
    }

    if (Array.isArray(data.data)) return data.data;

    for (const k of ["database", "quiz", "payload"]) {
      const result = rows(data[k]);
      if (result.length) return result;
    }

    return [];
  }

  function normalize(q, i) {
    if (!q || typeof q !== "object") return null;

    const question = text(pick(q, [
      "question", "question_text", "questionText",
      "question_statement", "stem", "q", "text", "ques"
    ]));

    let opts = pick(q, ["options", "choices", "option_list"]);

    if (typeof opts === "string") {
      try { opts = JSON.parse(opts); } catch (_) { opts = []; }
    }

    if (Array.isArray(opts)) {
      opts = opts.map(x =>
        x && typeof x === "object"
          ? text(pick(x, ["text", "value", "option", "label"]))
          : text(x)
      );
    } else if (opts && typeof opts === "object") {
      opts = ["A", "B", "C", "D"].map((l, n) =>
        text(pick(opts, [l, l.toLowerCase(), "option" + (n + 1)]))
      );
    } else {
      opts = [
        pick(q, ["option_a", "optionA", "option1", "a"]),
        pick(q, ["option_b", "optionB", "option2", "b"]),
        pick(q, ["option_c", "optionC", "option3", "c"]),
        pick(q, ["option_d", "optionD", "option4", "d"])
      ].map(text);
    }

    if (!question || opts.length < 4 || opts.slice(0, 4).some(x => !x)) {
      return null;
    }

    let answer = text(pick(q, [
      "answer", "correct_answer", "correctAnswer",
      "correct_option", "answer_key", "answerKey", "ans", "key", "cop"
    ])).toUpperCase();

    const letter = answer.match(/^[\s([{]*(?:OPTION\s*)?([A-D])(?:[\s)\]}.:].*)?$/);
    if (letter) {
      answer = letter[1];
    } else if (/^[0-3]$/.test(answer)) {
      answer = "ABCD"[Number(answer)];
    } else if (/^[1-4]$/.test(answer)) {
      answer = "ABCD"[Number(answer) - 1];
    } else {
      const idx = opts.findIndex(x => x.toLowerCase() === answer.toLowerCase());
      answer = idx >= 0 ? "ABCD"[idx] : "";
    }

    if (!answer) return null;

    return {
      id: "previous-neet-" + text(pick(q, ["id", "question_id", "qid"])) .replace(/\s/g, "") || "previous-neet-" + i,
      question,
      option_a: opts[0],
      option_b: opts[1],
      option_c: opts[2],
      option_d: opts[3],
      answer,
      explanation: text(pick(q, [
        "explanation", "solution", "rationale",
        "answer_explanation", "detailed_explanation"
      ])),
      topic: text(pick(q, [
        "chapter", "chapter_name", "topic", "unit", "subject_topic"
      ])) || "Chapter not specified",
      subtopic: text(pick(q, ["subtopic", "topic_name", "sub_topic"])),
      subject: "Biology",
      tags: "Previous NEET PYQ",
      source: "Previous NEET PYQ"
    };
  }

  window.loadPreviousNEETBank = async function () {
    const response = await fetch(URL);
    if (!response.ok) throw new Error("PYQ database HTTP " + response.status);

    const data = await response.json();
    const list = rows(data);

    if (!list.length) throw new Error("No question list found in the JSON.");

    const result = list.map(normalize).filter(Boolean);

    if (!result.length) {
      throw new Error("Questions were found, but the data format needs adjustment.");
    }

    return result;
  };
})();
