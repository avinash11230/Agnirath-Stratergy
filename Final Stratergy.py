import numpy as np

def generate_irradiance(num_points, start_hour, duration_hours, peak_irradiance):
    """Generates a realistic solar irradiance curve."""
    # Define the total daylight period (e.g., 6 AM to 6 PM is 12 hours)
    total_daylight_hours = 12
    # Calculate the time points for the trip in hours from sunrise (6 AM)
    # e.g., an 8 AM start is 2 hours from sunrise.
    start_time_from_sunrise = start_hour - 6
    end_time_from_sunrise = start_time_from_sunrise + duration_hours

    time_points = np.linspace(start_time_from_sunrise, end_time_from_sunrise, num_points)

    # Model the irradiance curve using a sine function
    # It peaks at noon (6 hours from sunrise)
    irradiance = peak_irradiance * np.sin(np.pi * time_points / total_daylight_hours)

    # Add some slight noise to make it more realistic
    noise = np.random.normal(0, 15, num_points)
    irradiance += noise

    # Ensure no negative values and convert to integers
    irradiance[irradiance < 0] = 0
    return [int(val) for val in irradiance]

# --- Parameters for your specific race ---
NUM_DATAPOINTS = 316
START_HOUR = 8  # 8 AM
DURATION_HOURS = 5
PEAK_IRRADIANCE = 1000  # Watts/m^2 for a very clear day

# Generate the data
irradiance_data = generate_irradiance(NUM_DATAPOINTS, START_HOUR, DURATION_HOURS, PEAK_IRRADIANCE)

# print(irradiance_data) # Uncomment to see the generated list



import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ---------------- CONSTANTS -----------------
CAR_MASS_KG = 330
DRAG_COEFFICIENT = 0.12
FRONTAL_AREA_M2 = 1.08
ROLLING_RESISTANCE_COEFF = 0.0045
DRIVETRAIN_EFFICIENCY = 0.98
PANEL_AREA_M2 = 6.0
PANEL_EFFICIENCY = 0.22
TOTAL_BATTERY_CAPACITY_WH = 3000
AIR_DENSITY_KGM3 = 1.225
GRAVITY_MS2 = 9.81

AGGRESSIVE_TARGET_SPEED_KMH = 95.0
CRITICAL_BATTERY_THRESHOLD = 5.0      # %
FINISH_LINE_KM = 30

MIN_VELOCITY_MS = 0.1

# Adam hyper-parameters
ADAM_LR = 0.03
BETA1 = 0.9
BETA2 = 0.999
EPS = 1e-8


# ------------ UTILITY FUNCTIONS -----------------
def calculate_power_needed(v_ms, grade_percent):
    """Return power in W needed to hold v_ms on given slope."""
    if v_ms <= 0:
        return 0.0
    grade_angle = np.arctan(grade_percent / 100.0)
    drag = 0.5 * AIR_DENSITY_KGM3 * DRAG_COEFFICIENT * FRONTAL_AREA_M2 * (v_ms ** 2)
    roll = ROLLING_RESISTANCE_COEFF * CAR_MASS_KG * GRAVITY_MS2 * np.cos(grade_angle)
    grav = CAR_MASS_KG * GRAVITY_MS2 * np.sin(grade_angle)
    mech = (drag + roll + grav) * v_ms
    return max(0.0, mech / DRIVETRAIN_EFFICIENCY)


# def generate_irradiance(n, peak=1000):
#     """Simple synthetic daylight curve."""
#     t = np.linspace(0, np.pi, n)
#     irr = peak * np.sin(t)
#     irr += np.random.normal(0, peak * 0.03, n)
#     irr[irr < 0] = 0
#     return irr


# --------- LOSS FUNCTION FOR OPTIMIZATION -------------
def velocity_loss(v_ms, grade_percent, power_from_sun, battery_frac):
    """
    Example loss:
      - want to go fast (negative term)
      - penalize drawing battery power too hard
    """
    power_need = calculate_power_needed(v_ms, grade_percent)
    deficit = max(0.0, power_need - power_from_sun)
    # we penalize deficit more when battery is low
    penalty = deficit * (1.0 + max(0, 0.5 - battery_frac))
    return -v_ms + 0.0005 * penalty


def adam_update_velocity(v_init, grade_percent, power_from_sun, battery_frac,
                          lr=ADAM_LR, beta1=BETA1, beta2=BETA2, eps=EPS, steps=40):
    """
    Run a few Adam steps to minimize velocity_loss w.r.t velocity.
    """
    v = v_init
    m = 0.0
    s = 0.0
    for t in range(1, steps + 1):
        # numerical gradient (finite difference)
        h = 1e-3
        grad = (velocity_loss(v + h, grade_percent, power_from_sun, battery_frac) -
                velocity_loss(v - h, grade_percent, power_from_sun, battery_frac)) / (2 * h)

        m = beta1 * m + (1 - beta1) * grad
        s = beta2 * s + (1 - beta2) * (grad ** 2)
        m_hat = m / (1 - beta1 ** t)
        s_hat = s / (1 - beta2 ** t)

        v -= lr * m_hat / (np.sqrt(s_hat) + eps)
        v = np.clip(v, MIN_VELOCITY_MS, AGGRESSIVE_TARGET_SPEED_KMH / 3.6)
    return v


# -------------- MAIN SIMULATION -----------------
def simulate_race(route_df):
    total_distance_km = len(route_df)
    batt_wh = TOTAL_BATTERY_CAPACITY_WH
    dist_m = 1000.0
    total_time_s = 0.0

    vel_profile = []
    batt_profile = []
    modes = []
    dist_profile = []

    for i in range(len(route_df) - 1):
        batt_frac = batt_wh / TOTAL_BATTERY_CAPACITY_WH
        dist_to_finish = total_distance_km - i

        # slope
        grade = (route_df.iloc[i + 1]['altitude_meters'] - route_df.iloc[i]['altitude_meters']) / dist_m * 100.0
        irr = irradiance_data[i]
        sun_power = irr * PANEL_AREA_M2 * PANEL_EFFICIENCY

        # choose velocity
        if dist_to_finish <= FINISH_LINE_KM:
            mode = "Final Sprint"
            v_ms = AGGRESSIVE_TARGET_SPEED_KMH / 3.6
        elif batt_frac * 100.0 <= CRITICAL_BATTERY_THRESHOLD:
            mode = "Critical Recovery"
            v_ms = adam_update_velocity(10.0 / 3.6, grade, sun_power, batt_frac)
        else:
            mode = "Adam-optimized"
            v_ms = adam_update_velocity(AGGRESSIVE_TARGET_SPEED_KMH / 3.6, grade, sun_power, batt_frac)

        # time and energy
        t_seg = dist_m / max(v_ms, MIN_VELOCITY_MS)
        power_need = calculate_power_needed(v_ms, grade)
        energy_need = power_need * t_seg / 3600.0
        energy_from_sun = sun_power * t_seg / 3600.0

        # battery update
        if energy_from_sun >= energy_need:
            batt_wh = min(TOTAL_BATTERY_CAPACITY_WH,
                          batt_wh + (energy_from_sun - energy_need))
        else:
            batt_wh = max(0.0, batt_wh - (energy_need - energy_from_sun))

        total_time_s += t_seg

        # store
        vel_profile.append(v_ms * 3.6)
        batt_profile.append(batt_wh / TOTAL_BATTERY_CAPACITY_WH * 100.0)
        modes.append(mode)
        dist_profile.append(i + 1)

    print(f"Race time: {total_time_s/3600:.2f} h  |  Final battery: {batt_profile[-1]:.2f}%")

    return {
        "distance": dist_profile,
        "velocity": vel_profile,
        "battery": batt_profile,
        "modes": modes
    }


# -------------------- DRIVER --------------------
if __name__ == "__main__":
    # EXAMPLE: if you have irradiance_data list
    N = 316
    route_df = pd.DataFrame({
        "altitude_meters": np.linspace(0, 200, N),
        "solar_irradiance": irradiance_data  # or replace with your irradiance_data
    })

    results = simulate_race(route_df)

    # --- plot ---
    fig, ax1 = plt.subplots(figsize=(14, 7))
    ax1.plot(results["distance"], results["velocity"], color='tab:blue', label='Velocity (km/h)')
    ax1.set_xlabel("Distance (km)")
    ax1.set_ylabel("Velocity (km/h)", color='tab:blue')

    ax2 = ax1.twinx()
    ax2.plot(results["distance"], results["battery"], color='tab:green', linestyle='--', label='Battery (%)')
    ax2.set_ylabel("Battery (%)", color='tab:green')

    plt.title("Race simulation with per-step Adam velocity optimization")
    fig.tight_layout()
    plt.show()