
TEMP_CRITICAL_THRESHOLD = 65

def check_critical_conditions(smart_data: list[dict]):
    # TODO
    for disk in smart_data:
        temp = disk.get("temp")
        if isinstance(temp, int) and temp >= TEMP_CRITICAL_THRESHOLD:
            print(f"!!! CRITICAL TEMP ALERT: {disk['dev']} is {temp}°C. Shutting down...")
            # os.system("shutdown -h now")
            pass
