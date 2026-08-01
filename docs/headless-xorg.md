# Headless NVIDIA Xorg workflow

Sunshine captures an existing desktop. It does not create a GNOME session or
a usable display topology by itself. On NVIDIA Xorg, these headless states have
materially different behavior:

| State | Result | Suitability |
|---|---|---|
| Physical monitor or hardware EDID emulator | Normal non-NULL MetaMode | Preferred baseline |
| Xvfb plus a lightweight X client | Capturable 2D framebuffer | Useful diagnostic |
| Xvfb plus GNOME | GNOME works, but typically uses llvmpipe | Functional fallback, not a performance tier |
| Xorg `Virtual 1920 1080` with no EDID | NVIDIA `NULL` MetaMode | Resolution exists, but Mutter composition may be absent from X11 capture |
| Valid `CustomEDID` plus forced connected output and MetaMode | Non-NULL NVIDIA display | Validated headless performance path |

## Safe decision sequence

1. Run `jetson-remote inspect` and record the active X11/Wayland session,
   connector status, existing EDID, current Xorg configuration, AI workloads,
   and remote-access listeners.
2. Prefer a real monitor or hardware EDID emulator when practical.
3. If a software-only headless display is required, capture an EDID from a
   known-good monitor using the same connector type. Do not commit the EDID:
   it can contain the monitor serial number.
4. Validate the captured file before use:

   ```bash
   ./jetson-remote edid-inspect monitor.edid
   ```

5. Confirm the NVIDIA Xorg display-device name (`DFP-0`, for example) from the
   target host's Xorg log. RandR names such as `DP-0` are a different namespace.
6. Prepare a candidate that preserves the existing `Device` and `Screen`
   sections and adds only the required options:

   ```text
   Option "ConnectedMonitor" "DFP-0"
   Option "CustomEDID" "DFP-0:/etc/X11/edid/monitor.edid"
   Option "MetaModes" "DFP-0: 1920x1080 +0+0"
   ```

7. Before privileged application, create a timestamped backup and a standalone
   rollback command. Applying the candidate requires an explicit approval
   because it writes under `/etc/X11` and restarts the display manager.
8. Validate within a bounded window. Roll back automatically unless all of the
   following are true:

   - Xorg, the display manager, and GNOME return;
   - the MetaMode is non-NULL and the intended RandR output is connected;
   - the requested resolution and refresh rate are active;
   - OpenGL vendor/renderer are NVIDIA, not llvmpipe;
   - a compositor-aware screenshot contains the GNOME desktop;
   - Sunshine initializes the intended hardware encoder;
   - unrelated AI containers and GPU processes remain healthy;
   - no new Xid, NVRM fatal, OOM, or Xorg fatal error appears.

Do not add `UseEDID false`, ignore an EDID checksum, or broadly disable mode
validation as an initial remedy. These options remove safety checks rather than
fixing the display topology.

## Interpreting resolution

Moonlight's stream resolution and the host desktop resolution are independent.
If Moonlight requests 2560x1440 while Xorg is 1920x1080, the encoded stream can
be 2560x1440 without adding desktop detail. Match the client to the host mode to
avoid scaling blur, bandwidth waste, and additional latency.

## Rollback

A rollback must restore the exact pre-test Xorg configuration, remove only the
EDID installed by the test, restart the display manager, and verify the prior
state. Never overwrite or delete unrelated Xorg fragments. Keep SSH available
throughout the test.
