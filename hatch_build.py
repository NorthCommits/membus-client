import sys
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def finalize(self, version, build_data, artifact_path):
        sys.stderr.write("\n")
        sys.stderr.write("  +---------------------------------------------+\n")
        sys.stderr.write("  |  membus installed successfully!              |\n")
        sys.stderr.write("  |                                             |\n")
        sys.stderr.write("  |  Type  membus  to open the quick guide      |\n")
        sys.stderr.write("  +---------------------------------------------+\n")
        sys.stderr.write("\n")
