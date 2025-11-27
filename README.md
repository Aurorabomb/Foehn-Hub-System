# 🌪️ Foehn-Hub-System  
*A versatile asynchronous scheduling hub for liquid-handling robotic platforms*

---

## 🧩 Overview
The **Foehn Hub System** is an open-source hardware and software platform designed to enable **asynchronous, multi-threaded control** of peripheral laboratory modules within automated workstations.  
By integrating a liquid-handling robot (such as OT-Flex) with external devices—including **DC pumps**, **magnetic stirrers**, and **signal modules**—the Foehn system allows **parallel and coordinated operations** across multiple experimental tasks.

This system was developed to address the bottlenecks of **sequential pipetting workflows** in high-throughput experimentation (HTE), providing a compact, modular, and low-cost solution for automation researchers.

---

## ⚙️ System Architecture
The Foehn system bridges hardware and software layers through:
- 🧠 **Arduino-based control core** — modular design for multi-channel device management.  
- 💻 **Python GUI (Tkinter-based)** — intuitive control interface for pumps, stirrers, and signal indicators.  
- 🔗 **Serial communication (USB)** — ensures stable bidirectional data exchange between robot and controller.  
- ☁️ **HTTP-API integration** — allows remote command execution and data synchronization from robotic workstations.  

**Key components:**
- L298N H-bridge driver modules  
- DC peristaltic and diaphragm pumps  
- Magnetic stirrer array (96-channel compatible)  
- LED signal light system for real-time status indication  
- 3D-printed housing and multi-layer PLA structure

Foehn-Hub-System/
├── hardware/ # 3D models, CAD drawings, wiring layout
├── software/ # Arduino firmware & Python GUI scripts
├── docs/ # Figures, diagrams, test data, publications
├── LICENSE # Open hardware/software license (CERN-OHL-S)
└── README.md # Project documentation

---

## 🧰 Repository Structure
