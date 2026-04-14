# Streaming Software Overview

## Software Comparison

| Feature | OBS Studio | vMix | Wirecast | StreamYard | Ecamm Live |
|---------|-----------|------|----------|------------|------------|
| **Price** | Free | $60-$700 | $600-$1,000 | $20-$65/mo | $16-$30/mo |
| **Platform** | Win/Mac/Linux | Windows only | Win/Mac | Browser-based | Mac only |
| **Max inputs** | Unlimited (CPU bound) | 1,000+ | 8-17 | 10 | 15 |
| **NDI support** | Via plugin | Native | Native | No | Limited |
| **SRT support** | Yes | Yes | No | No | No |
| **Recording** | Yes | Yes (ISO too) | Yes | Cloud only | Yes |
| **Instant replay** | No | Yes | No | No | No |
| **Graphics/overlays** | Scenes + browser sources | GT Title, built-in CG | Built-in titles | Built-in templates | Built-in |
| **Virtual sets** | Via plugins | Built-in | No | No | No |
| **Multi-destination** | Via plugins | Native | Native | Native | Via Restream |
| **Learning curve** | Moderate | Steep | Moderate | Easy | Easy |
| **Best for** | Budget setups, Linux | Professional production | Mid-range Mac/Win | Remote guests, simplicity | Mac-based simple streams |

## Choosing Your Software

### Use OBS Studio if:
- You're starting out and need free, capable software
- You're on Linux
- Your setup is 1-3 cameras with basic graphics
- You want a huge community and plugin ecosystem
- You're comfortable with some technical configuration

### Use vMix if:
- You need professional multi-cam production on Windows
- You want instant replay for sports or performances
- You need ISO recording of all inputs simultaneously
- Your workflow includes NDI cameras extensively
- You want built-in graphics, virtual sets, and titling

### Use Wirecast if:
- You need a polished mid-range solution on Mac or Windows
- You value a clean, intuitive interface over maximum features
- You stream to multiple destinations regularly
- You want built-in Rendezvous (remote guest) integration

### Use StreamYard if:
- You primarily stream panels, interviews, or remote-guest shows
- You want the simplest possible workflow (browser-based)
- Your team is non-technical
- You don't need advanced features like NDI, SRT, or ISO recording

### Use Ecamm Live if:
- You're Mac-only and want a clean native app
- You need something more capable than StreamYard but simpler than OBS
- Interview and presentation-style streams are your primary content

## Encoding Settings Reference

These settings work for most venue streaming scenarios:

### Standard 1080p Stream

```
Resolution: 1920x1080
Frame rate: 30fps (talk/conference) or 60fps (music/sports)
Encoder: x264 (software) or NVENC/QSV (hardware)
Rate control: CBR
Bitrate: 4,500-6,000 kbps
Keyframe interval: 2 seconds
Audio codec: AAC
Audio bitrate: 192-320 kbps
Audio sample rate: 48 kHz
```

### 4K Stream (if platform supports it)

```
Resolution: 3840x2160
Frame rate: 30fps
Encoder: NVENC or hardware encoder (x264 too CPU-heavy at 4K)
Rate control: CBR
Bitrate: 13,000-20,000 kbps
Keyframe interval: 2 seconds
Audio codec: AAC
Audio bitrate: 320 kbps
Audio sample rate: 48 kHz
```

### Conservative / Low-Bandwidth Stream

```
Resolution: 1280x720
Frame rate: 30fps
Encoder: x264 or hardware
Rate control: CBR
Bitrate: 2,500-4,000 kbps
Keyframe interval: 2 seconds
Audio codec: AAC
Audio bitrate: 128 kbps
Audio sample rate: 48 kHz
```

## Protocol Comparison

| Protocol | Latency | Firewall-Friendly | Use Case |
|----------|---------|-------------------|----------|
| **RTMP** | 10-30s | Yes (outbound 1935) | Standard platform ingest |
| **SRT** | 1-4s | Needs port forwarding | Low-latency, reliable delivery |
| **RTSP** | 1-3s | Needs port forwarding | Camera-to-encoder on LAN |
| **NDI** | ~1 frame | LAN only | Camera-to-switcher on local network |
| **HLS** | 15-45s | Yes | Playback delivery to viewers |
| **WebRTC** | <1s | Yes | Ultra-low-latency interactive |

## Related Guides

- [OBS Studio Guide](obs-guide.md) — Complete OBS setup for venues
- [vMix Guide](vmix-guide.md) — Professional production with vMix
- [Encoders & Switchers](../02-hardware-equipment/encoders-switchers.md) — Hardware encoding alternatives
