[⬅ Back to index](00-Home.md)

# 10. English Executive Summary

## WREWS — Water Risk Early Warning System

**WREWS (Water Risk Early Warning System)** is a low-cost IoT prototype designed to monitor water availability and generate early local warnings when conditions associated with water-scarcity risk are detected.

The system is built around an **ESP32** and combines three main dimensions:

1. **Current water availability**, estimated from the reservoir level.
2. **Environmental conditions favorable to evaporation**, derived from temperature, relative humidity, and estimated solar irradiance.
3. **Water-level trend**, obtained by analyzing the rate at which the level decreases over time.

Rather than relying on a single measurement, WREWS fuses these signals into a **water-risk index** and classifies the situation into three easily understandable states:

- 🟢 **NORMAL**
- 🟡 **PRECAUTION**
- 🔴 **CRITICAL**

In **Challenge #2** the prototype became a **finished, enclosed, battery-powered device** that, in addition to the local alarm, hosts a **web dashboard** on an embedded web server inside the ESP32. The dashboard is reachable only from the local WLAN provided by the authorities and only after logging in. It shows current values and recent history, notifies every state change, lets authorities silence the physical alarm, and allows calibration without opening the enclosure. The evaporative index was replaced by **Priestley-Taylor potential evaporation with FAO-56 parameters**, and the weights and thresholds are now anchored to cited methods and regulations.

---

## System architecture

The physical prototype integrates:

- **ESP32** as the central processing unit.
- **OKY3261/HC-SR04 ultrasonic sensor** for water-level estimation.
- **BME280** for temperature, relative humidity, and atmospheric pressure.
- **Mini photovoltaic panel + INA219** for experimental solar-irradiance estimation.
- **16×2 I²C LCD** for local visualization.
- **Green, yellow, and red LEDs** for status indication.
- **Buzzer** for critical audible warnings.

All sensing, processing, risk classification, and actuation are performed **locally on the ESP32**.

Therefore, WREWS does not depend on Wi-Fi, cellular networks, cloud services, or any external communication infrastructure to generate an alert.

Since Challenge #2, the firmware runs on three FreeRTOS threads: measurement on core 0, alarms on core 1, and the web server, Wi-Fi and LCD in the main loop. Two mutexes protect the shared state and the I²C bus. Because the alarms run in their own task, a slow browser or a WLAN outage cannot freeze the physical alarm.

---

## Data fusion

The water-risk model combines three components:

```text
Water-level deficit              54 %
Evaporative conditions           30 %
Level-decrease trend             16 %
```

The weights are the priority vector obtained with Saaty's **Analytic Hierarchy Process** (consistency ratio 0.008); Challenge #1 used the rounded 50/30/20.

Conceptually:

```text
WATER LEVEL
     ↓
LEVEL DEFICIT ─────────── 54 % ──┐
                                  │
TEMPERATURE + HUMIDITY            │
     ↓                            │
    VPD                           ├──→ WATER-RISK INDEX
     +                            │
ESTIMATED IRRADIANCE              │
     ↓                            │
EVAPORATIVE INDEX ─────── 30 % ───┤
                                  │
LEVEL OVER TIME                   │
     ↓                            │
DECREASE RATE ─────────── 16 % ───┘
```

The weighted index is complemented by **independent safety rules**, allowing an extreme individual condition to escalate the system state even when the weighted average has not yet reached the critical threshold. The one exception, introduced in Challenge #2, is evaporation: on its own it can raise the state only up to PRECAUTION, because a sunny, dry noon with a full reservoir is not an emergency. It still feeds the combined risk with its weight, so a low level plus high evaporation does reach CRITICAL.

| Variable | PRECAUTION | CRITICAL | Source |
|---|---|---|---|
| Level | ≤ 50 % | ≤ 15 % | Spanish Drought Management Plans (pre-alert 0.50, emergency 0.15) |
| Evaporative index | ≥ 60 | ≥ 85 (severity only) | Assumption; to be closed with local climatological percentiles |
| Decrease rate | ≥ 33 pp/min | ≥ 68 pp/min | Experimental calibration |
| Combined risk | ≥ 36.2 | ≥ 69.2 | Derived from the level thresholds |

---

## Environmental analysis

Temperature and relative humidity measured by the BME280 are used to calculate **Vapor Pressure Deficit (VPD)**.

VPD provides an indicator of how favorable atmospheric conditions are for evaporation.

The photovoltaic panel and INA219 provide an electrical signal related to the amount of radiation received. This signal is used as an **experimental estimate of solar irradiance**.

In Challenge #2, the evaporative index is built on the **Priestley-Taylor** equation, λET = α·Δ/(Δ+γ)·(Rn − G), with net radiation, Δ and γ computed with **FAO-56**. The model runs over a moving window of measurements (24 h in field mode; in demo mode a short window whose average light is treated as the noon of a day with that cloudiness, using the clearness index). The resulting daily evaporation is normalized against a clear day at the site (7.5 mm/day) and combined with the window's VPD:

```text
Evaporative index = 70 · min(ET / 7.5, 1) + 30 · min(VPD / 2.0, 1)
```

This index does not represent the actual percentage of water evaporated. Instead, it indicates how favorable the environmental conditions are for evaporation.

Atmospheric pressure is also measured by the BME280. It is not used as a risk indicator — in a fixed tropical station its variation is negligible and it does not respond to water scarcity. Instead, it acts as a **parameter of the evaporation model**: through the psychrometric constant γ = 0.665·10⁻³·P, the measured pressure sets the Priestley-Taylor term Δ/(Δ+γ) directly, replacing the fixed altitude factor used in Challenge #1.

---

## Level trend

WREWS also analyzes multiple water-level measurements over time.

This makes it possible to estimate the **rate of level decrease** and distinguish between two reservoirs that may currently have the same level but are evolving differently.

For example:

```text
Reservoir A
Level: 50 %
Decrease rate: low
→ relatively stable

Reservoir B
Level: 50 %
Decrease rate: high
→ water availability is declining rapidly
```

This trend analysis adds an early-warning component to the system.

---

## Local warning system

After processing the available information, WREWS classifies the situation and activates the corresponding local indicators:

```text
NORMAL
→ Green LED
→ LCD status
→ Buzzer off

PRECAUTION
→ Yellow LED
→ LCD status

CRITICAL
→ Red LED
→ LCD status
→ Audible buzzer warning
```

The **16×2 I²C LCD** provides local information about the system, while the LEDs make the current state immediately recognizable.

---

## Web dashboard (Challenge #2)

The ESP32 joins the local WLAN in station mode and serves a dashboard with no external libraries or cloud services. It provides:

- current values of all variables, color-coded by severity;
- a 10-minute history chart for level, risk, evaporative index, decrease rate, temperature and irradiance, with dashed threshold lines;
- an event log with on-screen, sound and vibration notifications for every state change;
- a button to silence the buzzer for 15 minutes (the LEDs keep showing the state);
- a calibration panel (tank full/empty distances, panel constant, rate thresholds, demo or field mode), stored in the ESP32 flash.

Access requires both being on the same subnet as the device and an authenticated session (random 128-bit token in an HttpOnly cookie, lockout after 5 failed attempts). As a declared limitation, the dashboard uses HTTP without TLS.

---

## Validation

The development and validation process was divided into two stages.

### Stage 1 — Wokwi simulation

The system was initially developed and tested in Wokwi.

The simulation allowed the team to:

- validate the system architecture;
- test sensor acquisition;
- verify I²C communication;
- evaluate the mathematical processing;
- reproduce controlled environmental scenarios;
- validate NORMAL, PRECAUTION, and CRITICAL states;
- debug the firmware before physical integration.

Custom simulation components were used for some sensors and signals.

### Stage 2 — Physical prototype

After the simulation stage, WREWS was assembled and tested as a **functional physical prototype**.

A movable platform was incorporated into the scale model to represent the water surface.

Changing the platform height modifies the distance measured by the ultrasonic sensor, allowing different reservoir levels to be reproduced safely and repeatedly without exposing the electronics directly to water.

Physical testing confirmed the operation of:

- ultrasonic level sensing;
- BME280 environmental acquisition;
- photovoltaic panel and INA219 acquisition;
- local processing on the ESP32;
- level-decrease analysis;
- risk classification;
- 16×2 I²C LCD;
- status LEDs;
- critical buzzer alarm.

The physical implementation therefore validated the complete chain:

```text
SENSING
   ↓
ACQUISITION
   ↓
PROCESSING
   ↓
DATA FUSION
   ↓
RISK CLASSIFICATION
   ↓
LOCAL WARNING
```

### Stage 3 — Challenge #2 test bench

The finished device was tested outdoors in the sun, following the minimum blocks required by the brief: calibration against reference instruments, accelerated emulation (draining the tube, sun and shade on the panel, a hair dryer on the BME280), validation of the fusion logic and thresholds, notification tests (dashboard updates, alerts, silencing the alarm from the dashboard), and robustness tests (WLAN loss and reconnection, restricted access). An on-board self-test checks the evaporation model against independently computed reference values at every start-up. These tests revealed and fixed four real issues: saturation of the evaporative index in full sun, false CRITICAL alarms caused by evaporation alone with a full reservoir, a dashboard that did not recover after a WLAN outage, and a critical-alarm tone (2500 Hz) above the buzzer's usable range (now 2000 Hz).

### Experimental characterization

Before fixing the trend-detection parameters, the ultrasonic sensor's noise was characterized experimentally: with the platform stationary, 20 measurements were taken and their standard deviation computed. From this, the standard error of a
least-squares slope over the estimation window was derived, and the dead band was set at three times that value — keeping the false-positive rate below 1 %. This characterization runs automatically at every startup, so the dead band adapts to the specific installation rather than relying on a fixed a-priori value.

The trend thresholds were then calibrated using two controlled descent manoeuvres, yielding maximum slopes of **46.9 pp/min** (slow) and **98.2 pp/min** (fast). The precaution threshold was set at 70 % of the slow manoeuvre and the critical threshold at the geometric mean of both, which leaves the same relative margin on either side.

---

## Conclusion

WREWS demonstrates how a low-cost IoT system can combine **water level, environmental conditions, and level trend** to provide a more comprehensive assessment of water-scarcity risk.

The final result is a functional physical prototype capable of acquiring multiple variables, processing them locally on an ESP32, and translating the information into three clear warning states.

The project demonstrates the complete transition from **sensing to decision and local actuation**, providing a functional proof of concept for an early water-risk warning system.

In Challenge #2, WREWS evolved into an enclosed, battery-powered device with a secure local web dashboard, a physically based evaporation model, and weights and thresholds traceable to published methods and regulations.

---

[⬅ Previous: Team and roles](09-Equipo-Roles.md) · [⬆ Index](00-Home.md)
