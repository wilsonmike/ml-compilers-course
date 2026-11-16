def seconds_to_hms(seconds: int) -> str:
    hours = seconds // 3600
    minutes = seconds % 3600 // 60
    secs = seconds % 60
    return f"{hours}:{minutes:02}:{secs:02}"
