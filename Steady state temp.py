def calculate_steady_state_temp(temp_a, tau):
    """
    Calculates the steady-state winding temperature of a motor.

    Arguments:
        temp_a (float)
        tau (float): Motor torque in Nm.

    Returns:
        float: The steady-state winding temperature in Kelvin, rounded to 1 decimal place.
    """
    # Initial guess for winding temperature (T_w) in Kelvin.
    # Using a float ensures precision in calculations.
    T_w = 323.0

    # This loop will continue until the temperature change between iterations is less than 1 K.
    while True:
        # Store the current temperature to check for convergence at the end of the loop.
        T_w_old = T_w

        # --- Start of a single iteration ---

        # 1. Calculate Magnet temp (average of ambient and winding)
        T_m = (temp_a + T_w_old) / 2

        # 2. Calculate Remanence (magnetic strength, decreases with temp)
        B = 1.32 - 1.2e-3 * (T_m - 293)

        # 3. Calculate Phase current required for the given torque
        i = 0.561 * B * tau

        # 4. Calculate Resistance (increases with temp)
        R = 0.0575 * (1 + 0.0039 * (T_w_old - 293))

        # 5. Calculate Copper loss (heat from resistance)
        P_c = 3 * (i**2) * R

        # 6. Calculate Eddy loss (heat from magnetic effects)
        # Check to prevent division by zero, though R should always be positive here.
        if R > 0:
            P_e = (9.602e-6 * (B * tau)**2) / R
        else:
            P_e = 0

        # 7. Update the winding temperature based on total heat loss
        T_w = 0.455 * (P_c + P_e) + temp_a

        # --- Check for the stopping condition ---
        if abs(T_w - T_w_old) < 1:
            break

    # Once the loop breaks, return the final stable temperature.
    return round(T_w, 2) #rounds off T_w to 1 decimal point


calculate_steady_state_temp(298,100)