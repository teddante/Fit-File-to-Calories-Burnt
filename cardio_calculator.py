def prompt_float(prompt: str) -> float | None:
    """
    Prompt the user for a float value. Returns None if input is blank.
    """
    value = input(prompt)
    if value.strip() == "":
        return None
    try:
        return float(value)
    except ValueError:
        print("Please enter a valid number or leave blank.")
        return prompt_float(prompt)

def calculate_kcal_per_min(heart_rate: float, weight: float, age: float) -> float:
    """
    Calculate kcal per minute using the Keytel et al. formula for men.
    """
    return (-55.0969 + 0.6309 * heart_rate + 0.1988 * weight + 0.2017 * age) / 4.184

def calculate_heart_rate(kcal_per_min: float, weight: float, age: float) -> float:
    """
    Solve for heart rate given kcal_per_min, weight, and age.
    """
    return (4.184 * kcal_per_min + 55.0969 - 0.1988 * weight - 0.2017 * age) / 0.6309

def calculate_weight(kcal_per_min: float, heart_rate: float, age: float) -> float:
    """
    Solve for weight given kcal_per_min, heart_rate, and age.
    """
    return (4.184 * kcal_per_min + 55.0969 - 0.6309 * heart_rate - 0.2017 * age) / 0.1988

def calculate_age(kcal_per_min: float, heart_rate: float, weight: float) -> float:
    """
    Solve for age given kcal_per_min, heart_rate, and weight.
    """
    return (4.184 * kcal_per_min + 55.0969 - 0.6309 * heart_rate - 0.1988 * weight) / 0.2017

def main():
    print("Enter values for the following variables. Leave one blank (press Enter) if unknown.")
    heart_rate = prompt_float("Heart rate: ")
    weight = prompt_float("Weight (in kg): ")
    age = prompt_float("Age (in years): ")
    kcal_per_min = prompt_float("Kcal per minute: ")

    values = {
        "heart_rate": heart_rate,
        "weight": weight,
        "age": age,
        "kcal_per_min": kcal_per_min,
    }
    missing = [k for k, v in values.items() if v is None]
    if len(missing) != 1:
        print("Error: Exactly one value must be missing.")
        return

    missing_var = missing[0]
    if missing_var == "kcal_per_min":
        kcal_per_min = calculate_kcal_per_min(heart_rate, weight, age)
        print(f"Calculated kcal per minute: {kcal_per_min:.4f}")
    elif missing_var == "heart_rate":
        heart_rate = calculate_heart_rate(kcal_per_min, weight, age)
        print(f"Calculated heart rate: {heart_rate:.4f}")
    elif missing_var == "weight":
        weight = calculate_weight(kcal_per_min, heart_rate, age)
        print(f"Calculated weight (kg): {weight:.4f}")
    elif missing_var == "age":
        age = calculate_age(kcal_per_min, heart_rate, weight)
        print(f"Calculated age (years): {age:.4f}")

if __name__ == "__main__":
    main()
