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

---

## Data fusion

The water-risk model combines three components:

```text
Water-level deficit              50 %
Evaporative conditions           30 %
Level-decrease trend             20 %
```

Conceptually:

```text
WATER LEVEL
     ↓
LEVEL DEFICIT ─────────── 50 % ──┐
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
DECREASE RATE ─────────── 20 % ───┘
```

The weighted index is complemented by **independent safety rules**, allowing an extreme individual condition to escalate the system state even when the weighted average has not yet reached the critical threshold.

---

## Environmental analysis

Temperature and relative humidity measured by the BME280 are used to calculate **Vapor Pressure Deficit (VPD)**.

VPD provides an indicator of how favorable atmospheric conditions are for evaporation.

The photovoltaic panel and INA219 provide an electrical signal related to the amount of radiation received. This signal is used as an **experimental estimate of solar irradiance**.

VPD and estimated irradiance are then combined into an **evaporative-condition index**.

This index does not represent the actual percentage of water evaporated. Instead, it indicates how favorable the environmental conditions are for evaporation.

Atmospheric pressure is also measured by the BME280. It is not used as a risk indicator — in a fixed tropical station its variation is negligible and it does not respond to water scarcity. Instead, it acts as a **parameter of the evaporation model**: through the psychrometric constant, it determines the Penman partition between the radiative and aerodynamic terms. At the 2550 m altitude of Sabana Centro, this shifts the weighting towards evaporation by approximately 10 % relative to sea level. A model calibrated with sea-level parameters would underestimate local evaporative demand.

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

### Experimental characterization

Before fixing the trend-detection parameters, the ultrasonic sensor's noise was characterized experimentally: with the platform stationary, 20 measurements were taken and their standard deviation computed. From this, the standard error of a
least-squares slope over the estimation window was derived, and the dead band was set at three times that value — keeping the false-positive rate below 1 %. This characterization runs automatically at every startup, so the dead band adapts to the specific installation rather than relying on a fixed a-priori value.

The trend thresholds were then calibrated using two controlled descent manoeuvres, yielding maximum slopes of **46.9 pp/min** (slow) and **98.2 pp/min** (fast). The precaution threshold was set at 70 % of the slow manoeuvre and the critical threshold at the geometric mean of both, which leaves the same relative margin on either side.

---

## Conclusion

WREWS demonstrates how a low-cost IoT system can combine **water level, environmental conditions, and level trend** to provide a more comprehensive assessment of water-scarcity risk.

The final result is a functional physical prototype capable of acquiring multiple variables, processing them locally on an ESP32, and translating the information into three clear warning states.

The project demonstrates the complete transition from **sensing to decision and local actuation**, providing a functional proof of concept for an early water-risk warning system.

---

[⬅ Previous: Team and roles](09-Equipo-Roles.md) · [⬆ Index](00-Home.md)
