import json
import os
import hashlib
import subprocess
import urllib.request

def _parse_args(_args, _arg_values, _arg_rules):
    _args_list = []
    for _arg in _args:
        #print(_arg)
        if isinstance(_arg, dict):
            _rules = _arg.get("rules")
            _allow = True
            if _rules is not None:
                _conditions = []
                for _rule in _rules:
                    for k1, v1 in _rule.items():
                        if k1 != "action":
                            for k2, v2 in v1.items():
                                _v1 = _arg_rules.get(k1)
                                if _v1 is not None:
                                    _v2 = _v1.get(k2)
                                    if _v2 is not None:
                                        _conditions.append(v2 == _v2)

                for _condition in _conditions:
                    if not _condition:
                        _allow = False
                        break

            _value = _arg["value"]
            if _allow:
                if isinstance(_value, list):
                    _args_list += _value
                else:
                    _args_list.append(_value)
        elif isinstance(_arg, list):
            _args_list += _arg
        else:
            _args_list.append(_arg)

    _args_ret = []
    for _arg in _args_list:
        _argument = _arg
        for k, v in _arg_values.items():
            _argument = _argument.replace("${" + k + "}", v)
        _args_ret.append(_argument)

    return _args_ret


def _download(_url, _libpath, _sha1hash):
    print("Downloading from", _url)
    urllib.request.urlretrieve(_url, _libpath)

    # Check SHA1 hash
    sha1 = hashlib.sha1()
    with open(_libpath, 'rb') as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            sha1.update(data)
    if sha1.hexdigest() != _sha1hash:
        raise Exception("Fatal: Library could not download correctly due to incorrect SHA-1 hash.")


def _parse_libs(_libs, _arg_values, _arg_rules):
    _classpath = ""
    for _lib in _libs:
        _libpath = os.path.join(_arg_values['game_directory'], "libraries", _lib['downloads']['artifact']['path'])
        _sha1hash = _lib['downloads']['artifact']['sha1']
        if os.path.exists(_libpath):
            sha1 = hashlib.sha1()
            with open(_libpath, 'rb') as f:
                while True:
                    data = f.read(65536)
                    if not data:
                        break
                    sha1.update(data)
            if sha1.hexdigest() != _sha1hash:
                print("SHA-1 hash does not match for", _lib['downloads']['artifact']['path'] + ". Redownloading...")
                _download(_lib['downloads']['artifact']['url'], _libpath, _sha1hash)
        else:
            print("Could not find library", _lib['downloads']['artifact']['path'] + ". Downloading...")
            _download(_lib['downloads']['artifact']['url'], _libpath, _sha1hash)

        _rules = _lib.get("rules")
        if _rules is not None:
            for _rule in _rules:
                if _rule["action"] == "allow" and _rule["os"]["name"] == _arg_rules["os"]["name"]:
                    _classpath += _libpath + ";"
        else:
            _classpath += _libpath + ";"
    _classpath += _arg_values['game_directory'] + f"/versions/{_arg_values['version_name']}/{_arg_values['version_name']}.jar"
    return _classpath


def launch(arg_values, jvm_args, rules, wait):
    verjson = arg_values['game_directory'] + f"/versions/{arg_values['version_name']}/{arg_values['version_name']}.json"
    with open(verjson, "r") as j:
        argj = json.load(j)

    sha1 = hashlib.sha1()
    with open(arg_values['game_directory'] + f"/versions/{arg_values['version_name']}/{arg_values['version_name']}.jar", 'rb') as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            sha1.update(data)

    arg_values["assets_root"] = f"{arg_values['game_directory']}/assets"
    arg_values["assets_index_name"] = argj["assetIndex"]["id"]
    arg_values["natives_directory"] = f"{arg_values['game_directory']}/bin/tinylauncher_{sha1.hexdigest()}"
    arg_values["version_type"] = argj["type"]

    arg_values['classpath'] = _parse_libs(argj["libraries"], arg_values, rules)

    args = [arg_values['java_runtime']]
    args += _parse_args(argj["arguments"]["jvm"], arg_values, rules)
    args += jvm_args
    args.append(argj["mainClass"])
    args += _parse_args(argj["arguments"]["game"], arg_values, rules)
    proc = subprocess.Popen(args, cwd=arg_values['game_directory'])
    if wait:
        proc.wait()
