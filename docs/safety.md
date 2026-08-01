# Safety contract

## Read-only commands

`inspect` and `plan` must never:

- invoke `sudo` or another privilege escalation mechanism;
- install, upgrade, or remove packages;
- load or unload kernel modules;
- start, stop, enable, or disable services;
- change display modes, firewall rules, routes, or network exposure;
- create a remote-desktop listener;
- send synthetic input events.

## State-changing commands

Future state-changing subcommands must implement a preview/apply boundary. The
preview must state:

1. why the change is needed;
2. exact commands and affected paths;
3. whether sudo, restart, reboot, or network listeners are involved;
4. impact on current GUI, AI workloads, and remote access;
5. validation and rollback commands.

An apply operation must require an explicit flag or interactive approval. It
must not combine unrelated privileged changes into one approval.

## Network exposure

- UPnP is disabled by default.
- Public port forwarding is outside the default workflow.
- Temporary Sunshine listeners bind to an explicitly selected address.
- Existing firewall rules are observed, not rewritten.
- Service discovery is reported separately from listener binding.

## Jetson platform integrity

The project does not use a remote-desktop setup as justification to update
JetPack, L4T, the NVIDIA driver, boot firmware, or the kernel. Missing kernel
features are reported as blockers. Any external-module experiment is a separate,
explicitly approved workflow and must record source tag, vermagic, symbol CRCs,
hash, taint impact, and rollback.

