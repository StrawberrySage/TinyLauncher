import sys

from launch import launch
import os
import json


def main(_argv):
    _argc = len(_argv)
    if _argc == 1:
        print("Usage:   tl-cli launch <profile> <auth>")
        print("         tl-cli launch <profile> <auth> <fork (true, [false])>")
        print("Example: tl-cli profile.json auth.json")
        return

    if _argv[1] == "launch":
        if _argc < 4:
            print("Usage:   tl-cli launch <profile> <auth>")
            print("         tl-cli launch <profile> <auth> <fork (true, [false])>")
            print("Example: tl-cli profile.json auth.json")
            return
        with open(_argv[2], "r") as f_profile:
            profile = json.load(f_profile)
        with open(_argv[3], "r") as f_auth:
            auth = json.load(f_auth)

        for k, v in profile["options"].items():
            profile["options"][k] = os.path.expandvars(v)

        arg_values = profile["options"] | auth
        jvm_args = profile["jvm_args"]
        rules = profile["rules"]

        wait = True
        if _argc > 4:
            fork = _argv[4].lower()
            if fork == "true" or fork == "t" or fork == "yes" or fork == "y" or fork == "1":
                wait = False

        launch(arg_values, jvm_args, rules, wait)
        print("Launching...")


if __name__ == "__main__":
    main(sys.argv)
