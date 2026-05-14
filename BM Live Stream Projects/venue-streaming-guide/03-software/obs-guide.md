# OBS Studio Setup Guide for Venues

OBS Studio is free, open-source, and the most widely used streaming software. This guide covers setting it up specifically for venue live streaming.

## Installation & System Requirements

### Minimum PC Specs

| Component | 1080p30 | 1080p60 | 4K30 |
|-----------|---------|---------|------|
| CPU | Intel i5-10th gen / Ryzen 5 3600 | Intel i7-10th gen / Ryzen 7 3700X | Intel i9 / Ryzen 9 |
| RAM | 16 GB | 16 GB | 32 GB |
| GPU | GTX 1650 (for NVENC) | RTX 3060 | RTX 4070+ |
| Storage | SSD (for recording) | NVMe SSD | NVMe SSD |
| OS | Windows 10/11, macOS 12+, Ubuntu 22+ | Same | Windows recommended |

Download from [obsproject.com](https://obsproject.com).

## Initial Configuration

### Step 1: Output Settings

Go to **Settings > Output > Advanced Mode**:

**Streaming Tab:**
- Encoder: `NVIDIA NVENC H.264` (if available) or `x264`
- Rate Control: `CBR`
- Bitrate: `5000 kbps` (adjust for your upload speed — see [Network Guide](../04-network-bandwidth/requirements.md))
- Keyframe Interval: `2`
- Preset: `Quality` (NVENC) or `veryfast` (x264)
- Profile: `high`

**Recording Tab:**
- Type: `Standard`
- Recording Path: your SSD
- Recording Format: `mkv` (crash-resilient; remux to mp4 after via File > Remux Recordings)
- Encoder: `NVIDIA NVENC H.264` (separate from streaming encoder)
- Bitrate: `15000-25000 kbps` for high-quality archive

### Step 2: Video Settings

Go to **Settings > Video**:
- Base Resolution: `1920x1080`
- Output Resolution: `1920x1080`
- Downscale Filter: `Lanczos`
- FPS: `30` (conferences/worship) or `60` (music/sports)

### Step 3: Audio Settings

Go to **Settings > Audio**:
- Sample Rate: `48 kHz`
- Channels: `Stereo`
- Mic/Auxiliary Audio: Your audio interface input
- Disable Desktop Audio if not needed (prevents accidental PC sounds in stream)

## Scene Setup for Venues

### Recommended Scenes

Create these scenes for a typical multi-cam venue stream:

| Scene | Contents | When to Use |
|-------|----------|-------------|
| **Wide Shot** | Camera 1 (full stage) | Default/establishing shot |
| **Close-Up** | Camera 2 (performer zoom) | Featured performer |
| **Audience** | Camera 3 (crowd) | Reactions, applause |
| **Picture-in-Picture** | Camera 1 + Camera 2 overlay | Transitional moments |
| **Pre-Show** | Graphic card + background music | Before event starts |
| **BRB / Intermission** | Graphic card + timer or music | Set breaks |
| **Presentation** | Screen capture + speaker camera PiP | Conferences/speakers |
| **End Card** | Graphic with social links + VOD info | Post-event |

### Adding Sources

**For HDMI/SDI cameras (via capture card):**
1. Add Source > Video Capture Device
2. Select your capture card input
3. Set resolution to match camera output
4. Deactivate "Use custom audio device" (handle audio separately)

**For NDI cameras:**
1. Install [OBS NDI Plugin](https://github.com/obs-ndi/obs-ndi)
2. Add Source > NDI Source
3. Select camera from the dropdown
4. Set bandwidth to Highest

**For USB webcams:**
1. Add Source > Video Capture Device
2. Select webcam
3. Set to highest resolution available

## Essential Plugins for Venue Streaming

| Plugin | Purpose | Link |
|--------|---------|------|
| **obs-ndi** | NDI camera/source support | github.com/obs-ndi/obs-ndi |
| **Advanced Scene Switcher** | Automated scene changes on timers or triggers | obsproject.com/forum |
| **Source Record** | Record individual sources separately | obsproject.com/forum |
| **obs-websocket** | Remote control OBS via API (built into OBS 28+) | Built-in |
| **StreamFX** | Advanced effects, 3D transforms, blur | github.com/Xaymar/obs-StreamFX |
| **Closed Captions** | Live auto-captioning via Google/Azure | obsproject.com/forum |

## Multi-Platform Streaming from OBS

### Option 1: Multiple Output Plugin
Install the **Multiple RTMP Output** plugin to stream to several platforms from one OBS instance. Each output gets its own stream key.

### Option 2: Restream.io
Stream once to Restream, which relays to 30+ platforms. Add Restream as your single RTMP destination in OBS.

### Option 3: Custom NGINX RTMP Server
For advanced setups, run a local RTMP relay server that rebroadcasts to multiple destinations. More complex but zero external dependencies.

## Hotkeys for Live Switching

Set up keyboard shortcuts for fast scene switching during the show:

| Action | Suggested Hotkey |
|--------|-----------------|
| Switch to Wide Shot | `F1` |
| Switch to Close-Up | `F2` |
| Switch to Audience | `F3` |
| Switch to PiP | `F4` |
| Switch to BRB | `F9` |
| Switch to End Card | `F10` |
| Start/Stop Streaming | `Ctrl+F11` |
| Start/Stop Recording | `Ctrl+F12` |
| Transition (cut) | `Enter` (numpad) |

## Performance Tips

- **Use hardware encoding (NVENC/QSV)** over x264 to free up CPU for other tasks
- **Close all unnecessary applications** during the stream
- **Set Windows Power Plan to High Performance**
- **Disable Game Mode and Game Bar** in Windows settings
- **If using NDI**, ensure your network switch supports Jumbo Frames and is Gigabit
- **Monitor OBS stats** (View > Stats) — watch for dropped frames and encoding lag
- **Test for 30+ minutes** before any live event to catch overheating or stability issues

## Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| Dropped frames (network) | Insufficient upload bandwidth | Lower bitrate or upgrade internet |
| Dropped frames (encoding) | CPU/GPU overloaded | Switch to hardware encoder, lower resolution, or close other apps |
| Black screen on capture card | Resolution mismatch | Match capture card settings to camera output exactly |
| Audio out of sync | Clock mismatch or buffer issues | Set audio to 48kHz everywhere, check "Use device timestamps" |
| NDI source not appearing | Firewall blocking | Allow OBS and NDI through Windows Firewall |
| Choppy PTZ movement on stream | Low frame rate or encoding lag | Ensure 60fps for PTZ motion, use hardware encoding |

## Related Guides

- [Software Overview](overview.md) — Compare OBS to other options
- [vMix Guide](vmix-guide.md) — When you outgrow OBS
- [Multi-Camera Planning](../05-multi-camera/planning.md) — Designing your camera layout
