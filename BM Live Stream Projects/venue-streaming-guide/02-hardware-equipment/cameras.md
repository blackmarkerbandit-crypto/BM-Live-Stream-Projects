# Cameras for Venue Live Streaming

## Camera Categories

### PTZ Cameras (Pan-Tilt-Zoom)

PTZ cameras are the workhorse of venue streaming. They mount on walls or ceilings, are controlled remotely, and eliminate the need for a camera operator per angle.

#### Recommended Models

| Camera | Resolution | Zoom | Output | Price Range | Best For |
|--------|-----------|------|--------|-------------|----------|
| **PTZOptics Move 4K** | 4K 60fps | 12x/20x/30x | HDMI, SDI, USB, NDI | $1,500-2,500 | Best all-around venue PTZ |
| **BirdDog P4K** | 4K 60fps | 12x | NDI, HDMI | $2,500-3,000 | NDI-native workflows |
| **Sony SRG-X400** | 4K 30fps | 40x | HDMI, IP | $3,000-4,000 | Large venues needing long zoom |
| **PTZOptics Move SE** | 1080p 60fps | 12x/20x/30x | HDMI, SDI, USB, NDI | $800-1,400 | Budget-friendly starter |
| **Panasonic AW-UE160** | 4K 60fps | 20x | SDI, HDMI, NDI, SRT | $8,000+ | Broadcast-grade productions |

**Why PTZ for venues:**
- No operator needed per camera — one person can control multiple PTZ cameras
- Permanent install means consistent framing every show
- Quiet operation (no fan noise audible from audience)
- Presets allow instant recall of common shots (wide stage, close-up on mic stand, audience)

**Setup tips:**
- Mount at least 8-10 feet high to shoot over standing audiences
- Use PoE (Power over Ethernet) models to simplify cabling — one cable for power, control, and video (NDI)
- Program 6-10 presets per camera for common shots
- Place one PTZ front-of-house for a wide establishing shot, and one or two at 45-degree angles for close-ups

### Camcorders

Traditional camcorders are still relevant for venues that want operated cameras for key events or as a supplement to PTZ cameras.

| Camera | Resolution | Key Feature | Price Range | Best For |
|--------|-----------|-------------|-------------|----------|
| **Canon XA75** | 4K 30fps | Dual-pixel AF, SDI out | $2,000 | Reliable operated camera |
| **Sony PXW-Z90V** | 4K 30fps | Fast hybrid AF | $2,500 | Run-and-gun events |
| **Panasonic AG-CX350** | 4K 60fps | NDI/SRT built-in | $3,500 | Direct IP streaming |

**When to use camcorders:**
- You have volunteer or staff camera operators
- Events require follow-the-action shooting (roaming performers, audience interaction)
- Backup camera for critical events

### Mirrorless / Cinema Cameras

For venues that want cinematic depth-of-field and a premium look.

| Camera | Resolution | Key Feature | Price Range | Best For |
|--------|-----------|-------------|-------------|----------|
| **Sony A7 IV** | 4K 60fps | Full-frame, clean HDMI out | $2,500 | Cinematic streaming |
| **Blackmagic Pocket Cinema 6K** | 6K | 12-bit RAW, great color | $1,500 | Film-quality look |
| **Canon R6 Mark II** | 4K 60fps | Excellent low-light | $2,500 | Dark venue environments |

**Considerations:**
- Require external power (battery life insufficient for multi-hour streams)
- Overheating risk on some models during long streams — verify with a 2+ hour test
- Need HDMI capture cards or converters to integrate with switchers
- Manual focus or external focus systems recommended for consistent results

## Choosing the Right Camera

### Decision Factors

| Factor | PTZ | Camcorder | Mirrorless |
|--------|-----|-----------|------------|
| Permanent install | Best | Poor | Poor |
| Operator required | No | Yes | Yes |
| Remote control | Yes | Limited | No |
| Image quality | Good-Excellent | Good | Excellent |
| Low-light performance | Moderate | Good | Excellent |
| Depth of field control | Minimal | Moderate | Excellent |
| Cost per camera | $800-8,000 | $2,000-3,500 | $1,500-2,500 + lens |
| Durability / reliability | Excellent | Good | Moderate |

### Recommendations by Venue Type

- **Small bar/club (1-2 cameras):** 2x PTZOptics Move SE — budget-friendly, remote-controlled, covers the stage
- **Mid-size venue (3-4 cameras):** 2x PTZOptics Move 4K + 1 operated Canon XA75 for roaming + 1 wide lockoff
- **Large theater/concert hall (4-6 cameras):** Mix of PTZ (wide + balcony angles) + operated camcorders + 1 mirrorless for cinematic hero shots
- **House of worship (2-4 cameras):** PTZ cameras are the standard — quiet, remote-controlled, and permanent

## Essential Camera Accessories

- **Mounting hardware:** Wall/ceiling mounts for PTZ; tripods/monopods for operated cameras
- **Power:** PoE injectors for PTZ; V-mount or NP-F battery plates for mirrorless; AC adapters for long events
- **Cabling:** SDI (up to 300ft without boosters) or Cat6 (for NDI); HDMI limited to ~50ft without active cable
- **Tally lights:** Visual indicators showing which camera is live — critical for operated cameras
- **Lens filters:** ND filters for mirrorless cameras in bright environments

## Related Guides

- [Encoders & Switchers](encoders-switchers.md) — How to connect cameras to your streaming pipeline
- [Multi-Camera Setups](../05-multi-camera/planning.md) — Planning camera positions and shot lists
- [Network & Bandwidth](../04-network-bandwidth/requirements.md) — Bandwidth needed for NDI camera feeds
