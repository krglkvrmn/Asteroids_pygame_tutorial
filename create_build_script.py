import argparse
import re

parser = argparse.ArgumentParser()
parser.add_argument("filename", type=str)
parser.add_argument("--output", "-o", type=str, required=True)
args = parser.parse_args()


abs_path_getter = """import sys, os
if hasattr(sys, '_MEIPASS'):
    ap = sys._MEIPASS
else:
    ap = os.path.abspath(".")"""


with open(args.filename) as file_in:
    initial_script = file_in.read()
    modified_script = re.sub(r"os\.path\.join\(", "os.path.join(ap, ", initial_script)
    new_script = f"{abs_path_getter}\n{modified_script}"

with open(args.output, "w") as file_out:
    file_out.write(new_script)
