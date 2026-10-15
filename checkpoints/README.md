# Checkpoint convention

Checkpoints are append-only dated Markdown files named `YYYYMMDDTHHMMSSZ-TASK-ID.md` (UTC).

Each checkpoint must contain:

- Task ID, milestone, operator/agent identity and UTC timestamp.
- The exact observed starting state and command evidence (sanitized).
- What changed and which files/services were affected.
- What was tested, with result and timestamp.
- What remains unverified and any rollback instructions.
- The **single next safe action** and whether human approval is required.

If the agent disappears unexpectedly, the next agent must validate reality before resuming. Do not interpret a checkpoint as authorization to apply its next action.

Never store credentials, raw sensitive logs or secret configuration here; this folder is in a public repository.
