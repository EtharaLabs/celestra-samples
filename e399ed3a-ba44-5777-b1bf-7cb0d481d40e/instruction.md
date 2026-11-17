# Classic `mort` tables only work for non-contextual subtables

fontTools (checked out at `/app/fonttools`, installed in editable mode) decompiles, dumps to TTX,
reads back from TTX and compiles the extended AAT `morx` table for all of its subtable types. The
obsolete classic `mort` table, which fonts still shipping with macOS carry, works only when every
subtable is a non-contextual glyph substitution (type 4). A `mort` table with a rearrangement (0),
contextual glyph substitution (1), ligature (2) or glyph insertion (5) subtable cannot be used:

```python
from fontTools.ttLib import newTable
table = newTable("mort")
table.decompile(data, font)   # KeyError: (0, 'MorphSubtable', 'MorphChain')
```

Make `mort` subtables of all five types decompile, write to TTX, read from TTX and compile, in the
classic `mort` binary encoding (not the `morx` one). Apple's TrueType Reference Manual describes
both formats; there is no network access, so work from what you know of them and from the existing
`morx` and `mort` code.

## Requirements

1. **Same object model as `morx`.** A decompiled classic subtable has the same `MorphType` (0, 1,
   2, 4 or 5) and the same `SubStruct` class as the `morx` subtable of that type
   (`RearrangementMorph`, `ContextualMorph`, `LigatureMorph`, `NoncontextualMorph`,
   `InsertionMorph`). State-table subtables carry a `StateTable` with the attributes fontTools'
   `morx` state tables use: `GlyphClasses`, `GlyphClassCount`, `States` (each with `Transitions`
   keyed by glyph class), `PerGlyphLookups`, and, for ligature subtables, `LigComponents` and
   `Ligatures`. Transitions carry the same fields as their `morx` counterparts, with
   `ReservedFlags` holding any flag bits the type leaves unassigned: `NewState`, `DontAdvance`,
   `MarkFirst`, `MarkLast`, `Verb` (rearrangement); `SetMark`, `MarkIndex`,
   `CurrentIndex` (contextual, where `0xFFFF` means no substitution); `SetComponent` and `Actions`
   with `GlyphIndexDelta` and `Store` (ligature); and `CurrentInsertionAction`,
   `MarkedInsertionAction` and their flags (insertion). TTX uses the same elements as `morx`
   state tables. Reuse the state-table, state and action classes and the state-table TTX code
   fontTools already has for `morx`; add no `mort`-only copy of any of them.
2. **Glyph classes.** `GlyphClasses` holds exactly the glyphs the classic class array covers, from
   its first glyph for its glyph count, each with the class the array gives it, including class 1.
3. **Ligature components.** `LigComponents` and `Actions` hold the same normalized values as in
   `morx`, so the ligature-table base that classic component entries include is removed on
   decompile and added back on compile. Which component entries carried that base must be kept
   exactly, so that compiling a decompiled ligature subtable, directly or through TTX, reproduces
   the original component table even where components are zero. In TTX, write that set inside the
   ligature subtable's `StateTable` element, after `LigComponents`, as a `MortLigatureRebase`
   element with one `<Component index="N"/>` child per component index, in ascending order, and
   restore it when reading TTX.
4. **Trimmed contextual windows.** A contextual entry's (possibly negative) offset plus a glyph ID
   locates that glyph's replacement word, so each lookup is a per-glyph window. Decode every
   word that lies inside the substitution table and ends at or before the end of the subtable,
   and only those; every other glyph has no substitution. A window that is empty this way still gets its own entry in
   `PerGlyphLookups`, and the transitions keep pointing at it. When compiling, write full per-glyph
   arrays; such tables then round trip by meaning, not byte for byte.
5. **Class count from TTX.** When a state table is read from TTX, `GlyphClassCount` is one more
   than the largest class that either a glyph is assigned to or a transition is given for, so
   transitions for a class no glyph uses survive a TTX round trip.
6. **Round trips.** For every subtable type, decompiling, compiling and decompiling again, and the
   same through TTX, gives back the same subtables.
7. **Malformed tables.** Decompiling a classic state table raises an exception, rather than
   returning a table, when its glyph-class count is zero, when its state array starts after its
   entry table, or when a ligature subtable's component table starts after its ligature table,
   has an odd length in bytes, or holds an odd component value.
8. **Nothing else changes.** Non-contextual `mort` subtables keep their current TTX and bytes, and
   the binary encoding fontTools reads and writes for `morx` tables stays as it is.

Only your changes under `Lib/fontTools` are graded. Changes to `Tests/` and to
`Lib/fontTools/misc/testTools.py` are discarded before grading.
