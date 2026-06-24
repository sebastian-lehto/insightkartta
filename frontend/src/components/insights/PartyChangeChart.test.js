import { describe, expect, it } from "vitest";
import { formatPartyCodeTick, sortPartyChanges } from "./PartyChangeChart";

describe("sortPartyChanges", () => {
  it("sorts by vote share change descending (biggest gain first)", () => {
    const sorted = sortPartyChanges([
      { party_code: "KESK", vote_share_change_pct: -1.5 },
      { party_code: "VIHR", vote_share_change_pct: 2.0 },
      { party_code: "SDP", vote_share_change_pct: 0.5 },
    ]);

    expect(sorted.map((p) => p.party_code)).toEqual(["VIHR", "SDP", "KESK"]);
  });

  it("drops entries with no vote share change data instead of crashing the sort", () => {
    const sorted = sortPartyChanges([
      { party_code: "VIHR", vote_share_change_pct: 1.0 },
      { party_code: "NEW", vote_share_change_pct: null },
    ]);

    expect(sorted).toHaveLength(1);
    expect(sorted[0].party_code).toBe("VIHR");
  });

  it("does not mutate the input array", () => {
    const input = [
      { party_code: "A", vote_share_change_pct: 1 },
      { party_code: "B", vote_share_change_pct: 2 },
    ];
    sortPartyChanges(input);
    expect(input.map((p) => p.party_code)).toEqual(["A", "B"]);
  });
});

describe("formatPartyCodeTick", () => {
  it("leaves short codes untouched", () => {
    expect(formatPartyCodeTick("VIHR")).toBe("VIHR");
  });

  it("truncates long codes with an ellipsis", () => {
    expect(formatPartyCodeTick("LIBERTAS")).toBe("LIBER…");
  });
});
