import google.generativeai as genai
import pprint

print("--- Inspecting google.generativeai module ---")
print(dir(genai))

print("\n--- Inspecting google.generativeai.types ---")
try:
    import google.generativeai.types as types
    print(dir(types))
except ImportError:
    print("Could not import types")
