"""Classic mort subtables beyond the upstream fixtures, compiled by the reference and decoded here."""

import json

import pytest

from fontTools.misc.testTools import FakeFont, getXML, parseXML
from fontTools.misc.textTools import deHexStr
from fontTools.ttLib import newTable


NO_LOOKUP = 0xFFFF


def _lookup(table, index):
    if index == NO_LOOKUP:
        return None
    return dict(sorted(table.PerGlyphLookups[index].items()))


def _transition(table, transition):
    out = {}
    for name, value in sorted(vars(transition).items()):
        if name.startswith("_") or name == "ReservedFlags":
            continue
        if name in ("CurrentIndex", "MarkIndex"):
            out[name] = _lookup(table, value)
        elif name == "Actions":
            out[name] = [[action.GlyphIndexDelta, bool(action.Store)] for action in value]
        elif isinstance(value, (list, tuple)):
            out[name] = list(value)
        else:
            out[name] = value
    return out


def snapshot(mort):
    """The decoded meaning of every subtable, independent of lookup order and out-of-bounds class rows."""
    chains = []
    for chain in mort.table.MorphChain:
        subtables = []
        for subtable in chain.MorphSubtable:
            row = {"MorphType": subtable.MorphType, "CoverageFlags": subtable.CoverageFlags,
                   "SubFeatureFlags": subtable.SubFeatureFlags}
            struct = subtable.SubStruct
            if subtable.MorphType == 4:
                row["Substitution"] = dict(sorted(struct.Substitution.items()))
            else:
                table = struct.StateTable
                row["GlyphClasses"] = {g: c for g, c in sorted(table.GlyphClasses.items()) if c != 1}
                row["States"] = [{str(k): _transition(table, t) for k, t in sorted(state.Transitions.items())}
                                 for state in table.States]
                if subtable.MorphType == 2:
                    row["LigComponents"] = list(table.LigComponents)
                    row["Ligatures"] = list(table.Ligatures)
            subtables.append(row)
        chains.append({"DefaultFlags": chain.DefaultFlags, "Subtables": subtables})
    return chains


CASES = json.loads('{"all_types_edited": {"data": "00010000000000010000001f0000022800000005004820000000000100060008002c00320000001f0101010405010101010101010101010101010101010101010101010101010100000000000102002c0000002c8000002c20010000008c2001000000020005000a002e003400440000001f0101010101040101010101010101010101010101010101010101010101010100000000000100002e000000000000002e0000000000220000000000000000000800070000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000d82002000000040006000e0032003e004c005400cc0000001f010101010101010405010101010101010101010101010101010101010101010000000000010000000000000200320000003880000032804c00000000002a8000004800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc0010000000202004000000080006000400020008000100000003000b0009000affff000000502005000000100005000a002e003400440000001f0101010101010101010101010401010101010101010101010101010101010100000000000100002e0000ffffffff002e00400000ffff000e000c", "glyphs": [".notdef", "pad1", "space", "A", "B", "C", "D", "E", "F", "G", "H", "O", "X", "Y", "Z", "zero", "one", "one_zero", "one_one", "one_two", "one_three", "one_four", "one_five", "two", "three", "four", "five", "six", "seven", "eight", "nine"], "snapshot": [{"DefaultFlags": 31, "Subtables": [{"CoverageFlags": 32, "GlyphClasses": {"A": 4, "B": 5}, "MorphType": 0, "States": [{"0": {"DontAdvance": false, "MarkFirst": false, "MarkLast": false, "NewState": 0, "Verb": 0}, "1": {"DontAdvance": false, "MarkFirst": false, "MarkLast": false, "NewState": 0, "Verb": 0}, "2": {"DontAdvance": false, "MarkFirst": false, "MarkLast": false, "NewState": 0, "Verb": 0}, "3": {"DontAdvance": false, "MarkFirst": false, "MarkLast": false, "NewState": 0, "Verb": 0}, "4": {"DontAdvance": false, "MarkFirst": true, "MarkLast": false, "NewState": 0, "Verb": 0}, "5": {"DontAdvance": false, "MarkFirst": false, "MarkLast": true, "NewState": 0, "Verb": 1}}], "SubFeatureFlags": 1}, {"CoverageFlags": 32, "GlyphClasses": {"C": 4}, "MorphType": 1, "States": [{"0": {"CurrentIndex": null, "DontAdvance": false, "MarkIndex": null, "NewState": 0, "SetMark": false}, "1": {"CurrentIndex": null, "DontAdvance": false, "MarkIndex": null, "NewState": 0, "SetMark": false}, "2": {"CurrentIndex": null, "DontAdvance": false, "MarkIndex": null, "NewState": 0, "SetMark": false}, "3": {"CurrentIndex": null, "DontAdvance": false, "MarkIndex": null, "NewState": 0, "SetMark": false}, "4": {"CurrentIndex": {"B": "F", "C": "E"}, "DontAdvance": false, "MarkIndex": null, "NewState": 0, "SetMark": false}}], "SubFeatureFlags": 2}, {"CoverageFlags": 32, "GlyphClasses": {"E": 4, "F": 5}, "LigComponents": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], "Ligatures": ["one"], "MorphType": 2, "States": [{"0": {"Actions": [], "DontAdvance": false, "NewState": 0, "SetComponent": false}, "1": {"Actions": [], "DontAdvance": false, "NewState": 0, "SetComponent": false}, "2": {"Actions": [], "DontAdvance": false, "NewState": 0, "SetComponent": false}, "3": {"Actions": [], "DontAdvance": false, "NewState": 0, "SetComponent": false}, "4": {"Actions": [], "DontAdvance": false, "NewState": 1, "SetComponent": true}, "5": {"Actions": [], "DontAdvance": false, "NewState": 0, "SetComponent": false}}, {"0": {"Actions": [], "DontAdvance": false, "NewState": 0, "SetComponent": false}, "1": {"Actions": [], "DontAdvance": false, "NewState": 0, "SetComponent": false}, "2": {"Actions": [], "DontAdvance": false, "NewState": 0, "SetComponent": false}, "3": {"Actions": [], "DontAdvance": false, "NewState": 0, "SetComponent": false}, "4": {"Actions": [], "DontAdvance": false, "NewState": 0, "SetComponent": false}, "5": {"Actions": [[0, false], [30, false]], "DontAdvance": false, "NewState": 0, "SetComponent": true}}], "SubFeatureFlags": 4}, {"CoverageFlags": 32, "MorphType": 4, "SubFeatureFlags": 8, "Substitution": {"A": "O", "G": "H"}}, {"CoverageFlags": 32, "GlyphClasses": {"X": 4}, "MorphType": 5, "States": [{"0": {"CurrentInsertBefore": false, "CurrentInsertionAction": [], "CurrentIsKashidaLike": false, "DontAdvance": false, "MarkedInsertBefore": false, "MarkedInsertionAction": [], "MarkedIsKashidaLike": false, "NewState": 0, "SetMark": false}, "1": {"CurrentInsertBefore": false, "CurrentInsertionAction": [], "CurrentIsKashidaLike": false, "DontAdvance": false, "MarkedInsertBefore": false, "MarkedInsertionAction": [], "MarkedIsKashidaLike": false, "NewState": 0, "SetMark": false}, "2": {"CurrentInsertBefore": false, "CurrentInsertionAction": [], "CurrentIsKashidaLike": false, "DontAdvance": false, "MarkedInsertBefore": false, "MarkedInsertionAction": [], "MarkedIsKashidaLike": false, "NewState": 0, "SetMark": false}, "3": {"CurrentInsertBefore": false, "CurrentInsertionAction": [], "CurrentIsKashidaLike": false, "DontAdvance": false, "MarkedInsertBefore": false, "MarkedInsertionAction": [], "MarkedIsKashidaLike": false, "NewState": 0, "SetMark": false}, "4": {"CurrentInsertBefore": false, "CurrentInsertionAction": ["Z", "X"], "CurrentIsKashidaLike": false, "DontAdvance": false, "MarkedInsertBefore": false, "MarkedInsertionAction": [], "MarkedIsKashidaLike": false, "NewState": 0, "SetMark": false}}], "SubFeatureFlags": 16}]}]}, "all_types_shifted": {"data": "00010000000000010000001f0000021c00000005004820000000000100060008002e00340000002101010101010405010101010101010101010101010101010101010101010101010100000000000102002e0000002e8000002e200100902001000000020005000a00300036004600000021010101010101010401010101010101010101010101010101010101010101010101000000000001000030000000000000003000000000002300000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000d82002000000040006000e00340040004c005400cc000000210101010101010101010405010101010101010101010101010101010101010101010000000000010000000000000200340000003a80000034804c0000002a8000004800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc0012000000102004000000080008000b0001000c00502005000000100005000a003000360046000000210101010101010101010101010101040101010101010101010101010101010101010000000000010000300000ffffffff003000200000ffff000f", "glyphs": [".notdef", "pad1", "pad2", "pad3", "space", "A", "B", "C", "D", "E", "F", "G", "H", "O", "X", "Y", "Z", "zero", "one", "one_zero", "one_one", "one_two", "one_three", "one_four", "one_five", "two", "three", "four", "five", "six", "seven", "eight", "nine"], "snapshot": [{"DefaultFlags": 31, "Subtables": [{"CoverageFlags": 32, "GlyphClasses": {"A": 4, "B": 5}, "MorphType": 0, "States": [{"0": {"DontAdvance": false, "MarkFirst": false, "MarkLast": false, "NewState": 0, "Verb": 0}, "1": {"DontAdvance": false, "MarkFirst": false, "MarkLast": false, "NewState": 0, "Verb": 0}, "2": {"DontAdvance": false, "MarkFirst": false, "MarkLast": false, "NewState": 0, "Verb": 0}, "3": {"DontAdvance": false, "MarkFirst": false, "MarkLast": false, "NewState": 0, "Verb": 0}, "4": {"DontAdvance": false, "MarkFirst": true, "MarkLast": false, "NewState": 0, "Verb": 0}, "5": {"DontAdvance": false, "MarkFirst": false, "MarkLast": true, "NewState": 0, "Verb": 1}}], "SubFeatureFlags": 1}, {"CoverageFlags": 32, "GlyphClasses": {"C": 4}, "MorphType": 1, "States": [{"0": {"CurrentIndex": null, "DontAdvance": false, "MarkIndex": null, "NewState": 0, "SetMark": false}, "1": {"CurrentIndex": null, "DontAdvance": false, "MarkIndex": null, "NewState": 0, "SetMark": false}, "2": {"CurrentIndex": null, "DontAdvance": false, "MarkIndex": null, "NewState": 0, "SetMark": false}, "3": {"CurrentIndex": null, "DontAdvance": false, "MarkIndex": null, "NewState": 0, "SetMark": false}, "4": {"CurrentIndex": {"C": "D"}, "DontAdvance": false, "MarkIndex": null, "NewState": 0, "SetMark": false}}], "SubFeatureFlags": 2}, {"CoverageFlags": 32, "GlyphClasses": {"E": 4, "F": 5}, "LigComponents": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], "Ligatures": ["one"], "MorphType": 2, "States": [{"0": {"Actions": [], "DontAdvance": false, "NewState": 0, "SetComponent": false}, "1": {"Actions": [], "DontAdvance": false, "NewState": 0, "SetComponent": false}, "2": {"Actions": [], "DontAdvance": false, "NewState": 0, "SetComponent": false}, "3": {"Actions": [], "DontAdvance": false, "NewState": 0, "SetComponent": false}, "4": {"Actions": [], "DontAdvance": false, "NewState": 1, "SetComponent": true}, "5": {"Actions": [], "DontAdvance": false, "NewState": 0, "SetComponent": false}}, {"0": {"Actions": [], "DontAdvance": false, "NewState": 0, "SetComponent": false}, "1": {"Actions": [], "DontAdvance": false, "NewState": 0, "SetComponent": false}, "2": {"Actions": [], "DontAdvance": false, "NewState": 0, "SetComponent": false}, "3": {"Actions": [], "DontAdvance": false, "NewState": 0, "SetComponent": false}, "4": {"Actions": [], "DontAdvance": false, "NewState": 0, "SetComponent": false}, "5": {"Actions": [[0, false], [30, false]], "DontAdvance": false, "NewState": 0, "SetComponent": true}}], "SubFeatureFlags": 4}, {"CoverageFlags": 32, "MorphType": 4, "SubFeatureFlags": 8, "Substitution": {"G": "H"}}, {"CoverageFlags": 32, "GlyphClasses": {"X": 4}, "MorphType": 5, "States": [{"0": {"CurrentInsertBefore": false, "CurrentInsertionAction": [], "CurrentIsKashidaLike": false, "DontAdvance": false, "MarkedInsertBefore": false, "MarkedInsertionAction": [], "MarkedIsKashidaLike": false, "NewState": 0, "SetMark": false}, "1": {"CurrentInsertBefore": false, "CurrentInsertionAction": [], "CurrentIsKashidaLike": false, "DontAdvance": false, "MarkedInsertBefore": false, "MarkedInsertionAction": [], "MarkedIsKashidaLike": false, "NewState": 0, "SetMark": false}, "2": {"CurrentInsertBefore": false, "CurrentInsertionAction": [], "CurrentIsKashidaLike": false, "DontAdvance": false, "MarkedInsertBefore": false, "MarkedInsertionAction": [], "MarkedIsKashidaLike": false, "NewState": 0, "SetMark": false}, "3": {"CurrentInsertBefore": false, "CurrentInsertionAction": [], "CurrentIsKashidaLike": false, "DontAdvance": false, "MarkedInsertBefore": false, "MarkedInsertionAction": [], "MarkedIsKashidaLike": false, "NewState": 0, "SetMark": false}, "4": {"CurrentInsertBefore": false, "CurrentInsertionAction": ["Y"], "CurrentIsKashidaLike": false, "DontAdvance": false, "MarkedInsertBefore": false, "MarkedInsertionAction": [], "MarkedIsKashidaLike": false, "NewState": 0, "SetMark": false}}], "SubFeatureFlags": 16}]}]}, "contextual_windows_shifted": {"data": "000100000000000100000001000001540000000101480001000000010005000a0010001a003200230001040000000000010000000002001000000000000000158000007300000010000000190046000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000024000000000000000000000000000000000000000000000000000000000000002400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000", "glyphs": [".notdef", "pad1", "pad2", "pad3", "pad4", "pad5", "g1", "g2", "g3", "g4", "g5", "g6", "g7", "g8", "g9", "g10", "g11", "g12", "g13", "g14", "g15", "g16", "g17", "g18", "g19", "g20", "g21", "g22", "g23", "g24", "g25", "g26", "g27", "g28", "g29", "hyphen", "emdash", "h32", "h33", "h34", "h35", "h36", "h37", "h38", "h39"], "snapshot": [{"DefaultFlags": 1, "Subtables": [{"CoverageFlags": 0, "GlyphClasses": {"hyphen": 4}, "MorphType": 1, "States": [{"0": {"CurrentIndex": null, "DontAdvance": false, "MarkIndex": null, "NewState": 0, "SetMark": false}, "1": {"CurrentIndex": null, "DontAdvance": false, "MarkIndex": null, "NewState": 0, "SetMark": false}, "2": {"CurrentIndex": null, "DontAdvance": false, "MarkIndex": null, "NewState": 0, "SetMark": false}, "3": {"CurrentIndex": null, "DontAdvance": false, "MarkIndex": null, "NewState": 0, "SetMark": false}, "4": {"CurrentIndex": null, "DontAdvance": false, "MarkIndex": {}, "NewState": 1, "SetMark": true}}, {"0": {"CurrentIndex": null, "DontAdvance": false, "MarkIndex": null, "NewState": 0, "SetMark": false}, "1": {"CurrentIndex": null, "DontAdvance": false, "MarkIndex": null, "NewState": 0, "SetMark": false}, "2": {"CurrentIndex": null, "DontAdvance": false, "MarkIndex": null, "NewState": 0, "SetMark": false}, "3": {"CurrentIndex": null, "DontAdvance": false, "MarkIndex": null, "NewState": 0, "SetMark": false}, "4": {"CurrentIndex": {"g1": "emdash"}, "DontAdvance": false, "MarkIndex": {"hyphen": "emdash"}, "NewState": 0, "SetMark": false}}], "SubFeatureFlags": 1}]}]}, "ligature_rebase_shifted": {"data": "00010000000000010000000100000078000200010004000000000001ffffffff00000001000000000000000000542002000000010007000e001c002400300038004800000009010101010405060101000000000001010200001c0000001c8000001c80300000001a8000001e00000002000000000048004a0048004800070008", "glyphs": [".notdef", "pad1", "pad2", "space", "a", "b", "c", "a_c", "b_c"], "snapshot": [{"DefaultFlags": 1, "Subtables": [{"CoverageFlags": 32, "GlyphClasses": {"a": 4, "b": 5, "c": 6}, "LigComponents": [0, 1, 0, 0, 0, 1, 0, 0], "Ligatures": ["a_c", "b_c"], "MorphType": 2, "States": [{"0": {"Actions": [], "DontAdvance": false, "NewState": 0, "SetComponent": false}, "1": {"Actions": [], "DontAdvance": false, "NewState": 0, "SetComponent": false}, "2": {"Actions": [], "DontAdvance": false, "NewState": 0, "SetComponent": false}, "3": {"Actions": [], "DontAdvance": false, "NewState": 0, "SetComponent": false}, "4": {"Actions": [], "DontAdvance": false, "NewState": 0, "SetComponent": true}, "5": {"Actions": [], "DontAdvance": false, "NewState": 0, "SetComponent": true}, "6": {"Actions": [[-2, false], [2, false]], "DontAdvance": false, "NewState": 0, "SetComponent": true}}], "SubFeatureFlags": 1}]}]}}')


def _decompile(data, font):
    table = newTable("mort")
    table.decompile(data, font)
    return table


@pytest.mark.parametrize("case", sorted(CASES))
def test_decompile(case):
    font = FakeFont(CASES[case]["glyphs"])
    table = _decompile(deHexStr(CASES[case]["data"]), font)
    assert snapshot(table) == CASES[case]["snapshot"]


@pytest.mark.parametrize("case", sorted(CASES))
def test_binary_roundtrip(case):
    font = FakeFont(CASES[case]["glyphs"])
    table = _decompile(deHexStr(CASES[case]["data"]), font)
    assert snapshot(_decompile(table.compile(font), font)) == CASES[case]["snapshot"]


@pytest.mark.parametrize("case", sorted(CASES))
def test_xml_roundtrip(case):
    font = FakeFont(CASES[case]["glyphs"])
    table = _decompile(deHexStr(CASES[case]["data"]), font)
    compiled = newTable("mort")
    for name, attrs, content in parseXML(getXML(table.toXML)):
        compiled.fromXML(name, attrs, content, font=font)
    assert snapshot(_decompile(compiled.compile(font), font)) == CASES[case]["snapshot"]
