# Hardware validation matrix

Every row must be tested on real hardware. Documentation-derived expectations
are not accepted as runtime success.

| Target | L4T | Capture | Encoder paths | Status |
|---|---:|---|---|---|
| Jetson AGX Thor Developer Kit | R39.2 | X11, Wayland, headless | SDK 13.1 NVENCODE, FFmpeg NVENC, V4L2 | Planned |
| Jetson AGX Thor Developer Kit | R38.4 | X11, headless | Sunshine FFmpeg NVENC | Video + input verified at 1080p60 |
| Jetson AGX Orin Developer Kit | R39.2 | X11, Wayland, headless | V4L2, software | In progress |
| Jetson AGX Orin Developer Kit | R38.4 | X11, Wayland, headless | V4L2, software | Planned |
| Jetson Orin Nano Developer Kit | R39.2 | X11, Wayland, headless | software | Planned |
| Jetson Orin Nano Developer Kit | R38.4 | X11, Wayland, headless | software | Planned |

For each row, record:

- exact module and developer-kit identity;
- L4T, Ubuntu, kernel, CUDA, and driver versions;
- active desktop/session type and physical/headless display state;
- capture backend and negotiated resolution/refresh rate;
- encoder API, codec, pixel format, rate control, and actual bitstream proof;
- Moonlight pairing, video, keyboard, mouse, clipboard, and reconnect behavior;
- Corp LAN/VPN UDP behavior without public port exposure;
- CPU, GPU, memory, thermals, power, dropped frames, and end-to-end latency;
- concurrent AI inference workload and measured interference;
- all persistent changes and verified rollback.
