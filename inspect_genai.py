
try:
    from google.genai import types
    print("Types available:", dir(types))
    if hasattr(types, "Modality"):
        print("Modality Enum:", dir(types.Modality))
    else:
        print("No Modality enum found in types.")
    
    # Check if there are other relevant enums
    for x in dir(types):
        if "Modality" in x:
            print(f"Found {x}")
            
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
