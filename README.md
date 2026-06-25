<div align="center">

<!--
  ╔══════════════════════════════════════════════════════════════╗
  ║  BANNER IMAGE                                                ║
  ║  Place your banner image in: Media/Photos/                  ║
  ║  Recommended: 1200 × 400px — a CAD render or team photo     ║
  ║  Replace the src URL below with your actual image path      ║
  ╚══════════════════════════════════════════════════════════════╝
-->
<img src="https://github.com/MatthewsDS/Medical-drone-delivery-Project-/blob/main/Media/Photos/IMG_2022.jpeg"
     alt="Project AeroMed Banner" width="65%"/>

<br/><br/>

# 🚁 Project AeroMed
### Autonomous Biomedical Delivery Drone

*Bridging computer vision, aerospace engineering, and biomedical science*
*to deliver life-saving supplies where it matters most.*

<br/>

![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen?style=for-the-badge&logo=githubactions&logoColor=white)
![Team](https://img.shields.io/badge/Team-5%20Engineers-blueviolet?style=for-the-badge&logoColor=white)
![Phase](https://img.shields.io/badge/Current%20Phase-1%20%E2%80%93%20Learning%20%26%20Simulation-orange?style=for-the-badge)

<br/>

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)
![ArduPilot](https://img.shields.io/badge/ArduPilot-FF0000?style=for-the-badge&logo=arduino&logoColor=white)
![RaspberryPi](https://img.shields.io/badge/Raspberry%20Pi-A22846?style=for-the-badge&logo=raspberrypi&logoColor=white)
![Fusion360](https://img.shields.io/badge/Fusion%20360-F05A28?style=for-the-badge&logo=autodesk&logoColor=white)
![KiCad](https://img.shields.io/badge/KiCad-314CB0?style=for-the-badge&logoColor=white)

</div>

---

## 📖 Table of Contents

- [Mission Statement](#-mission-statement)
- [What We're Delivering](#-what-were-delivering)
- [Engineering Pillars](#-engineering-pillars)
- [The Team](#-the-team)
- [Technology Stack](#-technology-stack)
- [Roadmap](#-roadmap--timeline)
- [Repository Structure](#-repository-structure)
- [Getting Started](#-getting-started)

---

## 🎯 Mission Statement

> **"Time is the enemy in a medical emergency. Distance should not be."**

Project AeroMed is a full-scope engineering project built by five post-A-Level STEM students. We are designing, simulating, and physically constructing an **autonomous hexacopter** capable of navigating via GPS and computer vision to deliver temperature-sensitive, life-critical medical payloads to locations traditional logistics cannot reach in time.

<!--
  ╔══════════════════════════════════════════════════════════════╗
  ║  CONCEPT IMAGE — goes here, directly under mission statement ║
  ║  Suggested: your initial concept sketch, mood board,        ║
  ║  or first Fusion 360 render                                 ║
  ║  Recommended size: 900 × 500px                              ║
  ║  Upload to: Media/Renders/ or Media/Sketches/               ║
  ╚══════════════════════════════════════════════════════════════╝
-->
<div align="center">
  <img src="YOUR_CONCEPT_SKETCH_OR_RENDER_URL_HERE" alt="AeroMed Concept Sketch or CAD Render" width="70%"/>
  <br/>
  <sub><i>Initial concept sketch / early CAD render — replace this URL with your image path</i></sub>
</div>

---

## 💊 What We're Delivering

The payload bay is engineered to safely transport critical emergency medications. Each medicine has strict handling requirements — selecting a payload automatically reconfigures the bay's thermal environment to the correct conditions.

| Medication | Use Case | Temperature | Key Handling Requirement |
|:---:|:---|:---:|:---|
| 💉 **EpiPen / Adrenaline** | Anaphylactic shock | 15–25°C | Impact-sensitive; do not freeze |
| 🩹 **Naloxone** | Opioid overdose reversal | 15–25°C | Speed of delivery critical |
| 🐍 **Anti-Venom** | Venomous bites & stings | 2–8°C | Refrigerated; vibration-sensitive |
| 🩺 **Oxytocin** | Postpartum haemorrhage | 2–8°C | Cold chain essential; light-sensitive |
| 🩸 **Tranexamic Acid (TXA)** | Trauma bleeding control | 15–25°C | Highly stable; time-critical use |

> Cold chain medicines (Anti-Venom, Oxytocin) use active Peltier cooling. Room-temperature medicines use insulation and continuous monitoring. Payload selection triggers an interrupt-driven thermal state machine on the Raspberry Pi.

---

## ⚙️ Engineering Pillars

<table>
<tr>
<td width="50%" valign="top">

### 📐 6-DoF Kinematics & Mathematics
Transforming localised camera coordinate frames into global navigation waypoints using rotation matrices, quaternions, and rigid body dynamics.

**Topics:** Euler angles · Quaternions · Newton-Euler equations · NED frames

</td>
<td width="50%" valign="top">

### 👁️ Computer Vision
OpenCV and YOLO-based real-time target detection for precision landing zone identification and autonomous target acquisition during flight.

**Tools:** OpenCV · YOLO · ArUco markers · CNNs

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 🧬 Biomedical Payload Engineering
Designing an insulated, vibration-dampened payload bay that maintains strict thermal conditions (2–8°C cold chain where required) with real-time monitoring throughout transit.

**Topics:** Peltier modules · Thermodynamic isolation · Vibration dampening · KiCad PCB

</td>
<td width="50%" valign="top">

### 🔌 Systems Integration
Merging hardware flight controllers (Cube Orange+) with onboard edge computing (Raspberry Pi 5) via MAVLink for real-time autonomous decision making and safe failsafes.

**Tools:** MAVLink · ArduPilot · DroneKit-Python · SITL

</td>
</tr>
</table>

---

## 👥 The Team

<!--
  ╔══════════════════════════════════════════════════════════════╗
  ║  TEAM PHOTO — goes here, above the team table               ║
  ║  Even a casual group photo works well                       ║
  ║  Recommended size: 900 × 400px                              ║
  ║  Upload to: Media/Photos/                                   ║
  ╚══════════════════════════════════════════════════════════════╝
-->
<div align="center">
  <img src="YOUR_TEAM_PHOTO_URL_HERE" alt="The AeroMed Team" width="70%"/>
  <br/>
  <sub><i>The AeroMed team — replace this URL with your team photo path</i></sub>
</div>

<br/>

| Member | Role | Primary Responsibilities |
|:---|:---|:---|
| **Matthews** | Project Lead & Systems Engineer | Project management, SITL simulation, kinematics modelling, DroneKit mission scripting |
| **Jean-Paul** | Lead Programmer & CV Specialist | Computer vision (OpenCV, YOLO, CNNs), ArduPilot/MAVLink integration, autonomous targeting |
| **Malick** | Maths & Hardware Lead | Coordinate frame transforms, 6-DoF dynamics, Fusion 360 CAD, power distribution |
| **David** | Biochem & Payload Engineer | Thermodynamic isolation, cold chain compliance, payload bay design, KiCad PCB |
| **Mustafa** | Biochem & Payload Engineer | Protein/enzyme degradation research, vibration impact analysis, payload bay testing, regulations |

---

## 🛠️ Technology Stack
┌─────────────────────────────────────────────────────────────────┐

│                       SOFTWARE LAYER                            │

│   Python 3.x  ·  OpenCV  ·  DroneKit  ·  MAVLink  ·  YOLO     │

├─────────────────────────────────────────────────────────────────┤

│                     SIMULATION LAYER                            │

│          ArduPilot SITL          ·        Fusion 360 CAD        │

├─────────────────────────────────────────────────────────────────┤

│                      HARDWARE LAYER                             │

│   Raspberry Pi 5  ·  Cube Orange+  ·  6× T-Motor  ·  BLHeli32 │

│     Here3 GPS  ·  TF-Luna LiDAR  ·  Peltier TEC  ·  Custom PCB │

└─────────────────────────────────────────────────────────────────┘

| Tool | Purpose |
|:---|:---|
| Python 3.x | All flight logic, computer vision, and thermal control |
| ArduPilot / ArduCopter | Firmware for low-level flight stabilisation, failsafes, GPS navigation |
| ArduPilot SITL | Software-in-the-Loop simulator — fly a virtual drone with no hardware |
| DroneKit-Python | Autonomous mission scripting via MAVLink |
| OpenCV + YOLO | Real-time object detection, ArUco marker tracking, precision landing |
| Fusion 360 | CAD for frame, payload bay, mounts — exports STL for 3D printing |
| KiCad | PCB design for thermal control circuit — exports Gerber for JLCPCB |
| Raspberry Pi 5 (8GB) | Onboard computer running all Python code |
| Cube Orange+ | Flight controller with redundant IMUs and reliable GPS |

---

## 📅 Roadmap & Timeline
     Jul 2026           Nov 2026            Mar 2027        Jun 2027
        │                  │                   │               │
────────────┼──────────────────┼───────────────────┼───────────────┼────

│                  │                   │               │

┌─────────────────────────────────────┐           │               │

│   PHASE 1 · Learning & Simulation   │           │               │

│  SITL · OpenCV · CAD · Thermal spec │           │               │

└─────────────────────────────────────┘           │               │

│                   │               │

┌──────────────────────────────────────────────┤

│     PHASE 2 · Hardware & Build               │

│  Assembly · PID tuning · CV integration ·    │

│  Payload testing · Autonomous flight         │

└──────────────────────────────────────────────┘

### 🖥️ Phase 1 — Learning & Simulation *(July – October/November 2026)*

The summer window is the highest-productivity period. Learning and building in simulation happen simultaneously — topics the build never requires are skipped.

- Environment setup: Python, VS Code, Git, ArduPilot SITL, Fusion 360
- SITL autonomous mission scripting with DroneKit
- OpenCV target detection tested on webcam feeds
- Fusion 360 hexacopter frame and payload bay CAD design
- Breadboard Peltier thermal circuit with DS18B20 / BME280 sensors
- Payload biochemistry research and thermal specification per medicine
- Custom PCB designed in KiCad, ordered from JLCPCB

### 🔧 Phase 2 — Hardware & Build *(December 2026 – June 2027)*

- Hardware procurement (Cube Orange+, T-Motors, ESCs, Pi 5, LiPo batteries, LiDAR, Peltier modules)
- Frame assembly and Cube Orange+ configuration via Mission Planner
- Bench testing all electronics and payload bay thermal regulation
- First flights, PID tuning, autonomous mission testing
- Computer vision integration and precision landing trials
- Flight data logs, quantitative results, and full documentation

<!--
  ╔══════════════════════════════════════════════════════════════╗
  ║  GANTT CHART IMAGE (optional) — goes here                   ║
  ║  Export your timeline / Gantt from Notion, Excel, or        ║
  ║  draw.io as a PNG and drop the link in below                ║
  ║  Upload to: Media/Diagrams/                                 ║
  ╚══════════════════════════════════════════════════════════════╝
-->

---

## 📁 Repository Structure
AeroMed/

│

├── 📂 01_learning_and_simulation/         # Phase 1 — all simulation and research

│   ├── 📂 biochemistry/                  # Thermal & vibration stability research

│   ├── 📂 maths_and_kinematics/          # 6-DoF modelling & matrix derivations

│   ├── 📂 coding_and_cv/                 # Python scripts & OpenCV experiments

│   ├── 📂 cad_designs/                   # Fusion 360 files (.F3D, .STL, .STEP)

│   ├── 📂 pcb_design/                    # KiCad schematics & Gerber exports

│   └── 📂 flight_simulations/            # SITL profiles & autonomous mission scripts

│

├── 📂 02_hardware_and_build/              # Phase 2 — physical hardware

│   ├── 📂 flight_controller/             # Cube Orange+ params & firmware configs

│   ├── 📂 payload_bay/                   # Thermal test data & Peltier control code

│   └── 📂 telemetry_logs/               # Real flight data for performance analysis

│

└── 📂 Media/                             # All photos, renders, and diagrams

├── 📂 Photos/                        # Team photos, build progress shots

├── 📂 Renders/                       # Fusion 360 CAD renders

├── 📂 Sketches/                      # Concept sketches

└── 📂 Diagrams/                      # System diagrams, Gantt charts

---

## 🚀 Getting Started

> ⚠️ *Full setup instructions will be added as the project advances through Phase 2.*

**Prerequisites:**
```bash
# Clone the repository
git clone https://github.com/MatthewsDS/Medical-drone-delivery-Project-.git
cd Medical-drone-delivery-Project-

# Install Python dependencies
pip install opencv-python dronekit pymavlink numpy geopy folium
```

**Running an ArduPilot SITL simulation (Phase 1):**
```bash
# Launch the SITL virtual drone
sim_vehicle.py -v ArduCopter --console --map

# Run an autonomous mission script
python 01_learning_and_simulation/flight_simulations/autonomous_mission.py
```

---

<!--
  ╔══════════════════════════════════════════════════════════════╗
  ║  FOOTER / LOGO IMAGE — goes here at the very bottom         ║
  ║  Your AeroMed logo, school badge, or a clean project icon   ║
  ║  Recommended: square image, displayed at 100–130px wide     ║
  ╚══════════════════════════════════════════════════════════════╝
-->
<div align="center">

<img src="https://github.com/MatthewsDS/Medical-drone-delivery-Project-/blob/main/Media/Photos/IMG_2023.jpeg"
     alt="AeroMed Logo" width="120px"/>

<br/><br/>

**Project AeroMed** · Post-A-Level STEM Engineering Project
*Built with purpose. Engineered for impact.*

<br/>

![GitHub last commit](https://img.shields.io/github/last-commit/MatthewsDS/Medical-drone-delivery-Project-?style=flat-square&color=brightgreen)
![GitHub repo size](https://img.shields.io/github/repo-size/MatthewsDS/Medical-drone-delivery-Project-?style=flat-square&color=blue)
![GitHub stars](https://img.shields.io/github/stars/MatthewsDS/Medical-drone-delivery-Project-?style=flat-square&color=yellow)

</div>
