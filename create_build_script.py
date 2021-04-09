import sys
import re


filename = sys.argv[1]

abs_path_getter = """import sys, os
if hasattr(sys, '_MEIPASS'):
    ap = sys._MEIPASS
else:
    ap = os.path.abspath(".")"""


with open(filename) as file_in:
    initial_script = file_in.read()
    modified_script = re.sub(r"os\.path\.join\(", "os.path.join(ap, ", initial_script)
    new_script = f"{abs_path_getter}\n{modified_script}"
with open("main_build.py", "w") as file_out:
    file_out.write(new_script)
