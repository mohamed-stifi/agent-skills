# Narration recipe: KodeKloud-style tech Shorts (23 transcripts)

The corpus: 23 Shorts, median 170 s, 593 words, 207 wpm. Quotes are trimmed, with Whisper typos fixed.

## 1. Topic selection

| Category (n) | Title formula | Views |
|---|---|---|
| Interview fundamentals (6) | `Interview: How X Actually Works` / `Interview: Why X…` | TCP+TLS+HTTP 354k, Indexing 251k, DNS 166k, B-tree vs B+ 92k, Cookies 58k, Docker 54k (avg 162k) |
| System design (3) | `System Design: How <famous product> <does Y>` | Auth 264k, YouTube resume 206k, Slack 67k (avg 179k) |
| X vs Y (2) | `X vs Y` | **MCP vs UTCP 561k**, NGINX vs HAProxy 38k |
| New/news (2) | `What Is the New X?` / `Why X Wasn't Enough for <Co>!` | **HTTP QUERY 434k**, **Git→Anthropic 406k** |
| "How does X…?" (4) | `How Do/Does X <verb>?` | Maps 82k, Routers 79k, MCP usage 43k, Vault 11k (avg 54k) |
| What is X (2) | `What Are X and How Do They Work!` | Guardrails 70k, Ansible 31k |
| Named problem (2) | `The <Nickname> Problem in X` | Celebrity 121k, K8s DR 11k |
| Beginner orientation (1), Puzzle (1) | `X Explained for Beginners`, `Tricky Interview Question!` | Linux dirs 90k, 8÷2(2+2) 16k |

- **What wins:** the top 3 are new or trending AI and web things. Next come fundamentals that people "know but can't explain", framed as interview or system-design questions.
- **What loses:** niche ops topics (Vault, DR) and vague titles.
- **Title traits:** titles name a familiar brand or protocol and promise the hidden mechanism ("Actually", "Knows", "Detects"). 10 of 23 end with an emoji.

## 2. Hook (first ~10 s)

- **Timing:** the topic question is asked by ~3 s (median). A concrete scenario starts at 3–6 s (17/23). The scenario ends in a restated "So how does X…?" at 8–16 s, and the mechanism starts at ~10–20 s.
- **What's absent:** no greeting, no channel name, no "in this video".
- **Sentence 2:** usually "Let's say…" (the phrase appears in 19/23 videos).

| Pattern (n) | First sentences |
|---|---|
| Direct question (11) | B-tree "What is the difference between a btree and a bplus tree?"; MCP/UTCP "What is the difference between MCP and UTCP?"; MCP-use "How do you actually use an MCP server?"; Vault "How does your Kubernetes cluster work with HashiCorp Vault?"; Auth "How would you build an authentication system for an Instagram-like app…?"; DR "How should you prepare for disaster recovery in Kubernetes?"; Cookies "What are cookies in your browser?"; Slack "How does Slack deliver one message to thousands…?"; Indexing "How does database indexing actually work?"; Guardrails "What are AI guardrails?"; Ansible "What is Ansible? Why do we need it?" |
| Knowledge gap (3) | Routers, TCP/TLS "A lot of people know/understand X… but when I ask them…"; DNS "A lot of people think DNS is one big server…" |
| News fact (2) | "HTTP just got a new method called query."; "Anthropic moved away from Git and created their own tool…" |
| Interview framing (2) | Docker "Let's take one Docker interview question."; YouTube "Let's solve one system design interview question." |
| Everyday observation (2) | Maps "When you use Google Maps with the traffic layer enabled…"; Linux "The first time you explore Linux's top level directories…" |
| Named problem / paradox (1) | "One of the problems with database sharding is the celebrity problem." |
| X vs Y label (1) | "Nginx vs HAProxy." then "So when should you use…?" |
| Puzzle (1) | "What is the answer to this equation based on your understanding?" |

## 3. Running example

All **23/23** videos use one concrete scenario for the whole video.

- **Named person, 9/23:** Alan ×4 (MCP/UTCP, Vault, NGINX, Slack), John (Auth), Nicole the pop star (Sharding), Paul (Slack), Nina plus 8 named users (Indexing, B-tree), Alex (Linux).
- **"You" as the protagonist, ~12/23:** "You are uploading a 20 GB file to YouTube".
- **Concrete data:** `session ID = abc123`, ad ID `789`, `apple.com`, `tax.py` in the billing folder, `localhost 3000/signup`, `142.250.183.238`, `ns1.google.com`, refund order `4821` for `$5000`, $1 Chevy Tahoe, Nike/Puma t-shirts under $30, user ID `500` salted to `500-1…500-10`, 20 Apache servers.

**How it is reused.** Every step happens *to the example*. Mention counts: John 20×, Alan 14×, Nicole 13×, Apache 13×, Nina 10×. Two moves recur:
- **Escalation.** The same example is scaled up to expose a limit: "Let's find Nina one more time, but among 10 million users", "Now imagine Alan has 100 applications".
- **Variation.** A new branch keeps the same cast: Nicole gets her own shard, then a cache, then salting.

The payoff is stated in example terms: "send the remaining 6 GB".

## 4. Structure / beats

**Core explainer (~170 s):**
1. Hook question (2%, 0–3 s)
2. Scenario: person + concrete input + desired outcome (8–10%)
3. Naive approach or likely belief and why it fails, e.g. "Usually we…", "You might think…" (10–15%)
4. Mechanism step by step on the example, with terms named on arrival (40–45%)
5. Twist or second problem plus its fix: "But there's a problem", "But what if…?" (15–20%)
6. Synthesis or mental model: "So remember…", "If you notice…" (5–8%)
7. CTA (2%, last ~3 s)

**Variant A, Interview "How X works"** (Indexing, DNS, TCP/TLS, Cookies): question → scenario → follow the request/data hop by hop → "Focus on what just happened" recap with step count → scale-up → cost/limit → one-line summary.

**Variant B, X vs Y** (MCP/UTCP, NGINX/HAProxy, B-tree/B+): question → one shared scenario → "Let's start with X" → "Now let's see Y" (same scenario) → "If you notice, in both cases…" → "The biggest difference is…" → trade-off → "Easy way to remember: use X if…, use Y if…".

**Variant C, System-design ladder** (Auth, Slack, YouTube, Sharding): scaled question → user journey → simple design → "This works well, but there is a problem" at scale → fix 1 → new threat ("what if someone steals…?") → fix 2 → clever twist (token rotation, salting) → limit. It runs as 2–4 problem→fix rungs of 25–40 s each.

## 5. Sentence-level style

- **Length:** ~14 words per sentence on average (median 12), about 42 sentences per video. Short punch lines alternate with one longer "So…, because…" sentence.
- **Vocabulary:** plain spoken English with contractions. The only jargon is the topic's own terms, each defined in-line. No hype.
- **Pronouns per video:** you/your ≈11, we/our/us ≈5, let's ≈2.3, I ≈0.4 (only "when I ask people"). "We" stands for the system designer and "you" for the user or engineer.
- **Questions:** 3–5 rhetorical questions per video, each opening a new beat.
- **Top 20 signposts** (occurrences / videos):

| Phrase | Count | Phrase | Count |
|---|---|---|---|
| So… (sentence start) | 97/22 | That's why… | 13/9 |
| But… (sentence start) | 60/23 | But what…? / What if…? | 12/11 |
| Now… / Now let's… | 56/22 | Let's see / start with / take | 12/10 |
| Let's (any) | 54/23 | For example, | 10/6 |
| First / Second / Third | 40/25/11 | Once… | 10/8 |
| Then… | 40/16 | Notice / If you notice | 9/8 |
| …called X / This is called X | 39/18 | That's where / This is where… comes in | 7/7 |
| Let's say… | 28/19 | Imagine… / Now imagine… | 7/7 |
| Actually | 16/13 | You might think / You may ask | 7/6 |
| Instead of… | 15/10 | Basically, / Finally, | 5/5 each |

- **Terms:** the need comes first, then the thing, then the name: "This sorted list is called an index." Acronyms are expanded and given a one-line purpose ("RPO tells you how much data… you can afford to lose").
- **Numbers:** ~7 per video. They are round and concrete (10 million users, 1M req/s, 15 minutes), and the arithmetic is done aloud: "three steps instead of nine", "200 volumes… roughly 100 gigabytes".

## 6. Explanation technique

- **Literal data flow beats analogy.** The default is to follow one request, packet, row, or token hop by hop. Analogies appear in only ~6/23 videos, each a single clause: a frame is "an envelope around the IP packet", blocks are linked "like a chain", "roughly similar to Program Files".
- **Components talk.** Components get quoted dialogue: "I don't know, but ask the .com servers."
- **On-screen pointers are rare.** "like this" and "you see" appear ~10 times across the corpus. The audio stands alone.
- **Misconceptions are corrected explicitly in ~9/23 videos.** The pattern is belief → grant → break: "You might think TCP can solve this… correct, but…", "encoding isn't encryption", "these 10 keys are not 10 new machines".
- **Depth:** beginner-to-intermediate (interview prep). Real names are dropped (Redis, Vitess, BGP, CloudFront's 8 KB limit, `docker rm -v`), but there is no code or math beyond arithmetic.

## 7. Ending and CTA

- **CTA (21/23):** "If this video helped, hit subscribe and follow." (~2.5 s, no pause)
- **Exceptions:** Sharding ends with "To dive deeper, watch our long video on database sharding." Auth has no CTA and ends on its twist ("John has to log in again").
- **Last ~10 s before the CTA:**
  - ~11 videos give a recap or mental model ("So the mental model for you is…", "So remember, DNS finds…, TCP establishes…, TLS secures…, HTTP sends…", "Easy way to remember is…").
  - ~4 give a practical tip or caveat (`docker rm -v`, "your CDN might not support this").
  - ~3 give a callback to the hook ("The next time you see a road turn red… now you know").
  - The rest end on a surprising fact ("only seven engineers built Sion"), a term reveal (BGP), or an edge case.

## 8. Rules for writing in this style

1. Write 520–640 words (160–178 s at ~207 wpm).
2. Sentence 1 is the question, news fact, or "A lot of people think X…", in ≤16 words. No greeting or channel name.
3. Sentence 2 starts "Let's say…" with a named person (or "you") plus one concrete input, within 6 s.
4. By ~15 s, restate the question in example terms: "So how does <system> know…?"
5. Show the naive approach or likely belief and exactly why it fails, using one number.
6. Name each term only after its need is shown ("This is called X" / "That's where X comes in"). Use at most 4 new terms.
7. Narrate the mechanism hop by hop on the example: sender, receiver, payload.
8. Mention the example's name or value at least 8 times. Never switch to an abstract "a user".
9. Ask 3–5 rhetorical questions, each opening a beat ("But what if…?", "So why not…?").
10. Put one twist or second problem at 65–80% of runtime, and resolve it.
11. For comparisons, run both options through the same scenario, then say "If you notice, in both cases…" and "The biggest difference is…".
12. Use 5–9 round numbers and do one calculation aloud.
13. Average ~14 words per sentence. Open ≥30% of sentences with So / But / Now / Then / Let's.
14. Use at most one analogy, one clause long.
15. Correct one misconception explicitly ("You might think X. That's correct, but…").
16. Reference visuals at most twice.
17. End with a one-sentence mental model, then "If this video helped, hit subscribe and follow."
18. No hype, jokes, or self-promotion. The tone is a calm senior engineer at a whiteboard.

## 9. Annotated example: "System Design: How YouTube Knows Where to Resume" (206k views, 495 words)

[HOOK: interview framing] Let's solve one system design interview question. [SCENARIO: "you" + numbers, 2 s] You are uploading a 20 GB file to YouTube, and 14 GB is already uploaded, but suddenly your Wi-Fi disconnects. Your internet comes back after one minute, and YouTube continues uploading from where it left instead of starting from zero. [RESTATED QUESTION, 15 s] So how does YouTube know exactly where to continue from?

[MISCONCEPTION / NAIVE ANSWER, 17 s] You might think TCP can solve this, because it is reliable and TCP sends the lost data packets again. And this is correct, but it only works if this connection is still alive. If the TCP connection completely breaks, then a new TCP connection won't know how much of the video YouTube has already saved. [REQUIREMENT, 37 s] So we have to remember the upload progress. Otherwise, we have to upload the entire file again. Therefore, we need to track the upload progress on the YouTube server.

[MECHANISM 1, question-led, 46 s] So how does the server track the progress of upload? Before uploading the video, the browser first asks YouTube's server to start a new upload. And YouTube returns a unique upload URL. So even if the connection breaks, the next connection can find the same upload again using this unique upload URL. [TERM AFTER NEED, 61 s] This is called an upload session. [MECHANISM 2, 64 s] Now the browser starts sending the 20 GB video to that address. YouTube doesn't wait for the complete file. As the server receives the data, it saves the received bytes and keeps track of how much has been successfully uploaded. So if the connection breaks halfway, we know what we have already received.

[TWIST: replay the failure point, 82 s] Now imagine our Wi-Fi disconnects at 14 GB. Our laptop thinks it has already sent 14.2 GB because it has sent that much data. But some of that data got lost, and the server has actually saved only 14 GB, not 14.2 GB. Our laptop and YouTube disagree about how much of the video was uploaded. [RESOLUTION, 102 s] Therefore, we keep YouTube's server progress as the source of truth. And when the browser sends a small request to the same upload URL and asks how much data YouTube has saved, YouTube reports the saved position, and the browser continues sending the video from that point onwards. [ARITHMETIC PAYOFF, 119 s] So instead of uploading 20 GB again, we only need to send the remaining 6 GB. [TERM] This is called a resumable upload.

[SECOND MISCONCEPTION, 127 s] One more point I wanted to clarify. You may think the video has to be split into small pieces, each sent as a separate request. But that's not true. A resumable upload can transfer the file in one long request, and still recover from an interruption. What matters is that the server remembers the progress. [LIMIT, 143 s] And if the upload session expires, we may have to create a new session and start the upload again.

[MENTAL MODEL, 148 s] So the idea is not to make the network reliable. It's to make your upload progress survive a broken connection. [GENERALISE, 157 s] And that's the basic idea behind resumable uploads, whether you're uploading videos, large files, or backups. [CTA, 161 s] If this video helped, hit subscribe and follow.
