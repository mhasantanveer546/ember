import { describe, expect, it } from "vitest";
import { escapeRegExp, parseSnippet, queryTerms } from "./highlight";

describe("parseSnippet", () => {
  it("splits **bold** markers into hit and plain parts", () => {
    expect(parseSnippet("notes on **database** **normalization** theory")).toEqual([
      { text: "notes on ", hit: false },
      { text: "database", hit: true },
      { text: " ", hit: false },
      { text: "normalization", hit: true },
      { text: " theory", hit: false },
    ]);
  });
  it("returns plain text when there are no markers", () => {
    expect(parseSnippet("plain")).toEqual([{ text: "plain", hit: false }]);
  });
  it("never injects HTML: markup stays as literal text", () => {
    expect(parseSnippet("<img src=x onerror=alert(1)>")[0].text).toContain("<img");
  });
});

describe("queryTerms", () => {
  it("drops quotes, lowercases, dedupes and ignores 1-char words", () => {
    expect(queryTerms('"Database" database a normalization')).toEqual(["database", "normalization"]);
  });
});

describe("escapeRegExp", () => {
  it("escapes regex metacharacters so user input can't break highlighting", () => {
    expect(new RegExp(escapeRegExp("c++ (tcp)")).test("learn c++ (tcp) now")).toBe(true);
  });
});
