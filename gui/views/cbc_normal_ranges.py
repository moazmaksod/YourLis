# Dictionary for normal ranges of CBC parameters based on age
# The ranges are hypothetical and should be replaced with actual clinical data

NORMAL_RANGES = {
    "Hemoglobin (HGB)": {
        "newborn": (14, 24),
        "infant": (10, 15),
        "child": (11, 16),
        "adult": (12, 18)
    },
    "Red Blood Cells (RBC)": {
        "newborn": (4.1, 6.1),
        "infant": (3.8, 5.5),
        "child": (4.1, 5.5),
        "adult": (4.2, 5.9)
    },
    "Hematocrit (HCT)": {
        "newborn": (42, 65),
        "infant": (33, 41),
        "child": (34, 43),
        "adult": (37, 52)
    },
    "White Blood Cells (WBC)": {
        "newborn": (9, 30),
        "infant": (6, 17.5),
        "child": (5, 14.5),
        "adult": (4.5, 11)
    },
    "Platelets (PLT)": {
        "newborn": (150, 450),
        "infant": (150, 450),
        "child": (150, 450),
        "adult": (150, 450)
    },
    "Mean Corpuscular Volume (MCV)": {
        "newborn": (95, 120),
        "infant": (70, 85),
        "child": (75, 87),
        "adult": (80, 100)
    },
    "Mean Corpuscular Hemoglobin (MCH)": {
        "newborn": (30, 37),
        "infant": (24, 30),
        "child": (25, 31),
        "adult": (27, 33)
    },
    "Mean Corpuscular Hemoglobin Concentration (MCHC)": {
        "newborn": (30, 36),
        "infant": (30, 36),
        "child": (32, 36),
        "adult": (33, 36)
    },
    "Red Cell Distribution Width (RDW)": {
        "newborn": (14, 20),
        "infant": (12, 16),
        "child": (11, 15),
        "adult": (11, 15)
    },
    "Plateletcrit (PCT)": {
        "newborn": (0.15, 0.45),
        "infant": (0.15, 0.45),
        "child": (0.15, 0.45),
        "adult": (0.15, 0.45)
    },
    "Mean Platelet Volume (MPV)": {
        "newborn": (7, 11),
        "infant": (7, 11),
        "child": (7, 11),
        "adult": (7, 11)
    },
    "Platelet Distribution Width (PDW)": {
        "newborn": (10, 18),
        "infant": (10, 18),
        "child": (10, 18),
        "adult": (10, 18)
    },
    "Neutrophils": {
        "newborn": (40, 80),
        "infant": (20, 50),
        "child": (30, 60),
        "adult": (40, 70)
    },
    "Lymphocytes": {
        "newborn": (20, 40),
        "infant": (40, 70),
        "child": (30, 50),
        "adult": (20, 40)
    },
    "Monocytes": {
        "newborn": (2, 12),
        "infant": (2, 10),
        "child": (2, 10),
        "adult": (2, 8)
    },
    "Eosinophils": {
        "newborn": (1, 4),
        "infant": (1, 4),
        "child": (1, 4),
        "adult": (1, 4)
    },
    "Basophils": {
        "newborn": (0, 1),
        "infant": (0, 1),
        "child": (0, 1),
        "adult": (0, 1)
    }
}

def get_normal_range(parameter, age_group):
    """
    Get the normal range for a given CBC parameter and age group.

    :param parameter: The CBC parameter (e.g., "Hemoglobin (HGB)").
    :param age_group: The age group (e.g., "adult", "child").
    :return: A tuple representing the normal range (min, max) or None if not found.
    """
    return NORMAL_RANGES.get(parameter, {}).get(age_group)

def determine_age_group(age, age_unit):
    """
    Determine the age group based on the age and age unit.

    :param age: The age as a number.
    :param age_unit: The unit of age (e.g., "days", "months", "years").
    :return: The age group (e.g., "newborn", "infant", "child", "adult").
    """
    if age_unit == "days" and age <= 28:
        return "newborn"
    elif age_unit == "months" and age <= 12:
        return "infant"
    elif age_unit == "years" and age < 18:
        return "child"
    else:
        return "adult"

def set_flag(value, parameter, age_group):
    """
    Set a flag for a given CBC parameter value to indicate if it is high or low.

    :param value: The measured value of the parameter.
    :param parameter: The CBC parameter (e.g., "Hemoglobin (HGB)").
    :param age_group: The age group (e.g., "adult", "child").
    :return: A string flag ("High", "Low", or "Normal").
    """
    normal_range = get_normal_range(parameter, age_group)
    if not normal_range:
        return "Unknown"  # Return "Unknown" if no range is defined

    FLAG_LOW_COL = "yellow700"
    FLAG_HIGH_COL = "red700"
    min_value, max_value = normal_range
    if value < min_value:
        return "L", FLAG_LOW_COL
    elif value > max_value:
        return "H", FLAG_HIGH_COL