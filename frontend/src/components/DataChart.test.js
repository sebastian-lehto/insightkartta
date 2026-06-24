import { describe, expect, it } from "vitest";
import { yFormatter } from "./DataChart";

describe("yFormatter", () => {
  it("passes small numbers through unchanged", () => {
    expect(yFormatter(42)).toBe(42);
  });

  it("formats thousands with a k suffix", () => {
    expect(yFormatter(45_000)).toBe("45k");
  });

  it("formats millions with an M suffix", () => {
    expect(yFormatter(5_600_000)).toBe("5.6M");
  });
});
