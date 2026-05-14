# Network & Bandwidth Requirements for Venue Streaming

## Bandwidth Fundamentals

### Upload Speed Requirements

Your internet **upload** speed determines the quality of your stream. Download speed is largely irrelevant for streaming.

| Stream Quality | Resolution | FPS | Bitrate | Minimum Upload Required |
|---------------|-----------|-----|---------|------------------------|
| Basic | 720p | 30 | 2,500 kbps | 5 Mbps |
| Standard | 1080p | 30 | 4,500 kbps | 10 Mbps |
| High Quality | 1080p | 60 | 6,000 kbps | 12 Mbps |
| Premium | 1080p | 60 | 8,000 kbps | 15 Mbps |
| 4K | 2160p | 30 | 15,000 kbps | 25 Mbps |
| 4K High | 2160p | 60 | 20,000 kbps | 35 Mbps |

**Rule of thumb:** Your upload speed should be **at least 2x** your stream bitrate to account for overhead, spikes, and other network traffic. If streaming at 6,000 kbps, aim for 12+ Mbps upload.

### Multi-Destination Multiplier

If you're streaming to multiple platforms simultaneously:

```
Total bandwidth = stream bitrate x number of destinations (if direct)
Total bandwidth = stream bitrate x 1 (if using Restream or relay service)
```

Using a relay service like Restream means you only send one stream out. The relay handles distribution.

## Internet Connection Types

| Connection | Typical Upload | Reliability | Latency | Best For |
|-----------|---------------|-------------|---------|----------|
| **Dedicated fiber** | 100-1000 Mbps | Excellent | <5ms | Professional venues |
| **Business fiber** | 50-500 Mbps | Very good | <10ms | Regular streaming venues |
| **Business cable** | 10-50 Mbps | Good | 10-30ms | Occasional streaming |
| **Residential fiber** | 50-500 Mbps | Good | <10ms | Small venues |
| **Residential cable** | 5-20 Mbps | Fair | 15-40ms | Budget/backup only |
| **5G cellular** | 10-50 Mbps | Variable | 20-50ms | Outdoor/backup |
| **4G LTE** | 5-15 Mbps | Variable | 30-70ms | Emergency backup |
| **Bonded cellular** | 10-50 Mbps (combined) | Good | 30-70ms | Remote venues |
| **Starlink** | 10-40 Mbps up | Variable | 25-60ms | Rural/remote venues |

### Recommendations by Venue Type

- **Permanent venue streaming weekly:** Dedicated or business fiber — minimum 50 Mbps symmetrical
- **Occasional events at a venue:** Business cable with cellular backup
- **Outdoor / remote events:** Bonded cellular (LiveU, Teradek) + Starlink as backup
- **Mission-critical broadcast:** Dual fiber paths from different ISPs

## On-Site Network Architecture

### Dedicated Streaming Network

**Critical: Never share the general venue Wi-Fi or public network with your streaming equipment.**

Recommended network layout:

```
ISP Fiber Connection
    │
    ▼
Router / Firewall
    │
    ├── VLAN 1: Streaming (isolated, QoS priority)
    │     │
    │     ├── Streaming PC / Encoder
    │     ├── NDI Cameras (if using NDI)
    │     └── PTZ Controller
    │
    ├── VLAN 2: Venue Operations (POS, ticketing, etc.)
    │
    └── VLAN 3: Public Wi-Fi (guest network)
```

### Network Hardware

| Device | Purpose | Recommended Models | Est. Cost |
|--------|---------|-------------------|-----------|
| **Managed switch** | VLAN separation, QoS, Gigabit for NDI | Netgear M4250, Ubiquiti Pro 24 | $300-600 |
| **Router/Firewall** | Traffic management, dual WAN | Ubiquiti Dream Machine Pro, pfSense | $300-500 |
| **PoE Switch** | Power NDI/PTZ cameras via Ethernet | Netgear M4250-26G4F-PoE+ | $500-800 |

### NDI Network Requirements

NDI video runs on your local network, not the internet. It requires significant LAN bandwidth:

| NDI Mode | Bandwidth per Stream | Network Requirement |
|----------|---------------------|-------------------|
| NDI Full (1080p60) | ~120-150 Mbps | Gigabit Ethernet minimum |
| NDI Full (4K30) | ~250-300 Mbps | Gigabit Ethernet |
| NDI HX3 (1080p60) | ~20-40 Mbps | Gigabit Ethernet |
| NDI HX3 (4K30) | ~40-80 Mbps | Gigabit Ethernet |

**For NDI workflows:**
- Use **Gigabit Ethernet** for all NDI devices — Wi-Fi is not reliable enough
- Enable **Jumbo Frames (MTU 9000)** on all switches and devices in the NDI path
- Use a **dedicated VLAN** for NDI traffic to prevent congestion
- **Cat6 or Cat6a** cabling recommended (Cat5e works for Gigabit but has less headroom)

## QoS (Quality of Service) Configuration

Configure your managed switch and router to prioritize streaming traffic:

### Priority Order

1. **Highest:** RTMP/SRT outbound streaming traffic (port 1935 / custom SRT port)
2. **High:** NDI traffic on local network (mDNS + high-port video data)
3. **Medium:** PTZ camera control traffic
4. **Low:** General venue operations
5. **Lowest:** Public guest Wi-Fi

### DSCP Markings

If your network equipment supports DSCP:
- Streaming output: `EF` (Expedited Forwarding) — DSCP 46
- NDI video: `AF41` — DSCP 34
- Control traffic: `AF21` — DSCP 18
- Default traffic: `BE` (Best Effort) — DSCP 0

## Redundancy and Failover

### Backup Internet Strategies

| Strategy | Cost | Complexity | Failover Time |
|----------|------|-----------|---------------|
| **Dual ISP with auto-failover** | High | Moderate | 5-30 seconds |
| **Cellular bonding (LiveU/Teradek)** | Moderate | Low | Automatic |
| **Starlink as backup** | Low | Low | Manual switch |
| **Mobile hotspot standby** | Low | Low | Manual switch |

### Dual-Path Streaming

For critical events, send your stream via two paths simultaneously:
1. Primary: Wired fiber connection
2. Backup: Cellular bonding device

Both feed into a cloud relay (Restream, or your own NGINX server) that selects the best path to the platform.

## Testing Your Connection

### Before Every Event

1. **Speed test:** Run [speedtest.net](https://www.speedtest.net) or `speedtest-cli` from the streaming machine
2. **Stability test:** Stream to a private/unlisted YouTube stream for 30+ minutes and check for dropped frames
3. **Bandwidth reservation:** Ensure no large downloads, updates, or backups are scheduled during the event
4. **Firewall check:** Verify outbound ports 1935 (RTMP) and your SRT port are open

### Speed Test Checklist

- [ ] Upload speed is 2x+ your target bitrate
- [ ] Ping/latency is under 50ms to your streaming platform's ingest server
- [ ] Jitter is under 10ms
- [ ] No packet loss over a 5-minute test
- [ ] Speed is consistent across multiple tests (not just peak)

## Common Network Problems and Fixes

| Problem | Symptom | Fix |
|---------|---------|-----|
| Shared bandwidth | Intermittent dropped frames | Isolate streaming on dedicated VLAN with QoS |
| Wi-Fi streaming | Unreliable, variable quality | Always use wired Ethernet for streaming |
| ISP throttling | Speed degrades during events | Upgrade to business-class with SLA |
| DNS issues | Stream fails to connect | Use static DNS (8.8.8.8, 1.1.1.1) on streaming device |
| MTU mismatch | NDI stuttering | Enable Jumbo Frames on all NDI network devices |
| Windows Update | Bandwidth spike mid-stream | Set streaming PC to metered connection, defer updates |

## Related Guides

- [Encoders & Switchers](../02-hardware-equipment/encoders-switchers.md) — Encoding hardware with SRT/cellular bonding
- [Software Overview](../03-software/overview.md) — Encoding settings and protocol options
- [Starter Kits](../02-hardware-equipment/starter-kits.md) — Bandwidth requirements per kit level
