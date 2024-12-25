from miniros.source import Server
from argparse import ArgumentParser
import time
import os
import logging
import shutil
import colorama

colorama.init(autoreset=True)
logging.basicConfig(level=logging.INFO, format=colorama.Style.BRIGHT + colorama.Fore.BLUE + "%(asctime)s - %(levelname)s - %(message)s")

parser = ArgumentParser()
parser.add_argument("package", type=str, nargs="?", choices=["build", "install", "uninstall", "create", "delete", "run"], default=None, help="Package mode")
parser.add_argument("package_name", type=str, nargs="?", default=None, help="Package name")

pack_group = parser.add_argument_group("package")
pack_group.add_argument("--author", type=str, default="Some Author", help="Package authors", metavar="<str>")
pack_group.add_argument("--description", type=str, default="MiniROS Package", help="Package description", metavar="<str>")
pack_group.add_argument("--version", type=str, default="1.0.0", help="Package version", metavar="<str>")
pack_group.add_argument("--email", type=str, default="author@example.com", help="Author email", metavar="<str>")
pack_group.add_argument("--force", action="store_true", default=False, help="Force package creation")
pack_group.add_argument("--args", nargs="+", type=str, default="", help="Package arguments", metavar="<str>")

parser.add_argument("--secure", action="store_true", default=False, help="Enable secure mode")
parser.add_argument("--port", type=int, default=4532, help="Port number to use", metavar="<int>")

args = parser.parse_args()

DEFAULT_LICENSE = "CHANGE ME"
DEFAULT_README = "CHANGE ME"
DEFAULT_PYPROJECT = """
[project]
name = "%(name)s"
version = "%(version)s"
authors = [
    { name = "%(author_name)s", email = "%(email)s" }
]
description = "%(description)s"
readme = "README.md"
requires-python = ">=3.7"
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: None",
    "Operating System :: OS Independent",
]
"""

def search_for_package(package_name: str):
    if not os.path.exists("./src"):
        return False
    
    d = os.listdir("./src/")
    for x in d:
        if x == package_name:
            return True
    return False

def install(package_name):
    if not os.path.exists("src/%s/dist" % package_name):
        logging.warning("Package is not built. Build it now?")

        while (create_or_not := input(": Do you want to continue? (y/n) ")) not in ["y", "n"]:
            continue

        if create_or_not == "n":
            quit(0)

        build(package_name)


    whl = ""
    directory = os.listdir("./src/%s/dist" % package_name)
    for x in directory:
        if x.endswith(".whl"):
            whl = x

    if whl == "":
        logging.error("Failed to install package")
        return False

    os.system("pip install ./src/%s/dist/%s --force-reinstall" % (package_name, whl))
    os.system("cd ..")

    return True
        
def build(package_name: str):
    c = os.system("cd src/%s && python -m build && cd .." % package_name)

    if c != 0:
        logging.error("Failed to build package")
        quit(1)

    logging.info("Package built successfully")

if args.package:
    if not args.package_name:
        parser.error("Argument package_name is required")

    match args.package:
        case "run":
            if not search_for_package(args.package_name):
                parser.error("Package not found")
            else:
                logging.info("Running package...")
                os.system("python -m %s %s" % (args.package_name, " ".join(args.args)))

        case "delete":
            if not search_for_package(args.package_name):
                parser.error("Package not found")
            else:
                logging.info("Deleting package...")
                shutil.rmtree("./src/%s" % args.package_name)
                os.system("pip uninstall %s" % args.package_name)
        
        case "build":
            if not search_for_package(args.package_name):
                parser.error("Package not found")
            else:
                logging.info("Building package...")

                build(args.package_name)

        case "uninstall":
            if not search_for_package(args.package_name):
                parser.error("Package not found")
            else:
                logging.info("Uninstalling package...")
                os.system("pip uninstall %s" % args.package_name)

        case "install":
            if args.package_name == "all":
                success = 0
                for x in os.listdir("./src"):
                    try:
                        if not install(x):
                            logging.warning("Failed to install package %s" % x)
                        else:
                            success += 1
                    except:
                        pass

                logging.info("Successfully installed %d packages" % success)
                quit(0)

            if not search_for_package(args.package_name):
                parser.error("Package not found")
            else:
                logging.info("Installing package...")

                if not install(args.package_name):
                    logging.warning("Failed to install package %s" % args.package_name)
                    quit(1)

                logging.info("Package %s installed successfully" % args.package_name)

        case "create":
            if search_for_package(args.package_name) and not args.force:
                parser.error("Package already exists")
                logging.info("If you want to recreate this package, run `miniros create --force %s`" % args.package_name)
            else:
                if search_for_package(args.package_name) and args.force:
                    while (create_or_not := input(": Program will recreate package in ./src/%s\nDo you want to continue (all data will be lost)? (y/n) " % args.package_name)) not in ["y", "n"]:
                            continue

                    if create_or_not == "n":
                        quit(0)

                    shutil.rmtree("./src/%s" % args.package_name)

                else:
                    while (create_or_not := input(": Program will create package in ./src/%s\nDo you want to continue? (y/n) " % args.package_name)) not in ["y", "n"]:
                        continue

                    if create_or_not == "n":
                        quit(0)

                logging.info("Creating package...")

                if not os.path.exists("./src"):
                    os.mkdir("./src")

                if not os.path.exists("./src/%s" % args.package_name):
                    os.mkdir("./src/%s" % args.package_name)

                if not os.path.exists("./src/%s/src" % args.package_name):
                    os.mkdir("./src/%s/src" % args.package_name)

                if not os.path.exists("./src/%s/src/%s" % (args.package_name, args.package_name)):
                    os.mkdir("./src/%s/src/%s" % (args.package_name, args.package_name))


                with open(f"./src/{args.package_name}/src/{args.package_name}/__init__.py", "w") as f:
                    f.write("")

                with open(f"./src/{args.package_name}/src/{args.package_name}/__init__.py", "w") as f:
                    f.write("")

                with open(f"./src/{args.package_name}/src/{args.package_name}/__main__.py", "w") as f:
                    f.write("# put code here to run it like MiniROS package")

                with open(f"./src/{args.package_name}/README.md", "w") as f:
                    f.write(DEFAULT_README)

                with open(f"./src/{args.package_name}/pyproject.toml", "w") as f:
                    f.write(DEFAULT_PYPROJECT % {"name": args.package_name, "version": args.version, "author_name": args.author, "email": args.email, "description": args.description})
                
                with open(f"./src/{args.package_name}/LICENSE", "w") as f:
                    f.write(DEFAULT_LICENSE)

                with open(f"./src/{args.package_name}/src/{args.package_name}/source.py", "w") as f:
                    f.write("# put your source code here")
                    f.write("# you can delete this file and replace it with your own, but")
                    f.write("# it`s NOT recommended")

                with open(f"./src/{args.package_name}/src/{args.package_name}/datatypes.py", "w") as f:
                    f.write("# put your datatypes here (Packets)")
                    f.write("# you can delete this file and replace it with your own, but")
                    f.write("# it`s NOT recommended")

                logging.info("Created package in ./src/%s" % args.package_name)
                logging.info("")
                logging.info("Put your package code in ./src/%s/src/%s/source.py" % (args.package_name, args.package_name))
                logging.info("Put your packets in ./src/%s/src/%s/datatypes.py" % (args.package_name, args.package_name))
                logging.info("Put your runnable code in ./src/%s/src/%s/__main__.py" % (args.package_name, args.package_name))
                logging.info("")
                logging.info("Don`t forget to change README.md and LICENSE for your own needs.")

    quit(0)


server = Server(args.port, args.secure)
server.logger.info("Running...")
server.run()

try:
    while True:
        time.sleep(1)
except:
    quit(0)