# Multi-Camera Setup Planning

## Why Multi-Camera?

A single-camera stream works but gets visually monotonous. Multiple cameras create visual variety, maintain viewer attention, and give your stream a professional broadcast feel. Even adding one extra angle makes a significant difference.

## Camera Position Strategy

### The Three Essential Angles

At minimum, aim for three camera positions:

```
         ┌─────────────────────────────┐
         │          STAGE              │
         │                             │
         └─────────────────────────────┘
               ▲           ▲
              /             \
         CAM 2               CAM 3
        (45° left)         (45° right)
        Close-up            Close-up

                    ▲
                    │
                  CAM 1
               (Front center)
               Wide / Master
                    │
                ┌───┴───┐
                │  FOH  │
                │ Booth │
                └───────┘
```

| Camera | Position | Role | Lens/Zoom |
|--------|----------|------|-----------|
| **Cam 1** | Front of house, center | Wide master shot (full stage) | Wide angle, 12-20x zoom |
| **Cam 2** | 45° left of center | Close-up on performers | 20-30x zoom |
| **Cam 3** | 45° right of center | Close-up / alternate angle | 20-30x zoom |

### Additional Camera Positions (4-6 cameras)

| Camera | Position | Role |
|--------|----------|------|
| **Cam 4** | Rear stage / drummer angle | Unique perspective, reaction shots |
| **Cam 5** | Balcony or overhead | High wide / bird's eye |
| **Cam 6** | Audience / pit | Crowd energy, reactions |

### Venue-Specific Layouts

#### Music Venue / Concert Hall

```
         ┌─────────────────────────────┐
         │          STAGE              │
         │    CAM 4 (rear/drum)       │
         └─────────────────────────────┘
          ▲                         ▲
         CAM 2                   CAM 3
        (wing L)               (wing R)

                    ▲
                  CAM 1
               (FOH wide)

    CAM 5 ──────────── (balcony high wide)
```

#### Conference / Presentation

```
         ┌─────────────────────────────┐
         │    SCREEN / SLIDES          │
         │                             │
         │        PODIUM               │
         └─────────────────────────────┘
               ▲           ▲
              /             \
         CAM 2               CAM 3
      (speaker CU)     (speaker + screen)

                    ▲
                  CAM 1
             (wide room shot)

    + Slide capture via HDMI from presenter laptop
```

#### House of Worship

```
         ┌─────────────────────────────┐
         │      ALTAR / STAGE          │
         │         CAM 3 (overhead)    │
         └─────────────────────────────┘
          ▲                         ▲
         CAM 2                   CAM 4
      (worship CU)          (choir/band)

                    ▲
                  CAM 1
           (wide congregation shot)
```

## Shot Composition Guidelines

### The Rule of Thirds
Place key subjects at the intersection of thirds, not dead center. Most PTZ camera controllers can overlay a grid to help frame shots.

### Shot Types to Pre-Program

For PTZ cameras, save presets for each of these shots:

| Preset # | Shot Type | Description |
|-----------|----------|-------------|
| 1 | Wide | Full stage, all performers visible |
| 2 | Medium | Waist-up of center stage |
| 3 | Close-up center | Head-and-shoulders of lead performer |
| 4 | Close-up left | Head-and-shoulders, stage left performer |
| 5 | Close-up right | Head-and-shoulders, stage right performer |
| 6 | Instrument | Tight on guitar neck, piano keys, drum kit |
| 7 | Audience wide | Crowd reaction shot |
| 8 | Audience close | 2-3 people reacting |

### Cutting Rhythm

| Event Type | Cut Frequency | Style |
|-----------|--------------|-------|
| Rock/pop concert | Every 3-8 seconds | Fast, energetic, cut on beat |
| Jazz/classical | Every 10-20 seconds | Slow, deliberate, follow the solo |
| Conference keynote | Every 15-30 seconds | Alternate speaker and slides |
| Panel discussion | Cut to active speaker | Follow conversation |
| Worship service | Every 10-15 seconds | Smooth, gentle transitions |
| Comedy show | Primarily wide, CU for punchlines | Let jokes land, don't over-cut |

### Common Mistakes to Avoid

- **Cutting too fast** — viewers can't absorb what they're seeing
- **Cutting during camera movement** — always cut to a stable shot
- **Jump cuts** — don't cut between similar-sized shots of the same subject; change angle or size significantly
- **Ignoring audio** — cut on musical beats, not randomly
- **Empty stage on frame** — anticipate performer movement; don't show empty space
- **Crossed eyelines** — keep all cameras on the same side of the stage to maintain consistent screen direction

## Technical Considerations

### Signal Synchronization (Genlock)

When mixing multiple cameras through a switcher, all cameras must be synchronized to prevent glitches during cuts.

- **Hardware switchers (ATEM, Roland)** handle frame synchronization automatically for each input
- **NDI workflows** are inherently synchronized on the network
- **For broadcast-grade setups**, use genlock/tri-level sync from a master sync generator

### Matching Camera Output

All cameras feeding a switcher should output the same:
- **Resolution** (1080p or 4K — don't mix)
- **Frame rate** (29.97, 30, 59.94, or 60 — match exactly)
- **Color space** (Rec. 709 for HD)

If mixing camera brands, perform a **white balance** and **exposure match** across all cameras before the show using a gray card or white wall.

### Tally and Communication

- **Tally lights:** Red indicator on the active (live) camera — critical so operators and performers know which camera is on
- **ATEM Mini** supports tally via HDMI to camera monitors
- **NDI** supports tally natively
- **Intercom/comms:** Director needs to talk to camera operators — use wired comms (ClearCom, RTS) or wireless (Hollyland Solidcom)

## Crew Roles for Multi-Camera

| Role | Responsibility | When Needed |
|------|---------------|-------------|
| **Director / Technical Director** | Calls shots, switches cameras | Always (can be 1 person) |
| **PTZ Operator** | Controls remote PTZ cameras, frames shots | 2+ PTZ cameras |
| **Camera Operator** | Operates handheld/tripod cameras | Operated cameras |
| **Graphics Operator** | Triggers lower thirds, graphics, overlays | Shows needing titles/graphics |
| **Audio Engineer** | Manages stream audio mix | Complex audio events |
| **Stream Monitor** | Watches the live output for issues | Critical events |

For smaller venues, one skilled person can direct and operate PTZ cameras simultaneously for a 2-3 camera show.

## Related Guides

- [Cameras](../02-hardware-equipment/cameras.md) — Choosing cameras for each position
- [Encoders & Switchers](../02-hardware-equipment/encoders-switchers.md) — Connecting cameras to your switcher
- [Software Overview](../03-software/overview.md) — Software-based switching options
