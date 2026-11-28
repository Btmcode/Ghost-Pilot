# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 5.16.x | ✅ |
| < 5.16 | ⚠️ upgrade recommended |

## Reporting a vulnerability

Please **do not** open a public issue for security problems.

1. Open a [private security advisory](https://github.com/Btmcode/Ghost-Pilot/security/advisories/new), or
2. E-mail **devcloudpy@gmail.com** with the subject "GhostPilot security",
   or write through [btmcode.vercel.app](https://btmcode.vercel.app).

You can expect a first reply within **72 hours**. Please include:

- GhostPilot version (`python kur.py durum`)
- Operating system
- Steps to reproduce
- Impact (what an attacker could do)

## Threat model

GhostPilot is a **local** server. It listens on `127.0.0.1` only. Nothing is reachable from the network unless you explicitly start a tunnel.

The main risks we design for:

| Risk | Mitigation |
|---|---|
| Another local program using the server | Bearer access key is required for every request |
| An assistant running destructive commands unnoticed | Approval screen for risky tools, audit log, ghost cursor |
| Unattended access while you are away | `python kur.py dur` (emergency stop), read-only mode |
| Tunnel accidentally left open | Tunnel is opt-in, one command to close, address is random |
| Quota tampering | Signed counter, several redundant copies, clock-change detection |

## What GhostPilot does NOT protect against

Be honest with yourself about these:

- **A user who edits the source code.** It runs on your machine with your permissions. Open code can always be modified.
- **A malicious assistant you deliberately connect.** If you grant access, it can do what the tools allow — use read-only mode and approvals for unknown assistants.
- **Malware already on the machine.** Same permissions, same files.

## Hardening checklist

- [ ] Keep `read_roots` / `write_roots` narrow (one project folder, not the whole disk)
- [ ] Use `onay: "hepsi"` when trying a new assistant
- [ ] Enable read-only mode for "read my files and summarise" tasks
- [ ] Run `python kur.py dur` when you finish working
- [ ] Close the tunnel (`python kur.py tunel-kapat`) after phone sessions
- [ ] Review `~/.ghostpilot/audit.log` occasionally

## Dependencies

GhostPilot uses **only the Python standard library** — no third-party packages, no supply chain to audit.

## Data handling

No telemetry, no analytics, no account. Files are read and written locally. Document contents and tool results go only to the assistant you connected, through your own machine. See [GIZLILIK.md](GIZLILIK.md).
