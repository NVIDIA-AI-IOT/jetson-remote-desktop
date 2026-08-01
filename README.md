# Jetson Remote Desktop

Safe, reproducible discovery and setup workflows for low-latency remote
desktop access to NVIDIA Jetson systems.

The project evaluates Sunshine + Moonlight first, while keeping RDP,
NoMachine, and VNC-family servers available as comparison and fallback paths.
It treats platform discovery, planning, state-changing setup, validation, and
rollback as separate phases.

## Status

Early development. The initial implementation provides read-only inspection
and an evidence-based plan. It does not install packages, load kernel modules,
change the firewall, or start remote-desktop listeners.

## Quick start

```bash
git clone https://gitlab-master.nvidia.com/Jetson-TME/jetson-remote-desktop.git
cd jetson-remote-desktop

./jetson-remote inspect
./jetson-remote inspect --json
./jetson-remote plan
```

`inspect` and `plan` are intentionally read-only and never invoke `sudo`.

## Safety model

State-changing workflows will follow these rules:

- inspect current state before proposing a change;
- never update JetPack, NVIDIA drivers, or the kernel implicitly;
- never change firewall policy, expose public ports, or enable UPnP implicitly;
- show each privileged command, its impact, and its rollback before execution;
- keep temporary evaluation separate from persistent installation;
- do not stop or reconfigure unrelated AI workloads or remote-access services;
- bind temporary listeners to an explicitly selected interface address;
- save machine-readable evidence for every validation run.

See [docs/safety.md](docs/safety.md) for the detailed contract.

## Initial platform matrix

The repository distinguishes three questions that are often conflated:

1. Does the SoC contain a hardware video encoder?
2. Which Jetson multimedia API exposes it on this L4T release?
3. Is NVIDIA Video Codec SDK 13.1 officially supported?

Video Codec SDK 13.1 officially targets Jetson Thor with Jetson Linux 39.2 or
newer. That does not imply that every other Jetson lacks hardware encoding;
older Jetson multimedia/V4L2 paths are evaluated separately.

| Platform | L4T | HW encode | Video Codec SDK 13.1 | Primary evaluation path |
|---|---:|---|---|---|
| Jetson AGX Thor Developer Kit | R39.2 | Yes | Official target | NVENCODE API, FFmpeg NVENC, Sunshine |
| Jetson AGX Thor Developer Kit | R38.4 | Yes | No: L4T too old | Jetson V4L2/GStreamer, Sunshine probe |
| Jetson AGX Orin Developer Kit | R39.2 | Yes | No: SoC not listed | Jetson V4L2/GStreamer, software fallback |
| Jetson AGX Orin Developer Kit | R38.4 | Yes | No: SoC and L4T | Jetson V4L2/GStreamer, software fallback |
| Jetson Orin Nano Developer Kit | R39.2 | No NVENC | No | Software H.264/HEVC |
| Jetson Orin Nano Developer Kit | R38.4 | No NVENC | No | Software H.264/HEVC |

Statuses in this table are hypotheses or documentation-derived constraints
until an evidence record is attached to a tested device. The machine-readable
source is [manifests/support-matrix.json](manifests/support-matrix.json).

## Planned workflow

```text
inspect (read-only)
  -> plan (read-only)
  -> prepare (download and verify only)
  -> run (bounded temporary listener)
  -> pair (explicit Moonlight PIN)
  -> validate (video, input, load, latency)
  -> benchmark (including AI contention)
  -> report
  -> rollback or install (separate approval)
```

## Current evidence

The initial design is informed by live evaluation on:

- Jetson AGX Thor, L4T R38.4: X11 capture and Sunshine H.264/HEVC NVENC
  initialization succeeded; transient external `uinput` was required because
  the running kernel had `CONFIG_INPUT_UINPUT` disabled.
- Jetson AGX Thor, L4T R39.2: target for the Video Codec SDK 13.1 NVENCODE
  workflow; full SDK sample proof remains pending.
- Jetson AGX Orin, L4T R39.2: FFmpeg `h264_nvenc` reported unsupported device;
  software x264 succeeded. Jetson V4L2 needs further characterization.

Raw machine-specific evidence is deliberately not committed until it has been
redacted and normalized into the repository schema.

## References

- [NVIDIA Video Codec SDK 13.1 Read Me](https://docs.nvidia.com/video-technologies/video-codec-sdk/13.1/read-me/index.html)
- [NVIDIA Jetson Linux R39.2 Developer Guide](https://docs.nvidia.com/jetson/archives/r39.2/DeveloperGuide/index.html)
- [NVIDIA accelerated GStreamer documentation](https://docs.nvidia.com/jetson/archives/r39.2/DeveloperGuide/SD/Multimedia/AcceleratedGstreamer.html)
- [Sunshine documentation](https://docs.lizardbyte.dev/projects/sunshine/latest/)
- [Moonlight documentation](https://github.com/moonlight-stream/moonlight-docs/wiki)

