# Medical-drone-delivery-Project-
Develop a drone system capable of delivering medical supplies to remote areas using sensors, cameras, and automation. Be able to deliver vital medical supplies like such as EpiPen's, Adrenaline, Naloxone, Anti-venoms, Oxytocin, and Tranexamic Acid
# Autonomous Biomedical Delivery Drone (Project AeroMed)

[![Project Status: Active](https://img.shields.io/badge/Project%20Status-Active-green.svg)](https://github.com/MatthewsDS/Medical-drone-delivery-Project-)
[![Target](https://img.shields.io/badge/Target-UCAS%20%7C%20Degree%20Apprenticeships-blue)](https://github.com/MatthewsDS)

An advanced, autonomous unmanned aerial vehicle (UAV) engineered for time-critical, emergency biomedical deliveries. This project bridges university-level mathematics, computer vision navigation, and biochemistry to solve real-world logistical challenges in healthcare.

---

## 🚀 Project Overview

The objective of this project is to design, simulate, and construct a physical quadcopter capable of navigating autonomously to a destination via computer vision, ensuring the thermal and mechanical stability of sensitive medical payloads (e.g., vaccines, insulin, or blood samples). 

### Key Engineering Pillars
* **6-DoF Kinematics & Mathematics:** Transforming localized camera coordinate frames into global navigation waypoints.
* **Computer Vision (CV):** Implementing OpenCV-based target detection for precision landing and obstacle avoidance.
* **Biomedical Engineering:** Designing an insulated, vibration-dampened payload bay maintaining strict temperature controls.
* **Systems Integration:** Merging hardware flight controllers with onboard microcomputers (e.g., Raspberry Pi) for real-time edge processing.

---

## 👥 The Engineering Team & Specialties

We are a team of five Year 12/13 STEM students treating this project as an industry-grade engineering sprint. Each member owns a critical subsystem:

* **[Jean-Paul] (Lead Programmer / CV Specialist):** Focuses on computer vision algorithms, ArduPilot/MAVLink integration, and OpenCV targeting scripts.
* **[Malick & Matthews & Jean Paul] (Maths & Kinematics Lead):** Owns coordinate frame transformations, 6-DoF flight dynamics modeling, and physics simulations.
* **[David & Mustafa] (Biochem & Payload Engineer):** Responsible for the thermodynamic isolation of the payload bay and monitoring biochemical stability during transit.
* **[Malick & Matthews] (Hardware & Aerospace Lead):** Manages CAD chassis design, weight-to-thrust calculations, power distribution, and mechanical assembly.
* **[Matthews] (Systems & Repo Administrator):** Oversees architecture integration, Git version control, and end-to-end hardware-in-the-loop (HITL) simulation.

---

## 📅 Roadmap & Timeline

Our 7-month development cycle is split into three rigorous phases:

### Phase 1: The Learning & Research Era (Months 1-3)
* Deep dive into university-level kinematics papers and OpenCV documentation.
* Establish baseline mathematical models for drone rotation and translation matrices.
* Initial biochemistry research into enzyme/protein degradation under vibration.

### Phase 2: Simulation & CAD (Months 4-5)
* Develop and test OpenCV target-tracking scripts using PC webcams.
* Model the physical drone chassis and payload bay in CAD software (Fusion360/SolidWorks).
* Run Software-in-the-Loop (SITL) flight simulations to test autonomous mission scripts.

### Phase 3: Hardware Integration & Flight Trials (Months 6-7)
* Procurement and physical assembly of the frame, ESCs, motors, and flight controller.
* Bench-testing the payload container's thermal and vibration dampening capabilities.
* Real-world autonomous flight testing, telemetry log analysis, and iterative troubleshooting.

---

## 📁 Repository Structure

```text
├── 01_learning_phase/          # Research papers, math derivations, and core notes
│   ├── biochemistry/           # Thermal/vibration stability research
│   ├── maths_and_kinematics/   # 6-DoF modeling and matrix transformations
│   └── coding_and_cv/          # Early Python & OpenCV tutorials
├── 02_simulation_and_cad/      # The digital design and simulation environment
│   ├── opencv_testing/         # Target detection code tested via webcam
│   ├── cad_designs/            # 3D modeling files (.STL, .STEP)
│   └── flight_simulations/     # SITL simulation profiles and flight scripts
└── 03_hardware_and_flight/     # Real-world deployment files
    ├── flight_controller/      # Parameter configurations and firmware settings
    └── telemetry_logs/         # Real flight data for performance analysis
