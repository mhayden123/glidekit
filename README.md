# OP Replay Clipper

Render and extract video clips from [openpilot](https://github.com/commaai/openpilot) drives recorded on [comma.ai](https://comma.ai) devices. Runs entirely on your own hardware via Docker with GPU acceleration.

## Desktop App

The easiest way to use the clipper is the **[OP Replay Clipper Desktop App](https://github.com/mhayden123/op-replay-clipper-desktop)**. Download a single installer for your platform and everything is handled automatically.

## Render Types

| Type | Description |
|------|-------------|
| **UI** | openpilot UI replay with path, lanes, metadata overlay, and route branding |
| **UI Alt** | UI variant with steering wheel and confidence rail in the footer |
| **Driver Debug** | Driver camera with DM state, awareness, distraction, pose telemetry |
| **Forward / Wide / Driver** | Raw camera transcodes to compatible H.264 or HEVC MP4 |
| **360** | Spherical video from wide + driver cameras (VLC, YouTube, Insta360 Studio) |
| **Fwd/Wide** | Forward camera projected onto wide using logged camera calibration |
| **360 Fwd/Wide** | 8K 360 with forward-upon-wide overlay for high-res reframing |

All render types support configurable target file size and codec selection (H.264 / HEVC / Auto).

## Download Sources

- **Comma Connect** — Download route data from comma's cloud servers. Route must have Public Access enabled, or provide a JWT token.
- **Local SSH** — Download directly from your comma device on the local network. No cloud upload needed.

## Prerequisites

- **Linux** with an NVIDIA GPU and drivers installed (`nvidia-smi` should work)
- **[Docker Engine](https://docs.docker.com/engine/install/)** with Compose V2
- **[NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)**

Verify GPU access:
```bash
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

## Quick Start

```bash
# One-command setup: checks prerequisites, builds Docker images
./install.sh

# Start the web UI (opens browser to http://localhost:7860)
./start.sh
```

Or step by step:
```bash
make docker-build    # Build render + web images (~15-30 min first time)
make docker-web      # Start web UI at http://localhost:7860
```

## Usage

1. Open the web UI at `http://localhost:7860` (or use the [Desktop App](https://github.com/mhayden123/op-replay-clipper-desktop))
2. Choose a download source (Comma Connect or Local SSH)
3. Paste a Comma Connect URL or pipe-delimited route ID
4. Select a render type
5. Click **Start Render** and watch real-time progress
6. Download or preview the finished clip

### URL Formats

The clipper accepts these route URL formats:

| Format | Example |
|--------|---------|
| Full clip URL | `https://connect.comma.ai/dongle/route/start/end` |
| Absolute time URL | `https://connect.comma.ai/dongle/start_ms/end_ms` |
| Route-only URL | `https://connect.comma.ai/dongle/route-name` |
| Pipe-delimited ID | `dongle_id\|route-name` |

Route-only URLs and pipe-delimited IDs render the full route duration.

### Smear Preroll (UI renders)

UI renders (`ui`, `ui-alt`, `driver-debug`) use a hidden preroll period before the visible clip starts. This initializes openpilot's UI state (lead car markers, lane coloring, etc.) so the clip opens with the correct visual state rather than blank elements.

### JWT Tokens

For routes without Public Access, provide a JWT token from [jwt.comma.ai](https://jwt.comma.ai). Tokens are valid for 90 days and grant access to all routes on the account.

## Docker Images

Pre-built images are published to GitHub Container Registry:

```bash
docker pull ghcr.io/mhayden123/op-replay-clipper-web:latest
docker pull ghcr.io/mhayden123/op-replay-clipper-render:latest
```

## CLI Usage

```bash
uv sync
uv run python clip.py ui "https://connect.comma.ai/<dongle>/<route>/<start>/<end>"
uv run python clip.py forward --demo
uv run python clip.py driver-debug --demo --length-seconds 5
```

## Makefile Targets

| Target | Description |
|--------|-------------|
| `make docker-build` | Build render and web images |
| `make docker-web` | Start web UI at localhost:7860 |
| `make docker-render-test` | Quick smoke test (forward --demo) |
| `make docker-logs` | Tail recent web container logs |
| `make docker-clean` | Remove built images and stopped containers |
| `make docker-check` | Print Docker/GPU/image status |

## Architecture

```
Desktop App / Browser
        |
        v
   Web Container (FastAPI, port 7860)
        |
        v (spawns per-job via Docker socket)
   Render Container (NVIDIA GPU)
        |
        v
   clip.py -> core/ -> renderers/
```

The web container serves the UI and spawns render containers on demand. Each render container downloads route data, runs the rendering pipeline, and writes the output to a shared volume.

## Credits

Based on [nelsonjchen/op-replay-clipper](https://github.com/nelsonjchen/op-replay-clipper). UI replay built on openpilot's replay tooling by [@deanlee](https://github.com/deanlee). FFmpeg pipeline based on research by [@ntegan1](https://github.com/ntegan1).

## License

See [LICENSE.md](LICENSE.md).
