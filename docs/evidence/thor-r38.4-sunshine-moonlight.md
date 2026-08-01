# Live evidence: AGX Thor, L4T R38.4

Date: 2026-08-01

This record is normalized and omits hostnames, IP addresses, monitor serials,
pairing material, usernames, and internal service names.

## Verified observations

- Platform: NVIDIA Jetson AGX Thor Developer Kit
- L4T: R38.4
- Desktop: GNOME on X11
- Client: Moonlight on Windows over a private corporate/VPN route
- Public exposure: none; UPnP disabled and listeners bound to the selected
  private interface
- Encoder: Sunshine H.264 NVENC (`h264_nvenc`), confirmed by initialization
  and a live bitstream; this was not CPU H.264 encoding
- Client stream: 1920x1080 at approximately 60 FPS, H.264
- Video: full GNOME desktop verified by the user
- Input: keyboard and mouse control verified by the user through uinput
- Client-reported dropped frames: 0% network loss and 0% jitter loss during the
  recorded sample
- Client-reported host processing latency: about 9.8 ms average
- Client-reported network latency: about 63 ms average in the final 1080p sample
- Client decoding time: about 0.25 ms average
- Sunshine process: approximately 3-10% CPU depending on sample; the remaining
  work includes capture, copies, protocol, networking, and input handling
- GPU utilization during an earlier connected sample: approximately 11-23%
- Six pre-existing AI containers remained running with no restart or OOM
- No new GPU Xid, NVRM fatal, OOM, GDM crash, or GNOME crash was observed

The client had initially requested a 2560x1440 stream while the host desktop was
1920x1080. Matching Moonlight to 1920x1080 removed scaling blur and improved the
interactive feel. Stream resolution is not proof of host desktop resolution.

## Headless findings

1. The stock fallback Xorg display was 640x480 and showed only an NVIDIA logo.
2. Xvfb at 1920x1080 was capturable and Sunshine NVENC worked.
3. GNOME on Xvfb was functional but rendered through Mesa llvmpipe.
4. Adding only `Virtual 1920 1080` to NVIDIA Xorg produced a 1920x1080 `NULL`
   MetaMode. GNOME ran on the same X screen, but X11 root capture omitted the
   Mutter composite overlay; Moonlight showed the underlying NVIDIA logo and a
   movable X cursor.
5. A checksum-valid DisplayPort EDID from a known-good monitor, combined with
   `ConnectedMonitor`, `CustomEDID`, and an explicit 1920x1080 MetaMode, yielded
   a non-NULL output. Xorg reported the intended output connected, GNOME used
   the NVIDIA renderer, and Moonlight displayed and controlled the full desktop.

## Platform interpretation

Video Codec SDK 13.1 officially requires Jetson Thor with Jetson Linux R39.2 or
newer. This R38.4 result proves that the installed driver stack exposes an NVENC
path usable by this Sunshine/FFmpeg build; it does not make R38.4 an officially
supported Video Codec SDK 13.1 platform.

## Still planned

- controlled end-to-end latency measurement with a camera or equivalent method;
- repeatable bitrate sweep and visual-quality scoring;
- concurrent AI inference throughput comparison with and without streaming;
- HEVC live-stream validation (initialization was successful, but the recorded
  Windows session used H.264);
- reconnect, suspend, reboot persistence, and long-duration soak tests;
- equivalent tests on Thor R39.2, AGX Orin, and Orin Nano.
