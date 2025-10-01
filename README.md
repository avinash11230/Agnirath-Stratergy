# Agnirath-Stratergy
Agnirath strategy for the car to travel from chennai to Bangalore



About my Stratergy 

Solar Car Race Simulation

This project simulates the performance of a solar-powered race car over a defined route. The simulation aims to optimize the car’s velocity at each segment to minimize race time while ensuring efficient energy usage under varying terrain and solar conditions.



The route is divided into discrete segments. For each segment, the simulation determines the car’s velocity based on:

Solar irradiance (energy input from the sun)

Road slope (energy demand due to elevation changes)

Battery state of charge

Distance remaining to the finish line

A physics-based energy consumption model calculates the power required to sustain the chosen speed.

Key Features

Solar Irradiance Modeling: A sine-based daylight curve with noise simulates realistic solar input over the race duration.

Energy Model: Considers aerodynamic drag, rolling resistance, slope-induced gravitational forces, and drivetrain efficiency.

Battery Dynamics: Tracks the state of charge by accounting for both energy consumption and energy harvested from solar panels.

Velocity Optimization:

Uses the Adam optimizer at each segment to minimize a custom loss function that balances speed and energy conservation.

Includes specialized modes for critical battery levels and the final sprint phase.

Driving Strategy

Normal Mode:
The Adam optimizer computes an optimal velocity that prioritizes race progress while preserving battery energy.

Critical Recovery Mode (Battery below a defined threshold):
The car reduces speed to conserve energy and prevent battery depletion.

Final Sprint Mode (Close to the finish line):
The car prioritizes maximum velocity to minimize time, disregarding energy conservation.

This strategy enables efficient energy utilization during most of the race while ensuring competitive performance near the end.

Outputs

Velocity profile (in km/h) as a function of distance

Battery state of charge (in percentage) as a function of distance

Total race time and final battery state of charge at the end of the race
