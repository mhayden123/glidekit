# OP Replay Clipper

Render openpilot driving replay clips locally with GPU acceleration. Supports all openpilot render types including full UI overlay, driver debug, 360 video, and raw camera transcodes. Runs natively on Linux, Windows, and macOS with no Docker dependency.

## Render Types

| Type | Description | Requires openpilot |
|------|-------------|-------------------|
| `ui` | openpilot UI overlay with path, lanes, and metadata | Yes |
| `ui-alt` | Alternative UI layout with steering wheel and confidence rail | Yes |
| `driver-debug` | Driver camera with DM state, awareness, and pose telemetry | Yes |
| `forward` | Forward camera transcode (fast, no overlay) | No |
| `wide` | Wide camera transcode | No |
| `driver` | Driver camera transcode | No |
| `360` | Spherical 360 video from wide + driver cameras | No |
| `forward_upon_wide` | Forward projected onto wide using camera calibration | Yes |
| `360_forward_upon_wide` | 8K 360 with forward projected onto wide | Yes |

## Installation

### Linux

```bash
git clone https://github.com/mhayden123/op-replay-clipper-native.git
cd op-replay-clipper-native
./install.sh
```

The installer takes 10-20 minutes on first run. It installs system packages, clones openpilot, builds native dependencies, and generates font atlases. Re-running is safe and skips completed steps.

### macOS (beta)

```bash
git clone https://github.com/mhayden123/op-replay-clipper-native.git
cd op-replay-clipper-native
./install.sh
```

Requires Homebrew. Uses VideoToolbox for hardware acceleration. Headless rendering support is experimental.

### Windows

Download the desktop app from [releases](https://github.com/mhayden123/op-replay-clipper-desktop/releases) -- it handles everything automatically (installs Python, Git, FFmpeg, and the clipper project).

Or manually:
```bash
git clone https://github.com/mhayden123/op-replay-clipper-native.git
cd op-replay-clipper-native
python install_windows.py
```

Non-UI render types (forward, wide, driver, 360) work natively. UI render types require WSL -- the desktop app guides you through setup.

## Usage

### Web UI

```bash
./start.sh
```

Opens `http://localhost:7860` in your browser. Paste a Comma Connect URL, pick a render type, and click Clip.

### CLI

```bash
# Forward camera transcode (no openpilot needed, fast)
uv run python clip.py forward --demo

# Full UI render with openpilot overlay
uv run python clip.py ui --demo

# Render a specific route from Comma Connect
uv run python clip.py ui "https://connect.comma.ai/<dongle>/<start>/<end>"

# SSH download from a comma device on LAN
uv run python clip.py forward "<route>" --download-source ssh --device-ip 192.168.1.x

# Max quality (no file size limit)
uv run python clip.py ui "<route>" -m 0

# HEVC output
uv run python clip.py forward "<route>" --file-format hevc
```

### Desktop App

For a native GUI, download [OP Replay Clipper Desktop](https://github.com/mhayden123/op-replay-clipper-desktop/releases). It manages the server automatically -- no terminal needed.

## Platform Support

| Feature | Linux | Windows | macOS |
|---------|-------|---------|-------|
| Non-UI renders | Native | Native | Native |
| UI renders | Native | Via WSL | Native (beta) |
| GPU acceleration | NVIDIA (NVENC) | NVIDIA (NVENC) | VideoToolbox |
| CPU fallback | Yes | Yes | Yes |
| Desktop app | Yes | Yes (auto-setup) | Yes |

## Requirements

- **Linux**: Ubuntu 22.04+, Mint 21+, or Pop!_OS 22.04+. NVIDIA GPU + drivers recommended (CPU works but slower).
- **Windows**: Windows 10/11. Python 3.12+ for non-UI renders. WSL + Ubuntu for UI renders.
- **macOS**: Apple Silicon or Intel. Homebrew. Xcode command line tools.
- **Disk space**: 15 GB for openpilot build + dependencies.

## Management

```bash
./install.sh              # Re-run (skips completed steps)
./install.sh --help       # Show all options
./install.sh --uninstall  # Remove ~/.op-replay-clipper/
```

## Architecture

```
Browser / Desktop App
    |
    v
FastAPI Server (port 7860)
    |
    v
clip.py -> core/ -> renderers/
    |
    v
openpilot (native build)
NVIDIA GPU (NVENC) or CPU (libx264)
    |
    v
output.mp4
```

## Credits

- [nelsonjchen](https://github.com/nelsonjchen) -- original op-replay-clipper
- [commaai](https://github.com/commaai) -- openpilot, replay tools, and patched raylib
- [deanlee](https://github.com/deanlee) -- openpilot replay binary
- [ntegan1](https://github.com/ntegan1) -- EGL pbuffer headless rendering patches

## License

See [LICENSE.md](https://github.com/mhayden123/op-replay-clipper/blob/main/LICENSE.md).
