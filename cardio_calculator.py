def get_value(prompt):
    """
    Prompts the user for input.
    Returns a float if input is provided, or None if left blank.
    """
    value = input(prompt)
    if value.strip() == "":
        return None
    try:
        return float(value)
    except ValueError:
        print("Please enter a valid number or leave blank.")
        return get_value(prompt)

def main():
    print("Enter values for the following variables. Leave one blank (press Enter) if unknown.")
    heart_rate = get_value("Heart rate: ")
    weight = get_value("Weight (in kg): ")
    age = get_value("Age (in years): ")
    kcal_per_min = get_value("Kcal per minute: ")

    # Count how many values are missing.
    missing_count = sum(v is None for v in [heart_rate, weight, age, kcal_per_min])
    if missing_count != 1:
        print("Error: Exactly one value must be missing.")
        return

    # The equation (after multiplying both sides by 4.184):
    # 4.184 * kcal_per_min = -55.0969 + 0.6309 * heart_rate + 0.1988 * weight + 0.2017 * age

    # Solve for the missing variable.
    if kcal_per_min is None:
        # Solve for kcal_per_min:
        kcal_per_min = (-55.0969 + 0.6309 * heart_rate + 0.1988 * weight + 0.2017 * age) / 4.184
        print(f"Calculated kcal per minute: {kcal_per_min:.4f}")
    elif heart_rate is None:
        # Solve for heart_rate:
        # 0.6309 * heart_rate = 4.184 * kcal_per_min + 55.0969 - 0.1988 * weight - 0.2017 * age
        heart_rate = (4.184 * kcal_per_min + 55.0969 - 0.1988 * weight - 0.2017 * age) / 0.6309
        print(f"Calculated heart rate: {heart_rate:.4f}")
    elif weight is None:
        # Solve for weight:
        # 0.1988 * weight = 4.184 * kcal_per_min + 55.0969 - 0.6309 * heart_rate - 0.2017 * age
        weight = (4.184 * kcal_per_min + 55.0969 - 0.6309 * heart_rate - 0.2017 * age) / 0.1988
        print(f"Calculated weight (kg): {weight:.4f}")
    elif age is None:
        # Solve for age:
        # 0.2017 * age = 4.184 * kcal_per_min + 55.0969 - 0.6309 * heart_rate - 0.1988 * weight
        age = (4.184 * kcal_per_min + 55.0969 - 0.6309 * heart_rate - 0.1988 * weight) / 0.2017
        print(f"Calculated age (years): {age:.4f}")

if __name__ == "__main__":
    main()
