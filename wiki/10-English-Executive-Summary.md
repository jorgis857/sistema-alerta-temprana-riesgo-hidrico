[⬅ Back to index](00-Home.md)

# 10. Executive Summary (English)

> Written communication for engineering audiences is expected to demonstrate proficiency in a second language (English), per the course rubric. This page summarizes the project in English; the full technical documentation remains in Spanish across the rest of this Wiki.

## Project

**SATRH (Sistema de Alerta Temprana de Riesgo Hídrico / Early Water-Risk Warning System)** is a low-cost IoT prototype built on an **ESP32** microcontroller that monitors, in real time, the water level of a community reservoir, the environmental conditions that favor its evaporation, and the speed at which the level is dropping. These three signals are fused into a single **water-risk index** that drives a fully **local (in-situ) alert** — an OLED display, status LEDs, and a buzzer — with no dependency on Wi-Fi, cellular networks, or any communication infrastructure whatsoever.

## Motivation

During 2026, Colombia's national government and IDEAM confirmed an early onset of the El Niño phenomenon, sharply increasing water-scarcity risk across the Sabana Centro region of Cundinamarca. The regional environmental authority (CAR) identified 20 municipalities at extreme risk of water shortage. Rural communities that manage small reservoirs and wells (*aljibes*) often lack the technical infrastructure to monitor these assets continuously. SATRH addresses this gap with a standalone, battery/solar-powered sensor node that requires no network connectivity and no cloud services.

## System architecture

The node integrates three sensing subsystems — a **BME280** (temperature, humidity, atmospheric pressure), an **INA219** current sensor coupled to a small **solar panel** (used as a proxy for solar irradiance), and an **HC-SR04** ultrasonic sensor (used to estimate reservoir water level). All processing — sensor fusion, risk classification, and actuation — runs entirely on the ESP32, satisfying the challenge's explicit constraint of *"in-situ notification without conventional communication networks."*

## Data-fusion model

The system computes: (1) reservoir **level (%)** from the measured distance; (2) the **Vapor Pressure Deficit (VPD, kPa)** from temperature and humidity, using the Tetens/FAO-56 saturation-vapor-pressure equation; (3) an **evaporative index (%)**, combining normalized solar radiation and VPD (50%/50%); (4) a **level-drop rate (percentage points per hour)**, comparing successive level readings over time; and (5) an overall **water risk index (%)**, computed as a weighted sum: 50% level deficit + 30% evaporative index + 20% drop-rate index. Independent **safety rules** (hard thresholds on level, evaporative index, and drop rate) guarantee that no single extreme variable is diluted by the weighted average — a deliberate design decision validated experimentally in the test cases described in Section 5.

## Results

Eight test scenarios were designed and independently re-computed in Python (replicating the firmware's exact formulas) to confirm mathematical consistency between the embedded implementation and the documented model. The scenarios successfully exercise all three alert states — 🟢 NORMAL, 🟡 PRECAUCIÓN (caution), 🔴 CRÍTICO (critical) — and all four independent paths that can trigger a critical alert (low level, extreme evaporative conditions, fast level drop, and combined weighted risk), confirming the robustness of the fusion logic.

## Conclusion and future work

The prototype was fully validated in simulation using **Wokwi**, with custom C chips emulating the BME280, INA219, and solar-panel hardware. Planned future work includes migration to physical hardware, field calibration at real reservoir sites in Sabana Centro, IP-rated enclosure design, expanded edge-case and recovery-transition testing, and validation of the alert thresholds against real historical hydrological data for the region.

---
[⬅ Back to index](00-Home.md)
