<div align="center">

<img src="https://github.com/MatthewsDS/Medical-drone-delivery-Project-/blob/main/Media/Photos/IMG_2022.jpeg" alt="Project AeroMed" width="65%"/>

<br/><br/>

# PROJECT AEROMED
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
![KiCad](https://img.shields.io/badge/KiCad-314CB0?style=for-the-badge&logo=kicad&logoColor=white)

<br/>

![GitHub last commit](https://img.shields.io/github/last-commit/MatthewsDS/Medical-drone-delivery-Project-?style=flat-square&color=brightgreen)
![GitHub repo size](https://img.shields.io/github/repo-size/MatthewsDS/Medical-drone-delivery-Project-?style=flat-square&color=blue)
![GitHub stars](https://img.shields.io/github/stars/MatthewsDS/Medical-drone-delivery-Project-?style=flat-square&color=yellow)

</div>

---

## 📖 Table of Contents

- [Mission Statement](#-mission-statement)
- [The Medical Payload](#-the-medical-payload)
- [Engineering Pillars](#%EF%B8%8F-engineering-pillars)
- [The Team](#-the-team)
- [Technology Stack](#%EF%B8%8F-technology-stack)
- [Project Timeline](#-project-timeline)
- [Repository Structure](#-repository-structure)
- [Getting Started](#-getting-started)

---

## 🎯 Mission Statement

> **"Time is the enemy in a medical emergency. Distance should not be."**

Project AeroMed is an autonomous hexacopter drone system designed to deliver temperature-sensitive, life-critical medical supplies to locations that traditional logistics cannot reach in time.

The drone uses **computer vision** for autonomous navigation and precision landing, **GPS waypoint navigation** for accurate routing, and an **actively regulated payload bay** that automatically adjusts its thermal environment based on the medicine being carried — no manual configuration required.

Built by five STEM students over a 9–12 month timeline, AeroMed bridges computer science, aerospace engineering, mathematics, and biomedical science into a single integrated system.

---

## 💊 The Medical Payload

The payload bay is engineered to safely transport five critical emergency medications, each with strict and distinct handling requirements. Selecting a medicine from the control interface **automatically reconfigures the payload bay** to the correct thermal profile — implemented as an interrupt-driven state machine on the Raspberry Pi.

<br/>

| Medication | Emergency Use Case | Temperature Requirement | Sensitivity |
|:---|:---|:---:|:---|
| 💉 **EpiPen / Adrenaline** | Anaphylactic shock | 15–25°C | Impact-sensitive; do not freeze |
| 🩹 **Naloxone** | Opioid overdose reversal | 15–25°C | Speed of delivery critical |
| 🐍 **Anti-Venom** | Venomous bites & stings | **2–8°C** ❄️ | Refrigerated; vibration-sensitive |
| 🩺 **Oxytocin** | Postpartum haemorrhage | **2–8°C** ❄️ | Cold chain essential; light-sensitive |
| 🩸 **Tranexamic Acid (TXA)** | Trauma bleeding control | 15–25°C | Highly stable; time-critical |

<br/>

> ❄️ Cold chain medicines (Anti-Venom, Oxytocin) require active **Peltier cooling** to maintain 2–8°C throughout the entire flight. Room-temperature medicines require insulation and continuous monitoring only.

---

## ⚙️ Engineering Pillars

<table>
<tr>
<td width="50%" valign="top">

### 🚁 Hexacopter Airframe
Six-motor configuration chosen specifically for **motor redundancy** — a safety requirement for a medical delivery drone. A quadcopter losing one motor crashes; a hexacopter can execute a controlled emergency landing. 550–680mm carbon fibre frame.

</td>
<td width="50%" valign="top">

### 👁️ Computer Vision
Real-time target detection using **OpenCV** and **YOLO** for autonomous identification of a landing zone — whether a waving person, marked address, or ArUco landing pad. Precision landing assisted by a **TF-Luna LiDAR** sensor.

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 🧬 Biomedical Payload Engineering
An insulated, vibration-dampened payload bay with **active Peltier thermal regulation**, real-time DS18B20/BME280 sensor monitoring, and auto-switching thermal profiles. Designed to meet WHO cold chain and IATA biologic packaging standards.

</td>
<td width="50%" valign="top">

### 🔌 Systems Integration
A **Cube Orange+** flight controller (redundant IMUs, professional-grade GPS) communicates with a **Raspberry Pi 5** via MAVLink. The Pi runs all vision, thermal control, and mission scripting logic simultaneously using Python multi-threading.

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 📐 6-DoF Kinematics & Mathematics
Coordinate frame transforms, rotation matrices, and quaternion-based attitude representation translate camera-space detections into real-world navigation commands. Modelled and validated in Jupyter Notebook before deployment.

</td>
<td width="50%" valign="top">

### 🔋 Dual-Battery Architecture
Two LiPo 4S 6000mAh batteries — one flies while one charges — doubling testing session efficiency. The custom KiCad PCB (manufactured by JLCPCB) keeps the thermal control circuit lightweight, clean, and professional.

</td>
</tr>
</table>

---

## 👥 The Team

<br/>

| Member | Role | Domain |
|:---|:---|:---|
| **Matthews** | Project Lead, Systems & Kinematics | Project management, SITL simulation, kinematics modelling, DroneKit mission scripting |
| **Jean-Paul** | Lead Programmer & CV Specialist | Computer vision (OpenCV, YOLO, CNNs), ArduPilot/MAVLink integration, autonomous targeting |
| **Malick** | Maths & Hardware Lead | Coordinate frame transforms, 6-DoF dynamics, CAD chassis design (Fusion 360), power distribution |
| **David** | Biochem & Payload Engineer | Thermodynamic isolation, biochemical stability research, cold chain compliance, PCB design |
| **Mustafa** | Biochem & Payload Engineer | Protein/enzyme degradation research, vibration impact analysis, payload bay testing, regulations |

---

## 🛠️ Technology Stack
╔══════════════════════════════════════════════════════════════════╗

║                        SOFTWARE LAYER                           ║

║   Python 3.x  ·  OpenCV  ·  DroneKit  ·  MAVLink  ·  YOLO     ║

╠══════════════════════════════════════════════════════════════════╣

║                      SIMULATION & DESIGN                        ║

║        ArduPilot SITL  ·  Fusion 360 CAD  ·  KiCad PCB        ║

╠══════════════════════════════════════════════════════════════════╣

║                        HARDWARE LAYER                           ║

║  Raspberry Pi 5  ·  Cube Orange+  ·  BLHeli32 ESCs             ║

║  T-Motor Brushless (×6)  ·  Here3 GPS  ·  TF-Luna LiDAR       ║

║  Peltier TEC Modules  ·  DS18B20 / BME280 Sensors              ║

╚══════════════════════════════════════════════════════════════════╝

**All software tools used are entirely free.** Python, VS Code, ArduPilot, DroneKit, OpenCV, Fusion 360 (personal licence), KiCad, GitHub — zero licensing cost. Hardware is the only expenditure, with a team budget of £1,000+.

---

## 📅 Project Timeline

The project runs across **two phases**, with hardware procurement bridging them.

<br/>
     JULY                    OCT/NOV               MAY/JUNE
       │                        │                      │
─────────┼────────────────────────┼──────────────────────┼─────────

│                        │                      │

████████████████████████████████  │                      │

PHASE 1 — LEARNING & SIMULATION   │                      │

(July → Oct/Nov 2026)             │                      │

│                      │

██ HARDWARE PROCUREMENT ██       │

(Oct/Nov 2026)                   │

│

████████████████████████████████

PHASE 2 — HARDWARE & FLIGHT

(Dec 2026 → May/Jun 2027)

<br/>

### 🖥️ Phase 1 — Learning & Simulation *(July – Oct/Nov 2026)*

The highest-productivity window. Learning and building happen simultaneously — topics the build never requires are skipped. Summer runs at full pace; university prep slows the final weeks.

- Development environment setup (Python, Git, VS Code, ArduPilot SITL)
- Foundational topic learning: flight control, kinematics, computer vision, thermodynamics
- First autonomous SITL mission scripted via DroneKit
- OpenCV target detection tested on webcam feeds
- Fusion 360 hexacopter frame and payload bay modelled
- Breadboard Peltier thermal control circuit built and tested
- Biochemical storage research completed for all five payload medicines

### 🔧 Phase 2 — Hardware & Flight Testing *(December 2026 – May/June 2027)*

Physical hardware phase — cannot be compressed. Crashes will happen; spare motors and props are budgeted.

- Full frame assembly, Cube Orange+ configuration via Mission Planner
- Bench testing all electronics; payload bay thermal validation
- First outdoor test flights; PID tuning for stable hover
- Autonomous GPS mission testing
- Computer vision + landing integration in real flight
- Quantitative results logged: delivery accuracy, thermal stability, detection success rates

> **Realistic total timeline:** 9–12 months from July 2026.
> Best case: 9 months · Most likely: 10–11 months · Worst case: 12–14 months.

---

## 📁 Repository Structure
AeroMed/

│

├── 📂 Phase_1_Learning_and_Simulation/

│   ├── 📂 biochemistry/              # Thermal & vibration stability research

│   ├── 📂 maths_and_kinematics/      # 6-DoF modelling, quaternions, transforms

│   ├── 📂 coding_and_cv/             # Python scripts, OpenCV detection, SITL missions

│   ├── 📂 cad_designs/               # Fusion 360 frame & payload bay (.F3D, .STL)

│   └── 📂 pcb_design/                # KiCad thermal control circuit (Gerbers for JLCPCB)

│

└── 📂 Phase_2_Hardware_and_Flight/

├── 📂 flight_controller/         # Cube Orange+ params & ArduPilot firmware configs

├── 📂 vision_integration/        # YOLO + ArUco precision landing scripts

├── 📂 payload_testing/           # Thermal regulation logs & vibration test data

└── 📂 telemetry_logs/            # Real flight data for performance analysis

---

## 🚀 Getting Started

> ⚠️ *Full setup instructions will be added as the project progresses into Phase 2.*

**Install Python dependencies:**
```bash
pip install opencv-python dronekit pymavlink numpy geopy folium
```

**Clone the repository:**
```bash
git clone https://github.com/MatthewsDS/Medical-drone-delivery-Project-.git
cd Medical-drone-delivery-Project-
```

**Run an ArduPilot SITL simulation (Phase 1):**
```bash
# Launch the virtual drone environment
sim_vehicle.py -v ArduCopter --console --map

# Execute an autonomous waypoint mission
python Phase_1_Learning_and_Simulation/coding_and_cv/autonomous_mission.py
```

> 📌 All work is version-controlled on GitHub. If it isn't on GitHub, it didn't happen.

---

<div align="center">

<br/>

<img src="https://github.com/MatthewsDS/Medical-drone-delivery-Project-/blob/main/Media/Photos/IMG_2023.jpeg" alt="AeroMed" width="110px"/>

<br/><br/>

**Project AeroMed** &nbsp;·&nbsp; Five engineers. One mission.

*Built with purpose. Engineered for impact.*

<br/>

</div>
