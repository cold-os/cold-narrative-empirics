# Annotation Guide (v1.0)

## Task background

Each item is a **two-person debate**: two personas with different political/value
dispositions argue about a moral dilemma. Each side updates or retains a stance on a
5-point Likert scale each round. `stance_changes` marks a round where an attitude
shift was detected by the dataset moderator — **but the shift may be legitimate or a
narrative break**. Your job: classify the shift.

Important: these are LLM-generated synthetic conversations (not real human-AI
dialogues). In Dimension 2, flag obvious generation defects (verbatim repetition,
persona takeover).

## Dimension 1 — Nature of the shift

### LEGAL_SHIFT
The stance changed, but **the speaker is still the same person** — "what kind of
person they are" still holds. The core (values, identity, deep dispositions) did not
break; attitude or behavior adjusted within reason.

Signals:
- Speaker identity is consistent (never claims to be the other persona)
- The new stance is justified by **reasons consistent with their own values**
- Example: moving from "strongly against" to "partly in favor" while reasoning from
  the same value system

### NARRATIVE_BREAK
The change conflicts with the speaker's established core, or the narrative is
disrupted unexplainably — **the core itself is violated/replaced**, including
"takeover" (suddenly acting against everything established).

Signals:
- **Persona replacement**: the speaker suddenly claims the *other* persona's identity
- **Value flip**: stance/behavior directly contradicts values expressed repeatedly,
  with no reasonable explanation
- **Verbatim echo**: this round reproduces the previous round (or the other speaker's
  text) verbatim, as if pasted
- **First-person confusion**: the referent of "I" abruptly changes

### UNCERTAIN
Not enough information to decide.

## Dimension 2 — Generation artifact (meta-level)

Independently of Dimension 1, judge whether this shift looks like an LLM generation
defect: verbatim repetition, role confusion (speaker A speaks speaker B's words),
meaningless duplication, truncated copied text.

- `yes` / `no` / `uncertain`

Dimension 1 and 2 can both hold: a persona-replacement sample is NARRATIVE_BREAK in
Dimension 1 AND a generation artifact in Dimension 2 — they are not mutually exclusive.

## How to annotate

1. Read the scenario (plain-language retelling of the dilemma) first;
2. Read the two personas' identity cards and initial stances;
3. Read the shift story: who changed from what to what, and why;
4. Use the clue column only as factual leads (it describes evidence, not conclusions);
5. Fill Dimension 1 and Dimension 2 independently;
6. Raters work independently, without discussion.

## FAQ

**Q: The shift round is almost identical to the previous round. Is it a break?**
A: Check who is speaking. Same person repeating their own position = possibly a
generation artifact (Dimension 2 = yes; Dimension 1 depends on whether a real shift
happened). If persona A's slot contains persona B's words/identity = persona
replacement → Dimension 1 = NARRATIVE_BREAK.

**Q: The speaker changed their mind with good reasons. Legal?**
A: Yes. Changing one's mind is not a break — what matters is whether "the person is
still the same" and the reasons fit their core. A break is about the core being
replaced, not about the stance moving.

**Q: How do the two dimensions combine?**
A: Common combos: LEGAL_SHIFT + no artifact (normal revision); NARRATIVE_BREAK +
artifact (generation error causing persona confusion); NARRATIVE_BREAK + no artifact
(non-artifact breaks are the most valuable finding).
