import os
import glob

# Get the current directory of this file
current_dir = os.path.dirname(os.path.abspath(__file__))

# Get all .py files in the instruments directory
instrument_files = glob.glob(os.path.join(current_dir, "*.py"))
# print(instrument_files)
# Import all instrument files
for file in instrument_files:
    module_name = os.path.basename(file)[:-3]
    # print(module_name)
    if module_name != "__init__":
        __import__(f"instruments.{module_name}")