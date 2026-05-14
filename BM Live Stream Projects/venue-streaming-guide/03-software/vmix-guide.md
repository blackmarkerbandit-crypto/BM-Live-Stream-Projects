# vMix Production Guide for Venues

vMix is a Windows-based live production software that combines switching, effects, recording, streaming, and replay in one application. It's the go-to choice for professional venue streaming where OBS runs out of runway.

## Why vMix Over OBS?

| Capability | OBS | vMix |
|-----------|-----|------|
| Instant replay | No | Yes |
| ISO recording (all inputs) | No | Yes |
| Native NDI I/O | Plugin | Built-in |
| Built-in titling/CG | Basic | Full GT Title Designer |
| Virtual sets | Via plugins | Built-in (with tracking) |
| Multi-destination streaming | Plugin | Native |
| Scripting/automation | Limited | Full scripting API |
| Color correction | No | Per-input color controls |
| 4K switching | Limited | Full 4K pipeline |
| SRT support | Yes | Yes |

## License Tiers

| Edition | Inputs | Max Resolution | Key Features | Price |
|---------|--------|---------------|--------------|-------|
| **Basic** | 4 | 1080p | Streaming, recording | $60 |
| **HD** | 1,000 | 1080p | + Replay, GT titles | $350 |
| **4K** | 1,000 | 4K | + 4K, NDI 4 outputs | $700 |
| **Pro** | 1,000 | 4K | + PTZ control, 4 recordings | $1,200 |

For venue use, **HD** is the sweet spot. Move to **4K** when you need higher resolution or heavy NDI workflows.

## System Requirements

| Spec | 1080p (4-cam) | 1080p (8-cam) | 4K (4-cam) |
|------|--------------|--------------|------------|
| CPU | i7-12th gen / Ryzen 7 5800X | i9-13th gen / Ryzen 9 7900X | i9-14th gen / Ryzen 9 7950X |
| RAM | 16 GB | 32 GB | 64 GB |
| GPU | RTX 3060 | RTX 4070 | RTX 4080+ |
| Storage | 1TB NVMe SSD | 2TB NVMe SSD | 2TB+ NVMe RAID |
| OS | Windows 10/11 64-bit | Same | Same |

**Critical:** vMix is Windows-only. No Mac or Linux support.

## Input Setup

### Adding Cameras

1. **NDI Cameras:** Add Input > NDI/Desktop Capture > select camera from NDI source list
2. **Capture Cards (HDMI/SDI):** Add Input > Camera > select capture device
3. **SRT Sources:** Add Input > Stream/SRT > enter SRT URL and port
4. **Presentation slides:** Add Input > NDI/Desktop Capture > select presenter laptop's NDI output (install NDI Tools on laptop)

### Input Configuration

For each camera input:
- **Color Correct:** Adjust exposure, white balance, saturation to match across all cameras
- **Deinterlace:** Enable if cameras output interlaced (1080i)
- **Audio:** Mute video inputs and use a dedicated audio input from your mixer (prevents double audio)

## Production Features

### Transitions

vMix supports cut, dissolve, wipe, and custom stinger transitions. For venue streaming:
- **Cut** for fast-paced music performances
- **Dissolve (0.5s)** for general purpose
- **Stinger transitions** for branded animated transitions between segments

### Overlays (Up to 4 simultaneous)

Use overlay channels for persistent elements:
- **Overlay 1:** Lower third / name titles
- **Overlay 2:** Scoreboard or clock
- **Overlay 3:** Logo bug / watermark
- **Overlay 4:** Social media feed or ticker

### GT Title Designer

vMix includes a built-in title/graphics designer:
- Create lower thirds, full-screen graphics, tickers, and scoreboards
- Data-driven titles that pull from CSV, RSS, or API
- Animated in/out transitions
- Template system for quick changes during the show

### Instant Replay

Available in HD edition and above:
- Mark events during the show with a hotkey
- Play back at variable speed (slow-motion)
- Multiple replay angles if using multiple cameras
- Overlay replay with "REPLAY" graphic automatically

### MultiCorder (ISO Recording)

Record every input independently in addition to the program output:
- Each camera gets its own file at full quality
- Enables post-production editing after the event
- Requires fast NVMe SSD (multiple simultaneous write streams)

## Streaming Configuration

### Output Settings

Go to **Settings > Streaming**:
- **Destination:** Add RTMP/SRT destinations (YouTube, Twitch, Facebook, custom)
- **Quality:** Match your encoding preset to available bandwidth
- **Multiple destinations:** Add up to 3 simultaneous stream outputs

### Recommended Encoding

```
Encoder: NVENC H.264 (FFmpeg)
Bitrate: 5,000-8,000 kbps
Profile: High
Level: 4.1
Keyframe: 2 seconds
Audio: AAC 192-320 kbps, 48 kHz
```

## PTZ Camera Control

vMix Pro includes native PTZ control:
- Control PTZ cameras directly from the vMix interface
- Save and recall presets per camera
- Assign hotkeys to preset positions
- Supports VISCA, VISCA over IP, and NDI PTZ protocols

## Automation with Scripting

vMix supports VB.NET scripting for automation:
- Auto-switch cameras on a timed rotation
- Trigger graphics on audio cues
- Start/stop recording and streaming on schedule
- Integrate with external systems via API

The vMix API also allows HTTP-based control from external devices (Stream Deck, touch panels, custom apps).

## Elgato Stream Deck Integration

The Stream Deck is the most popular physical controller for vMix:
- Map buttons to camera switches, transitions, overlays, replay
- Visual feedback (button icons change based on active input)
- vMix plugin available in Stream Deck store
- 15-button ($150) or 32-button ($250) models

## Related Guides

- [Software Overview](overview.md) — Compare vMix to other options
- [OBS Guide](obs-guide.md) — Free alternative for simpler setups
- [Multi-Camera Setups](../05-multi-camera/planning.md) — Planning your camera layout
- [Encoders & Switchers](../02-hardware-equipment/encoders-switchers.md) — Hardware alternatives to software switching
