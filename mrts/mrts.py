#!/usr/bin/env python3

import argparse
import runpy
import shutil
import subprocess
import sys
from pathlib import Path

from path_utils import existing_directory, existing_file, path_within


def clean_generated_directories(genrules, gentests, verbose):
    old_rules = genrules.glob("*.conf")
    old_test = gentests.glob("*.yaml")
    for rule in old_rules:
        rule.unlink()
    for test in old_test:
        test.unlink()
    if verbose:
        print("Cleaned generated directories")


def generate_rules(testconfig, genrules, gentests, verbose):
    rule_definitions = sorted(testconfig.glob("*.yaml"))
    generate_rules_script = path_within(
        Path(__file__).resolve().parent,
        "generate-rules.py",
        "rule generator script",
    )

    genrule_stdout = sys.stdout if verbose else subprocess.DEVNULL
    subprocess.run(
        [
            sys.executable,
            str(generate_rules_script),
            "-r",
            *(str(definition) for definition in rule_definitions),
            "-e",
            str(genrules),
            "-t",
            str(gentests),
        ],
        check=True,
        stdout=genrule_stdout,
    )


def launch_albedo():
    if not shutil.which("albedo"):
        print("Failure: albedo not installed or found in system PATH")
        sys.exit(1)

    return subprocess.Popen(
        ["albedo", "-b", "127.0.0.1", "-p", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)


def execute_test_set(ftwconfig, infra, gentests, verbose):
    if not shutil.which("go-ftw"):
        print("Failure: go-ftw not installed or found in system PATH")
        sys.exit(1)

    if ftwconfig is None:
        ftwconfig = path_within(infra, "ftw.mrts.config.yaml", "go-ftw configuration")

    go_ftw = subprocess.Popen(
        ["go-ftw", "run", "--config", str(ftwconfig), "--dir", str(gentests), "--wait-for-expect-status-code", "200", "--fail-fast"],
        stdout=subprocess.PIPE
    )
    stdout = ""
    for line in go_ftw.stdout:
        stdout += line.decode("utf-8")
        if verbose:
            print(line.decode("utf-8"), end="")

    if '💥' in stdout:
        print("💥💥💥 Failure: test set failed")
    elif '🎉' in stdout:
        print("🎉🎉🎉 Success: test set passed")
    else:
        print("Failure: Incorrect go-ftw output")


def write_mrts_load(infra_path, genrules_path, verbose):
    load_file_path = path_within(infra_path, "mrts.load", "MRTS load file")
    with open(load_file_path, "w") as f:
        f.write(f"Include {genrules_path}\n")

    if verbose:
        print(f"File '{load_file_path}' created successfully with content: Include {genrules_path}")


def delete_mrts_load(infra_path, verbose):
    file_path = path_within(infra_path, "mrts.load", "MRTS load file")
    if file_path.exists():
        file_path.unlink()
        if verbose:
            print(f"File '{file_path}' has been deleted.")
    else:
        if verbose:
            print(f"File '{file_path}' does not exist.")


def main(infra, ftwconfig, testconfig, genrules, gentests, verbose, clean):
    project_root = existing_directory(Path(__file__).resolve().parent.parent, "MRTS project root")
    if existing_directory(".", "current working directory") != project_root:
        print("This script can only run from the MRTS root directory")
        sys.exit(1)

    infra = existing_directory(infra, "infrastructure")
    testconfig = existing_directory(testconfig, "rules definition directory")
    genrules = existing_directory(genrules, "rules export directory")
    gentests = existing_directory(gentests, "tests export directory")
    if ftwconfig is not None:
        ftwconfig = existing_file(ftwconfig, "go-ftw configuration")

    # Optionally, remove previous .conf and .yaml generated
    if clean:
        clean_generated_directories(genrules, gentests, verbose)

    # Step 1: generate rules and tests
    print("Generate rules and tests")
    generate_rules(testconfig, genrules, gentests, verbose)

    # Step 2: start backend
    print("Launch backend")
    backend = launch_albedo()

    # Step 3: create temporary file in infra to include rules, figuring out the absolute path dynamically
    infra_path = existing_directory(path_within(infra, "infra", "infrastructure state"), "infrastructure state")
    genrules_abs_path = str(genrules / "*.conf")
    write_mrts_load(infra_path, genrules_abs_path, verbose)

    # Step 4: launch infrastructure from start script
    print("Launch infrastructure")
    runpy.run_path(str(path_within(infra, "start.py", "infrastructure start script")))

    # Step 5: use go-ftw to run tests
    print("Executing test set...")
    execute_test_set(ftwconfig, infra, gentests, verbose)

    # Step 6: shutdown backend
    backend.terminate()
    print("Backend shutdown")

    # Step 7: remove temporary file including rules
    delete_mrts_load(infra_path, verbose)

    # Step 8: shutdown infrastructure from stop script
    runpy.run_path(str(path_within(infra, "stop.py", "infrastructure stop script")))
    print("Infrastructure shutdown")

    # The end
    print("MRTS completed")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="MRTS global utility")
    parser.add_argument("-i", "--infrastructure", metavar='/path/to/infra/', type=str,
                            help='Directory path to infrastructure to be tested', required=True)
    parser.add_argument("-r", "--rulesdef", metavar='/path/to/mrts/*.yaml', type=str,
                            help='Directory path to MRTS rules definition', required=True)
    parser.add_argument("-e", "--expdir", metavar='/path/to/mrts/rules/', type=str,
                            help='Directory path to generated MRTS rules', required=True)
    parser.add_argument("-t", "--testdir", metavar='/path/to/mrts/tests/', type=str,
                            help='Directory path to generated MRTS tests', required=True)
    parser.add_argument("-c", "--clean", action='store_true',
                            help='Clean generated rules and tests directories before new rule generation',
                            required=False, default=False)
    parser.add_argument("-f", "--ftwconfig", metavar='/path/to/mrts/ftw.mrts.config.yaml', type=str,
                            help='go-ftw config file', required=False, default=None)
    parser.add_argument("-v", "--verbose", action='store_true',
                            help='Verbose output', required=False, default=False)

    args = parser.parse_args()

    try:
        main(args.infrastructure, args.ftwconfig, args.rulesdef, args.expdir, args.testdir, args.verbose, args.clean)
    except ValueError as error:
        parser.error(str(error))
