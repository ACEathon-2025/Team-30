from .predictor import predict_green_time

def calculate_optimized_timing(ns_count, ew_count):
    try:
        ns_time = predict_green_time(ns_count)
        ew_time = predict_green_time(ew_count)
        return {"ns_time": ns_time, "ew_time": ew_time}
    except Exception as e:
        print(f"⚠️ Error in calculate_optimized_timing: {e}. Using fallback timings.")
        return {"ns_time": 10, "ew_time": 20}
