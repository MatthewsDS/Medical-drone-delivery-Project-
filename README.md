<div align="center">

<!-- ═══════════════════════════════════════════════════════════════ -->
<!--  PROJECT BANNER IMAGE                                          -->
<!--  👉 Replace the URL below with your own banner image.         -->
<!--     Recommended size: 1200 × 400px                            -->
<!--     Tools: Canva, Figma, or a screenshot of your CAD model    -->
<!-- ═══════════════════════════════════════════════════════════════ -->
<img src="https://github.com/MatthewsDS/Medical-drone-delivery-Project-/blob/main/Media/Photos/IMG_2022.jpeg" alt="Project AeroMed Banner" width="60%" length="40%"/>

<br/>

# 🚁 Project AeroMed
### Autonomous Biomedical Delivery Drone

*Bridging computer vision, aerospace engineering, and biomedical science*  
*to deliver life-saving supplies where it matters most.*

<br/>

<!-- Status & Target Badges -->
![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen?style=for-the-badge&logo=githubactions&logoColor=white)
![Team](https://img.shields.io/badge/Team-5%20Engineers-blueviolet?style=for-the-badge&logo=people&logoColor=white)
![Phase](https://img.shields.io/badge/Current%20Phase-1%20%E2%80%93%20Research-orange?style=for-the-badge)

<!-- Language Badges -->
<br/>

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![C++](https://img.shields.io/badge/C++-00599C?style=for-the-badge&logo=cplusplus&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)
![ArduPilot](https://img.shields.io/badge/ArduPilot-FF0000?style=for-the-badge&logo=arduino&logoColor=white)
![RaspberryPi](https://img.shields.io/badge/Raspberry%20Pi-A22846?style=for-the-badge&logo=raspberrypi&logoColor=white)
![Fusion360](https://img.shields.io/badge/Fusion%20360-F05A28?style=for-the-badge&logo=autodesk&logoColor=white)

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

> **Time is the enemy in a medical emergency. Distance shouldn't be.**

Project AeroMed is an industry-grade engineering project built by five Year 12/13 STEM students. We are designing, simulating, and physically constructing an **autonomous quadcopter** capable of navigating via computer vision to deliver temperature-sensitive, life-critical medical payloads to locations traditional logistics cannot reach in time.

<!-- ═══════════════════════════════════════════════════════════════ -->
<!--  CONCEPT PHOTO / SKETCH                                        -->
<!--  👉 Insert an image of your initial concept sketch, CAD       -->
<!--     render, or inspiration board here.                        -->
<!--     Recommended size: 900 × 500px                             -->
<!-- ═══════════════════════════════════════════════════════════════ -->
<div align="center">
  <img src="YOUR_CONCEPT_IMAGE_URL_HERE" alt="Drone Concept Sketch or CAD Render" width="75%"/>
  <br/>
  <sub><i>👆 Replace this with your concept sketch, CAD render, or mood board</i></sub>
</div>

---

## 💊 What We're Delivering

The payload bay is engineered to safely transport critical emergency medications, each with strict handling requirements:

| Medication | Use Case | Key Handling Requirement |
|:---:|:---|:---|
| 💉 **EpiPen / Adrenaline** | Anaphylactic shock | Temperature-stable; impact-sensitive |
| 🩹 **Naloxone** | Opioid overdose reversal | Stable; speed of delivery critical |
| 🐍 **Anti-Venom** | Venomous bites & stings | Refrigerated; vibration-sensitive |
| 🩺 **Oxytocin** | Postpartum haemorrhage | Cold chain (2–8°C); light-sensitive |
| 🩸 **Tranexamic Acid** | Trauma bleeding control | Stable; time-critical administration |

---

## ⚙️ Engineering Pillars

<table>
<tr>
<td width="50%" valign="top">

### 📐 6-DoF Kinematics & Mathematics
Transforming localised camera coordinate frames into global navigation waypoints using rotation matrices, quaternions, and rigid body dynamics.

**Key topics:** Euler angles · Homogeneous transforms · Newton-Euler equations

</td>
<td width="50%" valign="top">

### 👁️ Computer Vision (CV)
OpenCV-based real-time target detection for precision landing zone identification and dynamic obstacle avoidance during autonomous flight.

**Key tools:** OpenCV · ArUco markers · YOLO inference

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 🧬 Biomedical Engineering
Designing an insulated, vibration-dampened payload bay that maintains strict thermal conditions (2–8°C cold chain where required) throughout transit.

**Key topics:** Thermodynamic isolation · Peltier modules · Vibration dampening

</td>
<td width="50%" valign="top">

### 🔌 Systems Integration
Merging hardware flight controllers (Pixhawk) with onboard edge computing (Raspberry Pi) via MAVLink protocol for real-time autonomous decision making.

**Key tools:** MAVLink · ArduPilot · DroneKit-Python

</td>
</tr>
</table>

---

## 👥 The Team

<!-- ═══════════════════════════════════════════════════════════════ -->
<!--  TEAM PHOTO                                                    -->
<!--  👉 Add a team photo here — even a casual one works great!    -->
<!--     Recommended size: 900 × 400px                             -->
<!-- ═══════════════════════════════════════════════════════════════ -->
<div align="center">
  <img src="YOUR_TEAM_PHOTO_URL_HERE" alt="The AeroMed Team" width="70%"/>
  <br/>
  <sub><i>👆 Replace with a team photo</i></sub>
</div>

<br/>

| Member | Role | Responsibilities |
|:---|:---|:---|
| **Jean-Paul** | Lead Programmer & CV Specialist | Computer vision algorithms, ArduPilot/MAVLink integration, OpenCV targeting scripts |
| **Malick** | Maths & Hardware Lead | Coordinate frame transforms, 6-DoF dynamics, CAD chassis design, power distribution |
| **Matthews** | Systems & Repo Administrator | Architecture integration, Git version control, HITL simulation, kinematics modelling |
| **David** | Biochem & Payload Engineer | Thermodynamic isolation, biochemical stability research, cold chain monitoring |
| **Mustafa** | Biochem & Payload Engineer | Enzyme/protein degradation research, vibration impact analysis, payload bay testing |

---

## 🛠️ Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    SOFTWARE LAYER                           │
│  Python 3.x  │  C++  │  OpenCV  │  DroneKit  │  MAVLink   │
├─────────────────────────────────────────────────────────────┤
│                    SIMULATION LAYER                         │
│       ArduPilot SITL       │       Fusion 360 CAD          │
├─────────────────────────────────────────────────────────────┤
│                    HARDWARE LAYER                           │
│  Raspberry Pi  │  Pixhawk FC  │  ESCs  │  BLDC Motors      │
│         GPS Module  │  Barometric Sensor  │  LiDAR          │
└─────────────────────────────────────────────────────────────┘
```

---

## 📅 Roadmap & Timeline

```
MONTH   1       2       3       4       5       6       7
        ├───────────────────┤
PHASE 1 │  Research & Learn │
        └───────────────────┤───────────┤
PHASE 2                     │  Sim & CAD│
                            └───────────┤───────────┤
PHASE 3                                 │  Hardware │
                                        └───────────┘
```

### 🔬 Phase 1 — Research & Learning *(Months 1–3)*
- Deep dive into university-level kinematics papers and OpenCV documentation
- Establish mathematical models for rotation matrices and drone translation
- Initial biochemistry research into enzyme/protein degradation under vibration and thermal stress

### 🖥️ Phase 2 — Simulation & CAD *(Months 4–5)*
- Develop and test OpenCV target-tracking scripts using PC webcams
- Model the physical drone chassis and payload bay in **Fusion 360**
- Run **Software-in-the-Loop (SITL)** flight simulations via ArduPilot

### 🔧 Phase 3 — Hardware & Flight Trials *(Months 6–7)*
- Procurement and physical assembly: frame, ESCs, motors, flight controller
- Bench-test payload container thermal regulation and vibration dampening
- Real-world autonomous flight testing, telemetry log analysis, and iteration

<!-- ═══════════════════════════════════════════════════════════════ -->
<!--  ROADMAP / GANTT CHART IMAGE (OPTIONAL)                       -->
<!--  👉 Export your Gantt chart or timeline as an image and       -->
<!--     paste the URL here for a visual project overview.         -->
<!-- ═══════════════════════════════════════════════════════════════ -->

---

## 📁 Repository Structure

```
AeroMed/
│
├── 📂 01_learning_phase/              # Research, maths, and core notes
│   ├── 📂 biochemistry/              # Thermal & vibration stability research
│   ├── 📂 maths_and_kinematics/      # 6-DoF modelling & matrix derivations
│   └── 📂 coding_and_cv/             # Early Python & OpenCV tutorials
│
├── 📂 02_simulation_and_cad/          # Digital design & simulation environment
│   ├── 📂 opencv_testing/            # Target detection scripts (webcam-tested)
│   ├── 📂 cad_designs/               # 3D model files (.STL, .STEP, .F3D)
│   └── 📂 flight_simulations/        # SITL profiles & autonomous mission scripts
│
└── 📂 03_hardware_and_flight/         # Real-world deployment
    ├── 📂 flight_controller/         # Pixhawk params & firmware configs
    └── 📂 telemetry_logs/            # Real flight data for performance analysis
```

---

## 🚀 Getting Started

> ⚠️ *This section will be fully populated as the project advances through Phase 2/3.*

**Prerequisites (Phase 2 onwards):**
```bash
# Python dependencies
pip install opencv-python dronekit pymavlink numpy

# Clone the repository
git clone https://github.com/MatthewsDS/Medical-drone-delivery-Project-.git
cd Medical-drone-delivery-Project-
```

**Running a SITL simulation (Phase 2):**
```bash
# Launch ArduPilot SITL
sim_vehicle.py -v ArduCopter --console --map

# Run the mission script
python flight_simulations/autonomous_mission.py
```

---

<div align="center">

<!-- ═══════════════════════════════════════════════════════════════ -->
<!--  OPTIONAL FOOTER LOGO / SCHOOL BADGE                          -->
<!--  👉 Add your school logo, project badge, or a cool            -->
<!--     AeroMed logo you've designed here.                        -->
<!--     Recommended size: 200 × 200px                             -->
<!-- ═══════════════════════════════════════════════════════════════ -->

<img src="https://github.com/MatthewsDS/Medical-drone-delivery-Project-/blob/main/Media/Photos/IMG_2023.jpeg" alt="AeroMed Logo" width="120px"/>

<br/>

**Project AeroMed** · Year 12/13 STEM Engineering Project  
*Built with purpose. Engineered for impact.*

<br/>

![GitHub last commit](https://img.shields.io/github/last-commit/MatthewsDS/Medical-drone-delivery-Project-?style=flat-square&color=brightgreen)
![GitHub repo size](https://img.shields.io/github/repo-size/MatthewsDS/Medical-drone-delivery-Project-?style=flat-square&color=blue)
![GitHub stars](https://img.shields.io/github/stars/MatthewsDS/Medical-drone-delivery-Project-?style=flat-square&color=yellow)

</div>
