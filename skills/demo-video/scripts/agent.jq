# Claude Code stream-json -> one line per tool call, then the final answer.
#   claude -p "<question>" --output-format stream-json --verbose | jq -rj -f agent.jq
if .type == "assistant" then
  (.message.content[]? | select(.type == "tool_use")
   | "\u001b[36m→ \(.name | sub("^mcp__"; "") | sub("__"; ".")) \u001b[2m\(.input | tostring | .[0:90])\u001b[0m\n")
elif .type == "result" then
  "\n\u001b[1;32m■ answer\u001b[0m (\(.num_turns) turns, \((.duration_ms / 1000) | floor)s)\n\n\(.result)\n"
else empty end
