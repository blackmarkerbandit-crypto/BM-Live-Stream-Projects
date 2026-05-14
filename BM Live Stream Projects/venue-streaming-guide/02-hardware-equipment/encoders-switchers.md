# Encoders & Switchers for Venue Streaming

Encoders convert your video/audio signals into a streamable format. Switchers let you cut between multiple cameras in real time. Many modern devices combine both functions.

## Hardware Encoders

Hardware encoders are dedicated devices that take video input (HDMI/SDI) and output a compressed stream (H.264/H.265) to your streaming platform. They are more reliable than software encoding for mission-critical streams.

### Recommended Hardware Encoders

| Device | Inputs | Encoding | Output | Price | Best For |
|--------|--------|----------|--------|-------|----------|
| **Blackmagic Web Presenter 4K** | 1x SDI, 1x HDMI | H.264 | USB-C (as webcam), Ethernet | $600 | Simple single-camera encode |
| **Teradek VidiU Go** | 1x HDMI | H.264 | Cellular + Ethernet bonding | $1,000 | Mobile/outdoor events |
| **Epiphan Pearl Nano** | 1x HDMI | H.264 | RTMP, SRT | $1,200 | Compact standalone encoder |
| **Epiphan Pearl Mini** | 2x HDMI, 2x SDI | H.264 | RTMP, SRT, recording | $3,500 | Multi-input encoding + recording |
| **Teradek Prism** | 1-2x SDI/HDMI | H.264/H.265 | SRT, RTMP, Zixi | $3,000-6,000 | Professional broadcast-grade |
| **LiveU Solo Plus** | 1x HDMI | H.264 | Cellular + Ethernet bonding | $1,000 | Remote venues with poor internet |
| **Magewell Ultra Encode** | 1x HDMI or SDI | H.264/H.265 | NDI, SRT, RTMP | $800-1,000 | Versatile protocol support |

### When to Use a Hardware Encoder

- **Reliability is critical** — dedicated hardware doesn't crash, update, or run out of RAM mid-show
- **No dedicated streaming computer available** — encoders work standalone
- **Remote/outdoor venues** — cellular bonding encoders (Teradek VidiU, LiveU) combine multiple connections
- **Simple single-camera streams** — plug in camera, configure destination, go live

## Video Switchers

Switchers allow real-time switching between multiple camera feeds, adding graphics, and mixing sources.

### Hardware Switchers

| Device | Inputs | Key Features | Price | Best For |
|--------|--------|-------------|-------|----------|
| **Blackmagic ATEM Mini Pro** | 4x HDMI | Streaming built-in, recording, multiview | $450 | Best budget multi-cam streaming |
| **Blackmagic ATEM Mini Extreme ISO** | 8x HDMI | ISO recording all inputs, streaming, SuperSource | $1,300 | Mid-tier with full ISO recording |
| **Blackmagic ATEM 1 M/E Constellation** | 10x SDI | Broadcast-grade, hardware panel | $4,500+ | Large venue / professional |
| **Roland VR-6HD** | 6x HDMI/SDI | Built-in audio mixer, PTZ control | $4,500 | All-in-one with audio mixing |
| **Roland V-160HD** | 16x HDMI/SDI | Large format, streaming encoder built-in | $12,000 | Large productions |
| **FOR-A HVS-110** | 6x SDI | Broadcast-quality effects, keying | $8,000 | Theater / broadcast |

### The Blackmagic ATEM Mini Lineup (Most Popular for Venues)

The ATEM Mini series dominates venue streaming due to price-performance:

| Model | Inputs | Streaming | ISO Record | Price |
|-------|--------|-----------|------------|-------|
| ATEM Mini | 4x HDMI | Via USB only | No | $300 |
| ATEM Mini Pro | 4x HDMI | Direct Ethernet | No | $450 |
| ATEM Mini Pro ISO | 4x HDMI | Direct Ethernet | Yes (all inputs) | $750 |
| ATEM Mini Extreme | 8x HDMI | Direct Ethernet | No | $900 |
| ATEM Mini Extreme ISO | 8x HDMI | Direct Ethernet | Yes (all inputs) | $1,300 |

**Key features across the line:**
- Picture-in-picture, upstream/downstream keyers
- Built-in audio mixer
- Still image storage for graphics/lower thirds
- Multiview output (all cameras on one monitor)
- HDMI program output for projectors/monitors
- Software control via ATEM Software Control app

**Limitations:**
- HDMI only (no SDI) — need converters for SDI cameras
- 1080p max (no 4K switching)
- Limited to H.264 streaming
- No built-in SRT support

### Software-Based Switchers

For venues using NDI workflows or needing more flexibility:

- **vMix** — Professional Windows software. Handles switching, encoding, streaming, recording, and replay. See [vMix Guide](../03-software/vmix-guide.md).
- **OBS Studio** — Free, open source. Good for simple multi-cam switching. See [OBS Guide](../03-software/obs-guide.md).
- **Wirecast** — Professional Mac/Windows option. See [Software Overview](../03-software/overview.md).

## Signal Flow: Camera to Stream

A typical venue streaming signal flow:

```
Cameras (SDI/HDMI/NDI)
    │
    ▼
Video Switcher (ATEM, Roland, or software like vMix)
    │
    ├── Program Output → Projector / In-venue monitors
    ├── Recording → Local SSD or NAS
    │
    ▼
Encoder (hardware or software)
    │
    ▼
Streaming Platform (YouTube, Twitch, Vimeo, etc.)
```

### Connection Types

| Connection | Max Distance | Resolution | Cable | Cost/Run |
|------------|-------------|------------|-------|----------|
| **HDMI 2.0** | ~50 ft (15m) | 4K 60fps | HDMI cable | Low |
| **HDMI (active/fiber)** | 300+ ft | 4K 60fps | Fiber HDMI | Moderate |
| **SDI (3G)** | 300 ft (100m) | 1080p 60fps | BNC coax | Moderate |
| **SDI (12G)** | 300 ft (100m) | 4K 60fps | BNC coax | Higher |
| **NDI (via Ethernet)** | 300+ ft | 4K 60fps | Cat6 Ethernet | Low-Moderate |
| **NDI HX3** | 300+ ft | 4K 30fps | Cat6 Ethernet | Low-Moderate |
| **SRT (via IP)** | Unlimited | 4K | Ethernet/Internet | Low |

**For most venues:** SDI for runs over 50 feet, HDMI for short runs under 50 feet, NDI where you have a solid Gigabit network already in place.

## Buying Guide by Budget

### Starter ($1,000-3,000)
- 2x PTZOptics Move SE cameras
- 1x Blackmagic ATEM Mini Pro
- HDMI cables, basic mounts
- Stream via ATEM's built-in encoder

### Mid-Range ($5,000-15,000)
- 3-4x PTZOptics Move 4K cameras
- 1x ATEM Mini Extreme ISO or Roland VR-6HD
- SDI cabling with HDMI converters (or NDI workflow)
- Dedicated streaming PC with OBS or vMix
- Multiview monitor

### Professional ($15,000-50,000+)
- 4-6x mixed cameras (PTZ + operated)
- Blackmagic ATEM Constellation or Roland V-160HD
- Full SDI infrastructure with patch panels
- Dedicated encoding hardware (Teradek Prism or Epiphan Pearl)
- Redundant streaming paths
- Graphics system (CasparCG, Ross XPression, or vMix)

## Related Guides

- [Cameras](cameras.md) — Choosing the right cameras
- [Network & Bandwidth](../04-network-bandwidth/requirements.md) — Bandwidth for NDI and streaming
- [Software](../03-software/overview.md) — OBS, vMix, and Wirecast comparisons
