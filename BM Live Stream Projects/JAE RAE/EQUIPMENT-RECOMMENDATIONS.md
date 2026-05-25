# JAE RAE — EQUIPMENT RECOMMENDATIONS

**Assessment date**: 05-18-2026  
**Setup date**: 06-19-2026  
**First live**: 06-24-2026 @ 8pm EST

---

## PTZ CAMERAS (3x) — NDI + HDMI + Bitfocus Companion

### Top Recommendation: PTZOptics Move 4K (PT20X-MOVE-4K)
- Native NDI, HDMI, USB, IP all in one unit
- 4K capable (streams 4K NDI natively)
- **Full Bitfocus Companion support** — module exists, well-maintained
- Works seamlessly in vMix via NDI
- ~$1,099–$1,299/unit
- Rock-solid reliability, widely used in live broadcast

### Strong Alternative: BirdDog P200 or P400
- BirdDog specializes in NDI — extremely clean signal
- Bitfocus Companion module available
- P400 does 4K NDI
- More expensive (~$1,500–$2,500) but premium build quality

### On OBSBOT (ObSbots)
The OBSBOT Tail Air is AI-tracked and looks great on paper, but:
- **No native NDI** — relies on Wi-Fi or USB, not a true NDI camera
- Bitfocus Companion support is limited/unofficial
- Not designed for multi-camera broadcast switcher workflows
- **Recommendation: Avoid for this setup.** PTZOptics or BirdDog are the professional choice for a vMix + NDI + Companion rig.

---

## DO YOU NEED A VIDEO SWITCHER (ATEM)?

**No — skip it.**

With NDI cameras feeding directly into vMix over the network, **vMix IS the switcher.** Adding an ATEM creates an unnecessary step and extra cost. The workflow is:

```
PTZ Cam 1 (NDI) ──┐
PTZ Cam 2 (NDI) ──┤──→ vMix (switches, overlays, encodes) ──→ Stream
PTZ Cam 3 (NDI) ──┘
RØDECaster (USB) ─┘
```

No ATEM needed. Save the budget.

---

## ENCODER OPTIONS

Since you're using vMix and providing your own connectivity (1 Gbps up), **vMix on a capable PC handles encoding natively.** You likely don't need a dedicated hardware encoder unless you want a separate streaming box for redundancy.

### Option A: vMix PC (Recommended)
- vMix encodes and streams directly to YouTube/Facebook/etc.
- Requires a strong Windows PC (see specs note below)
- Most flexible — no extra hardware
- vMix 4K license required for 4K output (~$1,200 one-time or subscription)

### Option B: Magewell Ultra Encode (Hardware, if you want dedicated box)
- ~$995
- Takes HDMI or SDI input, encodes to RTMP, SRT, or NDI
- Simple, reliable, set-and-forget
- Good if you want to offload encoding from the vMix PC

### Option C: YoloBox Ultra (Standalone, simple)
- ~$699
- Self-contained — built-in switcher, encoder, streamer
- Good as a **backup/redundancy box**, not primary if you're running full vMix
- Limited compared to vMix for complex productions

### Option D: Teradek Cube (Broadcast-grade)
- ~$1,500+
- Overkill for this setup given the great internet connection
- Reserve for on-location shoots with poor/bonded connectivity

**Bottom line**: Build around a solid vMix workstation as your encoder. Add a YoloBox Ultra as a backup if budget allows.

---

## OVERHEAD CAMERA

The overhead shot (card shuffling, ritual objects, tarot) is critical for this show. A PTZ is probably overkill overhead — you want it locked off at a fixed angle.

### Top Pick: Marshall Electronics CV370 (or CV503-U3)
- Compact block camera, HDMI out
- Clean image, built for broadcast mounting
- Easy to rig overhead; doesn't need to pan/tilt
- ~$500–$700
- Run HDMI → capture card into vMix

### Alternative: PTZOptics OTF Camera
- PTZOptics makes a dedicated overhead camera (OTF = "Over-The-Frame")
- NDI capable, purpose-built for card/table overhead shots
- ~$799
- Cleaner integration into NDI workflow

### Budget Alternative: GoPro Hero 13 Black + HDMI out
- 4K, wide field of view, compact, easy to rig
- HDMI output via USB-C adapter → capture card into vMix
- ~$399
- Less "broadcast" but works

---

## 4K STREAMING FEASIBILITY

**Yes — 4K is doable here.**

With 1 Gbps up, you have plenty of bandwidth. 4K streaming to YouTube typically requires 20–51 Mbps upload — you have 1,000 Mbps. No issue there.

Requirements to unlock 4K:
- PTZOptics Move 4K cameras (or BirdDog P400)
- **vMix 4K license** (not the standard license)
- PC capable of handling 4K NDI decode + encode simultaneously (GPU matters)
- YouTube / platform that accepts 4K RTMP input

**Recommend confirming the vMix license tier before shopping.**

---

## AUDIO — RØDECaster Pro II

Already on-site — great call. It's a USB audio interface, connects directly to the PC, and vMix picks it up as an audio input device. No extra audio gear needed for the primary stream. Optional additions:
- Boom arm for the host mic (if not already there)
- IEM monitoring if call-in guests are integrated via phone/IP

---

## TENTATIVE SHOPPING LIST SUMMARY

| Item | Model | Est. Cost | Notes |
|------|-------|-----------|-------|
## FINALIZED PURCHASE LIST — 05-20-2026
*Source: Equipment Resources - 05202026.xlsx*

| QTY | Item | Unit Price | Subtotal | Link |
|-----|------|------------|----------|------|
| 2 | 4K FoMako PTZ Cameras (K820N) | $999.00 | $1,998.00 | [Amazon](https://www.amazon.com/gp/product/B0BJNHLK7C) |
| 1 | TRENDnet 8-Port 2.5G PoE++ Switch (TPE-BG380) | $239.99 | $239.99 | [Amazon](https://www.amazon.com/gp/product/B0DBMWNMMM) |
| 1 | FoMaKo NDI PTZ Controller KC608N | $499.00 | $499.00 | [Amazon](https://www.amazon.com/gp/product/B0C9J6H6RF) |
| 3 | Ethernet Cable 7ft | $7.99 | $23.97 | [Amazon](https://www.amazon.com/gp/product/B08MTCNS9S) |
| 2 | Ethernet Cable 35ft | $13.49 | $26.98 | [Amazon](https://www.amazon.com/gp/product/B00B3UR496) |
| 1 | Monitor Holder | $8.99 | $8.99 | [Amazon](https://www.amazon.com/dp/B0BTDHQJ6X) |

**TOTAL: $2,796.93** *(taxes not included)*

Already owned/handled: vMix license, RØDECaster Pro II, Stream Deck

---

## STILL TBD — Not Yet Purchased

| Item | Est. Cost | Notes |
|------|-----------|-------|
| Overhead Camera (Marshall CV370) | ~$719 | NDI HX3, fixed mount above card/ritual table |
| PTZ Floor Stands x2 (Proaim) | ~$506 | $253/unit — for 2x FoMako K820N |
| C-Stand Overhead Shot Kit | ~$175 | For mounting overhead cam |

*YoloBox Ultra (backup encoder) — pulled for now. Revisit after first show.*

---

## CONNECTIVITY NOTES

With 1 Gbps / 1 Gbps at the location:
- NDI cameras need to be on the **same LAN** as the vMix PC — use a managed switch, not Wi-Fi
- Run CAT6 from switch to each camera on 06-19 setup day
- Keep the stream PC on a wired connection — no Wi-Fi for the primary machine
- Confirm router/modem port forwarding isn't needed for direct RTMP push (usually not)

---

## RECOMMENDED vMix PC SPECS (if not already owned)

For 3x 4K NDI cameras + streaming:
- CPU: Intel i9-13900K or AMD Ryzen 9 7900X
- RAM: 32GB DDR5
- GPU: NVIDIA RTX 4070 or better (for 4K encoding/NVENC)
- NVMe SSD: 1TB+
- OS: Windows 11
- Network: Built-in 2.5GbE or dedicated GbE NIC

---

*Last updated: 05-19-2026 — confirmed: vMix handled, Stream Deck on hand, 2x PTZ cams only*
