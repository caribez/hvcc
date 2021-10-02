# import datetime
import hashlib
import os
import shutil
import time
import jinja2
from ..buildjson import buildjson
from ..copyright import copyright_manager


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
    def compile(clazz, c_src_dir, out_dir, externs,
                patch_name=None, patch_meta: dict = None,
                num_input_channels=0, num_output_channels=0,
                copyright=None, verbose=False):

        tick = time.time()

        receiver_list = externs['parameters']['in']

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
            shutil.copytree(os.path.join(os.path.dirname(__file__), "static"), out_dir)

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

            # generate DPF wrapper from template
            rack_h_path = os.path.join(source_dir, f"HeavyRack_{patch_name}.hpp")
            with open(rack_h_path, "w") as f:
                f.write(env.get_template("plugin.hpp").render(
                    name=patch_name,
                    meta=rack_meta,
                    class_name=f"HeavyRack_{patch_name}",
                    num_input_channels=num_input_channels,
                    num_output_channels=num_output_channels,
                    receivers=receiver_list,
                    copyright=copyright_c))
            rack_cpp_path = os.path.join(source_dir, f"HeavyRack_{patch_name}.cpp")
            with open(rack_cpp_path, "w") as f:
                f.write(env.get_template("plugin.cpp").render(
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
                "out_file": os.path.basename(rack_h_path),
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
