# Templates

Plain words, short sections, a number to reply with. Write for a product owner who didn't build it.
Every body and comment starts with the header line and contains the marker.

## Decision issue: title `Decision: <the question in a few words>`

```markdown
<!-- proj-agent -->
🤖 **Claude** (<project> build agent)

### The words
- **<term>:** <one plain line>. (Define every term the question uses.)

### The question
<one or two sentences>

### A story: <time> at <fictional tenant>
<one concrete scene with an on-call person; then:>
- **If <option A>:** <what happens to them>.
- **If <option B>:** <what happens to them>.

### What we found
<what the code and specs do today, checked in the code (file or PR). Say plainly if something promised was never built.>

### What others do
- **<standard / tool / paper>:** <what they do> ([source](url))
- …

**The common pattern:** <one sentence>.

### Choose
1. **<option> (recommended).** <what it means, what it costs>
2. **<option>.** <…>
3. **<option>.** <…>

Reply with the number.
```

## Task for a person: title `Task: <what to do>`

```markdown
<!-- proj-agent -->
🤖 **Claude** (<project> build agent)

### Why a person is needed
<the words first; why the agent can't do it; what it blocks>

### What was already tried
<gh / tunnel / local model / installer…, and what failed>

### Steps
1. <one action: where to click or what to run> → you should see <…>
2. …

### When it's done
Comment "done" here or close the issue. I'm watching it and will continue.
```

## Replies

**Answering a question:**
```markdown
<!-- proj-agent -->
🤖 **Claude** (<project> build agent)

<plain answer: the term defined, a short story or example>

<re-offer the choice in one line: "Reply 1, 2 or 3.">
```

**Recording a decision:**
```markdown
<!-- proj-agent -->
🤖 **Claude** (<project> build agent)

**Recorded: option <N>** <and any extra the human added, restated exactly>.

### What happens now
- <plain consequence 1>
- <who builds it, which PR closes this issue, what proves it>

<any "later" part → "tracked as #M">

Your part here is done, so I've removed `task-to-<owner>`.
```
