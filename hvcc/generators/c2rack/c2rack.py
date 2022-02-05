# import datetime
import hashlib
import os
import shutil
import time
import jinja2
import json

import hvcc.core.hv2ir.HeavyLangObject as HeavyLangObject
from ..buildjson import buildjson
from ..copyright import copyright_manager


heavy_hash = HeavyLangObject.HeavyLangObject.get_hash


class c2rack:
    """ Generates a VCV Rack wrapper for a given patch.
    """

    @classmethod
    def filter_uniqueid(clazz, s):
        """ Return a unique id (in hexadecimal) for the Plugin interface.
        """
        s = hashlib.md5(s.encode('utf-8'))
        s = s.hexdigest().upper()[0:8]
        s = f"0x{s}"
        return s

    @classmethod
    def nonraw_receivers(clazz, old_receiver_list):
        # remove raw receivers
        receiver_list = []
        for k, v in old_receiver_list:
            if 'raw' in v['attributes']:
                # receiver_list.pop(k)
                pass
            else:
                receiver_list.append((k, v))
        return receiver_list

    @classmethod
    def make_jdata(clazz, patch_ir):
        jdata = list()

        with open(patch_ir, mode="r") as f:
            ir = json.load(f)

            for name, v in ir['control']['receivers'].items():
                # skip __hv_init and similar
                if name.startswith("__"):
                    continue

                # If a name has been specified
                if v['attributes'].get('raw'):
                    key = v['attributes']['raw']
                    jdata.append((key, name, 'RECV', f"0x{heavy_hash(name)}",
                                  v['attributes']['min'],
                                  v['attributes']['max'],
                                  v['attributes']['default']))

                elif name.startswith('Channel-'):
                    key = name.split('Channel-', 1)[1]
                    jdata.append((key, name, 'RECV', f"0x{heavy_hash(name)}",
                                  0, 1, None))

            for k, v in ir['objects'].items():
                try:
                    if v['type'] == '__send':
                        name = v['args']['name']
                        if v['args']['attributes'].get('raw'):
                            key = v['args']['attributes']['raw']
                            jdata.append((key, f'{name}>', 'SEND', f"0x{heavy_hash(name)}",
                                          v['args']['attributes']['min'],
                                          v['args']['attributes']['max'],
                                          v['args']['attributes']['default']))
                        elif name.startswith('Channel-'):
                            key = name.split('Channel-', 1)[1]
                            jdata.append((key, f'{name}>', 'SEND', f"0x{heavy_hash(name)}",
                                          0, 1, None))
                except Exception:
                    pass

            return jdata

    @classmethod
    def compile(clazz, c_src_dir, out_dir, externs, patch_name=None, patch_meta: dict = None,
                num_input_channels=0, num_output_channels=0, copyright=None, verbose=False):

        tick = time.time()

        receiver_list = c2rack.nonraw_receivers(externs['parameters']['in'])

        if patch_meta:
            patch_name = patch_meta.get("name", patch_name)
            rack_meta = patch_meta.get("rack", {})
        else:
            rack_meta = {}
        rack_project = rack_meta.get('project')

        copyright_c = copyright_manager.get_copyright_for_c(copyright)
        # copyright_plist = copyright or u"Copyright {0} Enzien Audio, Ltd." \
        #     " All Rights Reserved.".format(datetime.datetime.now().year)

        try:
            # ensure that the output directory does not exist
            out_dir = os.path.abspath(out_dir)
            if os.path.exists(out_dir):
                shutil.rmtree(out_dir)

            # copy over static files
            # shutil.copytree(os.path.join(os.path.dirname(__file__), "static"), out_dir)

            if rack_project:
                shutil.copy(os.path.join(os.path.dirname(__file__), "static/README.md"), f'{out_dir}/../')

            # copy over generated C source files
            source_dir = os.path.join(out_dir, "source")
            shutil.copytree(c_src_dir, source_dir)

            # initialize the jinja template environment
            env = jinja2.Environment()
            env.filters["uniqueid"] = c2rack.filter_uniqueid

            env.loader = jinja2.FileSystemLoader(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"))

            # construct jdata from ir
            ir_dir = os.path.join(c_src_dir, "../ir")
            patch_ir = os.path.join(ir_dir, f"{patch_name}.heavy.ir.json")
            jdata = c2rack.make_jdata(patch_ir)

            # generate DPF wrapper from template
            plugin_hpp_path = os.path.join(source_dir, "plugin.hpp")
            with open(plugin_hpp_path, "w") as f:
                f.write(env.get_template("plugin.hpp").render(
                    jdata=jdata,
                    name=patch_name,
                    meta=rack_meta,
                    class_name=f"HeavyRack_{patch_name}",
                    num_input_channels=num_input_channels,
                    num_output_channels=num_output_channels,
                    receivers=receiver_list,
                    copyright=copyright_c))
            plugin_cpp_path = os.path.join(source_dir, "plugin.cpp")
            with open(plugin_cpp_path, "w") as f:
                f.write(env.get_template("plugin.cpp").render(
                    jdata=jdata,
                    name=patch_name,
                    meta=rack_meta,
                    class_name=f"HeavyRack_{patch_name}",
                    num_input_channels=num_input_channels,
                    num_output_channels=num_output_channels,
                    receivers=receiver_list,
                    pool_sizes_kb=externs["memoryPoolSizesKb"],
                    copyright=copyright_c))
            model_cpp_path = os.path.join(source_dir, f"HeavyRack_{patch_name}.cpp")
            with open(model_cpp_path, "w") as f:
                f.write(env.get_template("model.cpp").render(
                    jdata=jdata,
                    name=patch_name,
                    meta=rack_meta,
                    class_name=f"HeavyRack_{patch_name}",
                    num_input_channels=num_input_channels,
                    num_output_channels=num_output_channels,
                    receivers=receiver_list,
                    pool_sizes_kb=externs["memoryPoolSizesKb"],
                    copyright=copyright_c))
            # rack_h_path = os.path.join(source_dir, "DistrhoPluginInfo.h")
            # with open(rack_h_path, "w") as f:
            #     f.write(env.get_template("DistrhoPluginInfo.h").render(
            #         name=patch_name,
            #         meta=rack_meta,
            #         class_name=f"HeavyDPF_{patch_name}",
            #         num_input_channels=num_input_channels,
            #         num_output_channels=num_output_channels,
            #         receivers=receiver_list,
            #         pool_sizes_kb=externs["memoryPoolSizesKb"],
            #         copyright=copyright_c))

            # generate list of Heavy source files
            # files = os.listdir(source_dir)

            # ======================================================================================
            # Linux

            # plugin makefile
            with open(os.path.join(source_dir, "Makefile"), "w") as f:
                f.write(env.get_template("Makefile").render(
                    name=patch_name,
                    meta=rack_meta))

            with open(os.path.join(source_dir, "plugin.json"), "w") as f:
                f.write(env.get_template("plugin.json").render(
                    name=patch_name,
                    meta=rack_meta))

            # project makefile
            if rack_project:
                with open(os.path.join(source_dir, "../../Makefile"), "w") as f:
                    f.write(env.get_template("Makefile.project").render(
                        name=patch_name,
                        meta=rack_meta))

            buildjson.generate_json(
                out_dir,
                linux_x64_args=["-j"])
            # macos_x64_args=["-project", "{0}.xcodeproj".format(patch_name), "-arch",
            #                 "x86_64", "-alltargets"],
            # win_x64_args=["/property:Configuration=Release", "/property:Platform=x64",
            #               "/t:Rebuild", "{0}.sln".format(patch_name), "/m"],
            # win_x86_args=["/property:Configuration=Release", "/property:Platform=x86",
            #               "/t:Rebuild", "{0}.sln".format(patch_name), "/m"])

            return {
                "stage": "c2rack",
                "notifs": {
                    "has_error": False,
                    "exception": None,
                    "warnings": [],
                    "errors": []
                },
                "in_dir": c_src_dir,
                "in_file": "",
                "out_dir": out_dir,
                "out_file": os.path.basename(plugin_hpp_path),
                "compile_time": time.time() - tick
            }

        except Exception as e:
            return {
                "stage": "c2rack",
                "notifs": {
                    "has_error": True,
                    "exception": e,
                    "warnings": [],
                    "errors": [{
                        "enum": -1,
                        "message": str(e)
                    }]
                },
                "in_dir": c_src_dir,
                "in_file": "",
                "out_dir": out_dir,
                "out_file": "",
                "compile_time": time.time() - tick
            }
