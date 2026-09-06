# Explodex ⚡️

> **Interactive 3D Exploded-View Studio & Deconstruction Laboratory for Everyday Gadgets, Mechanical Timepieces & Anatomy.**

Explodex is a high-performance, browser-native 3D deconstruction laboratory built with React, Three.js, and WebGL. Explore "How Things Work" from the inside out — disassemble everyday consumer electronics, inspect the micro-mechanics of high-complication horology with live ticking movements, and explore anatomical reference models with zero lag.

---

## 🌟 Featured Interactive Models

### 1. 🎧 AirPods Pro (2nd Generation)
- **13 modeled CAD components** and 12 functional sub-assemblies accurately drafted from official Apple Accessory Design Guidelines.
- **Acoustic Engineering**: Custom low-distortion high-excursion transducer (stiff composite dome + compliant roll-surround) and laser-perforated acoustic pressure-equalization vents.
- **Computational Audio Silicon**: Apple H2 SiP running real-time ANC and Adaptive Transparency algorithms at 48 kHz.
- **Sensors & Controls**: Inward-facing calibration microphone and indented capacitive force-sensor stem.

### 2. ⌚️ Luxury Mechanical Automatic Chronograph
- **19 micro-machined horological components**, 10 functional subsystems, and 11,226 triangles.
- **Active 8-Beat Seconds Sweep (28,800 VPH)**: Central racing red chronograph sweeper needle sweeps continuously across the dial at **8 beats per second** (480 crisp micro-steps per 60-second revolution).
- **Live Local Time**: Faceted Dauphine hour and minute hands advance in real local time ($H:M:S$).
- **Live 4 Hz Regulating Organ**:
  - **Glucydur Balance Wheel & Nivarox Hairspring**: Rapidly oscillates back and forth at **4 Hz** (±160° amplitude).
  - **Synthetic Ruby Pallet Lever**: Rocks between synthetic ruby banking pins 8 times per second.
  - **15-Tooth Club-Tooth Escape Wheel**: Steps forward with each balance impulse.
  - **6-Pillar Column-Wheel Chronograph Clutch**: Coordinates start, stop, and reset pusher levers.
  - **Heavy Tungsten Bidirectional Rotor**: Swings with realistic inertial pendulum physics.
- **Synthesized Swiss Escapement Web Audio**: Zero-latency synthesized escapement acoustics ("tic-tac-tic-tac") with dedicated mute/unmute toggle.
- **Sculpted 316L Stainless Steel Case**: Ergonomically downward-swept curved lugs, integrated bracelet end-links, knurled screw-down crown with crown guards, and dual pump pushers.

### 3. 🫀 Adult Male Human Anatomy (BodyParts3D)
- **2,234 individually selectable meshes** and **3,432 named anatomical concepts**.
- **15 anatomical systems**: Skeletal, muscular, cardiac, nervous, arterial, venous, respiratory, and more.

---

## 🚀 Key Technical Innovations

- **Dual-Row GPU DataTexture Pipeline**:
  - Merged single-draw-call geometry for thousands of components.
  - **Row 0** ($y = 0.25$): 3D explosion layout translation $(dx, dy, dz, \text{visible})$.
  - **Row 1** ($y = 0.75$): Local pivot transformation $(px, py, \theta_{\text{rad}}, \text{isAnimated})$ applied inside the vertex shader for zero-cost real-time animation.
- **Synchronized Raycast Pickers**:
  - Invisible picker matrices dynamically match vertex shader transforms to machine epsilon, allowing users to tap or click moving hands in motion to inspect engineering metadata.
- **Stationary Floor Turntable**:
  - Decoupled scene graph architecture where the floor turntable pedestal remains 100% stationary on the ground while the model rotates smoothly on top of it.
- **Synthesized Web Audio API Engine**:
  - Realistic synthetic ruby pallet stone impact audio synthesized at 4,400 Hz and 3,800 Hz with sharp exponential decay (tau = 5ms).
- **Non-Overlapping Exploded Layouts**:
  - Dynamic 2D bin-packing algorithm computes optimal spatial distribution at any desktop or mobile aspect ratio.

---

## 🛠️ Getting Started

### Prerequisites
- Node.js 22.13 or newer
- npm

### Installation & Local Run
```sh
git clone https://github.com/vinayanand3/explodex.git
cd explodex
npm install
npm run dev
```

Open [http://localhost:3016](http://localhost:3016) in your browser.

### Quality & Contract Verification
```sh
# Verify TypeScript strict typecheck (0 errors)
npm run check

# Verify spatial packing, non-overlapping layouts, search, and gestures
npx jiti scripts/validate-interactions.mjs

# Build production bundle
npm run build
```

---

## 🏗️ Model Generation Scripts

The repository includes parameterized Python builders that generate browser-ready binary geometry chunks (`.bin`) and metadata (`.json`):

```sh
# Generate luxury mechanical chronograph
python3 scripts/generate-chronograph.py

# Generate AirPods Pro deconstruction
python3 scripts/generate-airpods-pro.py
```

---

## 📄 License

Original application code and generative model scripts are released under the [MIT License](LICENSE).
Attribution for third-party reference data is detailed in [ATTRIBUTION.md](public/ATTRIBUTION.md).
