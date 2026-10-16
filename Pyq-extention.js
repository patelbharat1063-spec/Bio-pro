
/* NEET Bio Pro — Previous NEET PYQ Loader
   Loads public questions in read-only mode.
   Does not modify localStorage or delete existing records.
*/
(function () {
  "use strict";

  const MASTER_URL =
    "https://raw.githubusercontent.com/AbuRaniya/bankofbiology-neet-quiz/main/Bank_of_Biology_NEET_Master_QuizReady.json";

  function first(obj, keys) {
    for (const key of keys) {
      if (
        obj &&
        obj[key] !== undefined &&
        obj[key] !== null &&
        obj[key] !== ""
      ) {
        return obj[key];
      }
    }
    return "";
  }

  function str(value) {
    if (value === null || value === undefined) return "";
    if (typeof value === "string" || typeof value === "number") {
      return String(value);
    }
    return "";
  }

  function getRows(data) {
    if (Array.isArray(data)) return data;
    if (!data || typeof data !== "object") return [];

    const keys = [
      "questions",
      "bank",
      "mcqs",
      "data",
      "items",
      "results",
      "previous_neet_questions",
      "question_bank"
    ];

    for (const key of keys) {
      if (Array.isArray(data[key])) return data[key];
    }

    for (const key of ["database", "quiz", "payload"]) {
      if (data[key] && typeof data[key] === "object") {
        const rows = getRows(data[key]);
        if (rows.length) return rows;
      }
    }

    return [];
  }

  function getOptions(q) {
    let raw = first(q, ["options", "choices", "option_list"]);

    if (typeof raw === "string") {
      try {
        raw = JSON.parse(raw);
      } catch (_) {
        raw = [];
      }
    }

    let values = [];

    if (Array.isArray(raw)) {
      values = raw.map(item => {
        if (item && typeof item === "object") {
          return str(first(item, [
            "text", "value", "option", "label"
          ]));
        }
        return str(item);
      });
    } else if (raw && typeof raw === "object") {
      values = ["A", "B", "C", "D"].map((letter, i) =>
        str(first(raw, [
          letter,
          letter.toLowerCase(),
          "option_" + letter.toLowerCase(),
          "option" + (i + 1)
        ]))
      );
    }

    if (!values.some(Boolean)) {
      values = [
        first(q, ["option_a", "optionA", "opa", "option1", "option_1", "a"]),
        first(q, ["option_b", "optionB", "opb", "option2", "option_2", "b"]),
        first(q, ["option_c", "optionC", "opc", "option3", "option_3", "c"]),
        first(q, ["option_d", "optionD", "opd", "option4", "option_4", "d"])
      ].map(str);
    }

    return values.slice(0, 4);
  }

  function getAnswer(q, options) {
    const rawAnswer = str(first(q, [
      "answer",
      "correct_answer",
      "correctAnswer",
      "correct_option",
      "answer_key",
      "answerKey",
      "ans",
      "key",
      "cop"
    ])).trim();

    if (!rawAnswer) return "";

    const letter = rawAnswer.match(
      /^(?:OPTION\s*)?[\(\[]?([A-D])[\)\].:\s-]*(?:.*)?$/i
    );

    if (letter) return letter[1].toUpperCase();

    const zeroBased = rawAnswer.match(/^[\(\[]?([0-3])[\)\].]?$/);
    if (zeroBased) return "ABCD"[Number(zeroBased[1])];

    const oneBased = rawAnswer.match(/^[\(\[]?([1-4])[\)\].]?$/);
    if (oneBased) return "ABCD"[Number(oneBased[1]) - 1];

    const cleaned = rawAnswer
      .replace(/^(answer|correct answer)\s*[:=-]\s*/i, "")
      .trim()
      .toLowerCase();

    const index = options.findIndex(
      option => str(option).trim().toLowerCase() === cleaned
    );

    return index >= 0 ? "ABCD"[index] : "";
  }

  function normalizeQuestion(q, index) {
    if (!q || typeof q !== "object") return null;

    const question = str(first(q, [
      "question",
      "question_text",
      "questionText",
      "question_statement",
      "stem",
      "q",
      "text",
      "ques"
    ])).trim();

    const options = getOptions(q);
    const answer = getAnswer(q, options);

    // Skip records that cannot be safely used as MCQs.
    if (
      !question ||
      options.length !== 4 ||
      options.some(option => !str(option).trim()) ||
      !answer
    ) {
      return null;
    }

    return {
      id: "pyq-master-" +
        str(first(q, ["id", "question_id", "qid", "serial_no", "s_no"]) || index),

      question: question,

      option_a: str(options[0]),
      option_b: str(options[1]),
      option_c: str(options[2]),
      option_d: str(options[3]),

      answer: answer,

      explanation: str(first(q, [
        "explanation",
        "solution",
        "rationale",
        "answer_explanation",
        "detailed_explanation"
      ])),

      topic: str(first(q, [
        "chapter",
        "chapter_name",
        "topic",
        "unit",
        "subject_topic"
      ])) || "Chapter not specified",

      subtopic: str(first(q, [
        "subtopic",
        "topic_name",
        "sub_topic"
      ])),

      subject: "Biology",
      tags: "Previous NEET PYQ",
      source: "Previous NEET PYQ"
    };
  }

  window.loadPreviousNEETBank = async function () {
    const response = await fetch(MASTER_URL, {
      cache: "no-store"
    });

    if (!response.ok) {
      throw new Error(
        "Previous NEET database request failed: HTTP " +
        response.status
      );
    }

    const data = await response.json();
    const rows = getRows(data);

    if (!rows.length) {
      throw new Error(
        "No supported question list was found in the master JSON."
      );
    }

    const questions = rows
      .map(normalizeQuestion)
      .filter(Boolean);

    if (!questions.length) {
      throw new Error(
        "The JSON loaded, but its question format needs adjustment."
      );
    }

    return questions;
  };
})();
