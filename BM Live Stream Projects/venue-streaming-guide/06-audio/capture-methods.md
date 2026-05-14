# Audio Capture for Live Venue Streaming

Audio quality makes or breaks a live stream. Viewers will tolerate mediocre video far longer than bad audio. Getting clean audio from a live venue environment is the single most important technical challenge in venue streaming.

## Audio Sources in a Venue

| Source | What It Captures | Quality | Control |
|--------|-----------------|---------|---------|
| **FOH board direct feed** | The main mix going to PA speakers | Excellent | Full |
| **Dedicated stream mix (Aux send)** | A custom mix created for the stream | Best | Full |
| **Stage box / splitter** | Raw mic signals before FOH mixing | Raw (needs mixing) | Full |
| **Ambient room microphones** | Room sound, audience, natural reverb | Variable | Limited |
| **Camera on-board mics** | Whatever the camera hears | Poor | None |

## Method 1: Direct Feed from FOH (Front of House)

The simplest approach: take the main stereo mix output from the venue's mixing console.

### How to Connect

```
FOH Mixing Console
    │
    ├── Main L/R Out ──→ PA System (as normal)
    │
    └── Aux Send / Matrix Out / Direct Out
            │
            ▼
        Audio Interface (USB)
            │
            ▼
        Streaming PC (OBS/vMix)
```

### Connection Options

| Console Output | Cable | Interface Input | Notes |
|---------------|-------|-----------------|-------|
| XLR Main/Aux out | XLR cable | XLR input on interface | Best quality, balanced signal |
| TRS 1/4" out | TRS cable | TRS input on interface | Good quality, balanced |
| RCA out | RCA to TRS adapter | TRS input | Consumer-level, unbalanced |
| 3.5mm out | 3.5mm to TRS | TRS input | Last resort only |

### Pros and Cons

**Pros:** Simple, uses existing venue audio setup, no additional mixing needed.

**Cons:** The FOH mix is designed for the room, not for headphones/speakers at home. Common issues:
- **Bass is too heavy** — PA subs compensate for room acoustics; stream listeners hear overwhelming low end
- **Vocals may be quiet** — in a live venue, vocals cut through partly via the acoustic stage volume, which the stream doesn't capture
- **No audience/room sound** — the direct feed is dry studio audio with zero ambiance

## Method 2: Dedicated Stream Mix (Aux/Bus Send) — Recommended

The gold standard: the FOH engineer sends a separate mix optimized for the stream via an auxiliary bus.

### How It Works

```
FOH Mixing Console
    │
    ├── Main L/R Out ──→ PA System
    │
    └── Aux Bus 7/8 (Stream Mix)
            │
            ▼
        Audio Interface
            │
            ▼
        Streaming PC
```

The FOH engineer (or a dedicated stream audio engineer) controls the aux send levels independently, creating a mix that sounds great on headphones and home speakers.

### Stream Mix Adjustments vs. FOH Mix

| Element | FOH Mix (PA) | Stream Mix (Aux) |
|---------|-------------|-----------------|
| Kick drum | Boosted for room impact | Pulled back 3-6 dB |
| Bass guitar | Prominent | Slightly reduced |
| Vocals | Moderate (room carries acoustics) | Pushed up 2-4 dB |
| Acoustic guitar | Often buried | Brought up for clarity |
| Room/ambient mic | Not used | Blended in 10-20% for liveness |
| Reverb/effects | Designed for room | Slightly more reverb for depth |
| Overall dynamic range | Wide (PA can handle it) | Compressed for consistent levels |

### Required: An Ambient/Room Mic

Add 1-2 condenser microphones in the audience area to capture:
- Crowd noise, applause, cheering
- Natural room reverb and ambiance
- The "you are here" feeling

**Recommended room mic setups:**
- **1x shotgun mic** at FOH position pointed at stage — simple and effective
- **2x small diaphragm condensers** in X/Y or ORTF pattern at FOH — stereo room image
- **Boundary mic on the stage lip** — picks up audience and stage ambiance

Blend the room mic(s) into the stream mix at 10-30% depending on the energy of the event.

## Method 3: Audio Splitter + Dedicated Stream Mixer

For maximum control, split all microphone signals and run a completely independent mix for the stream.

### How It Works

```
Stage Mics
    │
    ▼
Audio Splitter (passive or active)
    │
    ├── Split 1 ──→ FOH Console ──→ PA System
    │
    └── Split 2 ──→ Stream Console ──→ Audio Interface ──→ Streaming PC
```

### When This Makes Sense

- Large productions where FOH engineer can't manage a stream mix simultaneously
- Events where stream audio must be mixed by a separate engineer
- Situations where you need full multitrack recording of all channels for post-production

### Equipment

| Device | Purpose | Est. Cost |
|--------|---------|-----------|
| Passive splitter (16-ch) | Split mic signals without power | $500-1,500 |
| Active splitter (16-ch) | Split with signal isolation/boost | $1,500-4,000 |
| Small digital mixer (Behringer X32 Rack, Allen & Heath dLive) | Dedicated stream mixing | $1,500-5,000 |
| Dante/AES67 network | Digital audio transport | Varies |

## Audio Interfaces for Streaming

| Interface | Inputs | Outputs | Features | Price | Best For |
|-----------|--------|---------|----------|-------|----------|
| **Focusrite Scarlett 2i2** | 2x XLR/TRS | 2 | USB-C, low latency | $170 | Stereo FOH feed |
| **Focusrite Scarlett 4i4** | 2x XLR + 2x TRS | 4 | USB-C, MIDI | $230 | Stereo + room mics |
| **Behringer UMC404HD** | 4x XLR/TRS | 4 | USB, MIDAS preamps | $150 | Budget multi-input |
| **MOTU M4** | 2x XLR + 2x TRS | 4 | USB-C, excellent metering | $250 | Quality stereo + room |
| **Focusrite Scarlett 18i20** | 8x XLR + ADAT | 10 | USB-C, ADAT expansion | $500 | Multi-source mixing |
| **RME Babyface Pro FS** | 2x XLR + 2x TRS | 4 | USB, broadcast-grade quality | $800 | Professional reliability |

### Dante and AoIP (Audio over IP)

Modern venues increasingly use networked audio (Dante, AES67, Ravenna):
- **Dante Via** software can route Dante audio directly to your streaming PC
- **Dante AVIO adapters** convert Dante to analog/AES3 for your audio interface
- **Focusrite RedNet** series are Dante-native audio interfaces designed for broadcast

Advantage: a single Ethernet cable carries dozens of audio channels from anywhere in the venue to your streaming station.

## Stream Audio Processing

### Essential Processing Chain

Apply this processing to your stream audio output:

```
Raw Mix Input
    │
    ▼
1. High-Pass Filter (80-100 Hz) — Remove rumble and sub noise
    │
    ▼
2. Multiband Compressor — Tame low-end and control dynamics
    │
    ▼
3. Broadcast Limiter (-1 dBFS ceiling) — Prevent clipping
    │
    ▼
4. Loudness Normalization (target: -14 to -16 LUFS) — Consistent perceived volume
    │
    ▼
Stream Output
```

### Loudness Targets

| Platform | Target Loudness | True Peak Max |
|----------|----------------|---------------|
| YouTube | -14 LUFS | -1 dBTP |
| Twitch | -14 LUFS | -1 dBTP |
| Facebook | -16 LUFS | -1 dBTP |
| General web | -14 to -16 LUFS | -1 dBTP |

### Software Tools for Stream Audio Processing

- **OBS built-in filters:** Compressor, Limiter, Gain — basic but functional
- **Reaper ReaPlugs (free VST):** ReaComp, ReaEQ — lightweight and effective
- **Waves plugins:** MaxxVolume, L2 Limiter — broadcast standard
- **iZotope Ozone Elements:** All-in-one mastering chain
- **TDR Nova (free):** Dynamic EQ, excellent for stream audio

## Audio Monitoring

### What to Monitor

The stream audio engineer (or director) should monitor:

1. **The program audio output** (what viewers hear) via headphones
2. **Meters in OBS/vMix** — watch for peaking (should average -12 to -6 dBFS, peak no higher than -1 dBFS)
3. **The live platform** — check the actual stream playback (with a ~10-30 second delay) for end-to-end verification

### Monitoring Equipment

- **Closed-back headphones** (Audio-Technica ATH-M50x, Sony MDR-7506) — isolate from room noise
- **Headphone amp** if monitoring from a long cable run
- **Metering plugin** with LUFS display in your streaming software

## Common Audio Problems and Solutions

| Problem | Cause | Solution |
|---------|-------|---------|
| Distortion/clipping | Signal too hot from FOH | Pad the output or reduce gain at interface |
| Tinny / no bass | Using a 3.5mm or unbalanced connection | Switch to XLR balanced connection |
| Buzz / hum | Ground loop between FOH and streaming PC | Use a DI box or ground lift adapter |
| Echo / feedback | Room mic picking up PA | Reduce room mic level, use cardioid pattern pointed away from speakers |
| Audio/video out of sync | Different processing latency | Adjust audio sync offset in OBS/vMix (usually delay audio 20-80ms) |
| Inconsistent volume | No compression/limiting on stream output | Add a limiter and compressor to stream audio chain |
| Dead silence when band stops | No room mic | Add ambient microphone for continuous atmosphere |

## Related Guides

- [Hardware Starter Kits](../02-hardware-equipment/starter-kits.md) — Audio interfaces included in each kit
- [OBS Guide](../03-software/obs-guide.md) — Audio filter setup in OBS
- [Network & Bandwidth](../04-network-bandwidth/requirements.md) — Audio bitrate considerations
