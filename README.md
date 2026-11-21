# agent-skills

My collection of portable [Agent Skills](https://agentskills.io): plain folders with a `SKILL.md`, usable by
Claude Code, OpenCode, Codex, Hermes and any agent that reads files and runs shell commands.
One repo = one source of truth: install by symlink and every agent updates with `git pull`.

## Skills

| Skill | Version | What it does | Needs |
|---|---|---|---|
| [explainer-short](skills/explainer-short/) | 1.1.0 | Idea → finished vertical explainer video (MP4 1080×1920 + .srt + cover + upload text) in a dark-canvas, hand-lettered, one-continuous-diagram tech style. Local & free. | node 18+, ffmpeg, uv |
| [video-style-extractor](skills/video-style-extractor/) | 1.0.0 | Example videos (links) → measured style guide (`style.md`) an agent can follow. | ffmpeg, uv |
| [repo-walkthrough-video](skills/repo-walkthrough-video/) | 1.0.0 | Tests every function of a repo for real, then records a narrated, chaptered 1080p walkthrough. | macOS, vhs, ffmpeg, jq, Python+Pillow |
| [product-promo-video](skills/product-promo-video/) | 1.1.0 | Product (link, repo or brief) → finished promo films: a ≤ 60 s story-driven 16:9 film + 15 s and 6 s cuts (or story, teaser, explainer, 9:16, 1:1), camera motion, UI drawn in code, the product's brand, voice-over, synthesized music and sound design, captions. Local & free. | node 18+, ffmpeg, uv, git |
| [github-human-tasks](skills/github-human-tasks/) | 2.0.1 | Decisions and person-only tasks as watched GitHub issues: an approved format (words → story → what we found → what others do → choose), a 🤖 header plus marker, a watcher, and how to record a decision and close it via PR. Also PR review with the human (a reference file): review sets of N (default 5), a PR watcher, merging on their word, and a liaison sub-agent. | gh, python3 |
| [issue-driven-prs](skills/issue-driven-prs/) | 1.0.0 | Every PR starts from an issue written first: Vocabulary, Behaviors (Given / When / Then), Why, Impact. A tracking issue with one sub-issue per PR or stack layer, scenarios mapped to tests, stacks that close only their own issue, issue forms, a two-line AGENTS.md pointer. | gh |

## Bundles (skills that work together)

| Bundle | Skills | For |
|---|---|---|
| [idea-to-video](bundles/idea-to-video.txt) | explainer-short, video-style-extractor | learn a style from examples, then make videos in it |
| [video-all](bundles/video-all.txt) | all four video skills | everything video |
| [github-workflow](bundles/github-workflow.txt) | issue-driven-prs, github-human-tasks | issues before PRs, and the human's decisions and reviews on GitHub |

A bundle is just a text file listing skill names. Skills inside a bundle stay independent folders;
they may mention each other by name, never by path.

## Install

```bash
git clone https://github.com/mohamed-stifi/agent-skills.git ~/agent-skills
cd ~/agent-skills

scripts/install.sh explainer-short                      # Claude Code, symlinked (default)
scripts/install.sh idea-to-video --agent opencode       # a bundle into OpenCode
scripts/install.sh all --agent claude --agent codex     # everything, two agents
scripts/install.sh explainer-short --project ~/my-app   # only for one project (.claude/skills there)
scripts/install.sh explainer-short --ref explainer-short/v1.1.0 --copy   # a pinned, frozen version
scripts/install.sh explainer-short --dir /path/to/any/agent/skills       # any other agent
```

| `--agent` | Installs into (user level) | With `--project DIR` |
|---|---|---|
| `claude` (default) | `~/.claude/skills/` | `DIR/.claude/skills/` |
| `opencode` | `~/.config/opencode/skills/` (OpenCode also reads `~/.claude/skills/`) | `DIR/.opencode/skills/` |
| `codex` | `~/.codex/skills/` | `DIR/.codex/skills/` |
| `hermes` | `~/.hermes/skills/agent-skills/` | — |
| `agents` | `~/.agents/skills/` (shared folder some agents read) | `DIR/.agents/skills/` |

Update symlinked installs: `git pull`. Without any installer, any agent works with:
> Read `<path>/skills/explainer-short/SKILL.md` and follow it.

**For a friend:** clone + `scripts/install.sh <skill> --ref <skill>/vX.Y.Z --copy` gives them exactly the
version you tested.

## Versioning

- Every skill has `metadata.version` (semver) in its `SKILL.md` frontmatter and its own `CHANGELOG.md`.
- **patch** (1.1.**1**): wording/bug fix · **minor** (1.**2**.0): new capability, same usage · **major** (**2**.0.0): usage changes.
- Releases are git tags named `<skill>/v<version>` — each skill is versioned on its own.

```bash
# change skills/<name>/..., bump metadata.version, add a "## x.y.z" entry to its CHANGELOG.md, then:
scripts/validate.sh <name>
git commit -am "<name>: <what changed>"
scripts/release.sh <name>          # creates tag <name>/vX.Y.Z
git push && git push --tags
```

## Add a new skill

```bash
scripts/new-skill.sh my-skill "What it does. Use when the user asks to …"
# write skills/my-skill/SKILL.md (+ references/, scripts/), then
scripts/validate.sh my-skill
```

Rules (checked by `scripts/validate.sh`, also in CI on every push/PR):
- folder name = `name:` in the frontmatter, lowercase-with-dashes; description ≤ 1024 chars, says **what** and **when**
- `metadata.version` + matching `CHANGELOG.md` entry
- no file > 10 MB (download big models at setup time instead)
- no personal absolute paths (`/Users/<you>/…`) and nothing that looks like a secret
- keep `SKILL.md` < 500 lines; put detail in `references/`, code in `scripts/`
- a skill must say how it stops (bounded steps, max retries) — agents must not loop

## Layout

```
skills/<name>/        SKILL.md, CHANGELOG.md, references/, scripts/, (template/ | examples/)
bundles/<name>.txt    skill lists for multi-skill tasks
scripts/              install.sh, validate.sh, new-skill.sh, release.sh
```

## Licenses

[MIT](LICENSE) © Mohamed Stifi, unless noted. Bundled fonts in `skills/explainer-short/template/public/fonts/`
are under the SIL Open Font License (texts next to the fonts).
