import pefile
import os, sys
import shutil
import re
import subprocess
import platform
from machomachomangler.pe import redll
from hashfile import hashfile

def get_dll_deps(filepath):

    lib = pefile.PE(filepath)
    d = lib.dump_dict()

    if 'Imported symbols' not in d.keys():
        return []
    symbols = []

    #accumulate all imported symbols
    for sym in d['Imported symbols']:
        symbols += sym
    
    
    dlls = set(map(lambda x: x['DLL'].decode('utf-8') if 'DLL' in x.keys() else None, symbols))
    
    ret =[]
    for dll in dlls:
        if dll is None or re.search('(api-ms-win-core.+\.dll|KERNEL32.dll|KERNELBASE.dll|ntdll.dllUSER32.dll|SECHOST.dll)$', dll):
            continue
        ret.append(dll)

    print({filepath: ret})
    return ret


def get_dll_deps_recursive(filepath, search_paths, scanned_files=[]):
    if filepath is None or filepath in scanned_files:
        return []
    if re.search('(api-ms-win-.+\.dll|KERNEL32.dll|KERNELBASE.dll|ntdll.dll|USER32.dll|SECHOST.dll)$', filepath):
        return []

    deps = get_dll_deps(filepath)
    scanned_files.append(filepath)
    subdeps = []
    for dll in [d for d in deps if d is not None]:
        if dll in subdeps:
            continue
        if re.search('(api-ms-win-.+\.dll|KERNEL32.dll|KERNELBASE.dll|ntdll.dll|USER32.dll|SECHOST.dll)$', dll):
            continue

        dllpath = resolve_dll_path(dll, search_paths)
        subdeps += get_dll_deps_recursive(dllpath, search_paths, scanned_files)

    return [dll for dll in deps + subdeps if dll is not None]

def get_dll_search_paths():
    winpath = os.environ['WINDIR']
    syspath = winpath
    if platform.architecture()[0] == '64bit':
        syspath+= '\\System32\\'
    else:
        syspath+= '\\SysWOW64\\'
        
    search_paths = []
    search_paths.append(os.path.dirname(os.path.abspath(__file__)))
    search_paths.append(os.getcwd())
    search_paths.append(syspath)
    search_paths.append(winpath)
    for path in os.environ['PATH'].split(";"):
        search_paths.append(path)

    return search_paths

def resolve_dll_path(dll_name, search_paths):
    for path in search_paths:
        files = []
        try:
            files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))] 
        except Exception as err:
            # This most likely means the user has a PATH entry that no longer exists
            # so we probably don't care about this folder and can go onto the next 
            # folder in search_paths.
            #print(str(err))
            continue

        if dll_name.lower() in list(map(lambda x: x.lower(), files)):
            return os.path.join(path, dll_name)


if __name__=='__main__':
    myarg = os.path.normpath("C:\\dev\\blitzdg\\bin\\Release\\pyblitzdg.pyd")
    base_path = os.path.dirname(myarg)
    base_lib = os.path.basename(myarg)
    
    search_paths = get_dll_search_paths()
    search_paths.append(str(base_path))
    dlls = get_dll_deps_recursive(myarg, search_paths)

    print("done recursive scan.")

    dest_folder = os.path.join(base_path, "_libs")
    if not os.path.exists(dest_folder):
        os.mkdir(dest_folder)
    deps = {}
    manglermap = {}

    # whitelist of system dll's, not to be bundled.
    whitelist = set(["advapi32.dll","gdi32.dll","psapi.dll","rpcrt4.dll","shlwapi.dll","version.dll","ws2_32.dll","kernel32.dll", "python37.dll",
        "kernelbase.dll","ntdll.dll","user32.dll","sechost.dll", "msvcp120.dll", "msvcp140.dll", "vcruntime140.dll", "msvcrt.dll", "msvcr120.dll",
        "ucrtbased.dll", "msvcp140d.dll", "vcruntime140d.dll", "libgfortran-3.dll", "libgcc_s_seh-1"])
    for dll in set(dlls):
        dll_lower = dll.lower()
        if re.search('api-ms-win-.+\.dll$', dll_lower) or dll_lower in whitelist:
            continue
        dll_path = resolve_dll_path(dll, search_paths)
        deps[dll] = dll_path

        # this assumes ".dll" does not appear earlier in the filename than the extension.
        splitdll = dll_lower.split(".dll")

        with open(dll_path, 'rb') as f:
            sha256 = hashfile(f)
        destdllname = "".join(["".join(splitdll[:-1]), "-", sha256[:8], ".dll"])
        dest_path = os.path.join(dest_folder, destdllname)
        manglermap[bytes(dll,'utf-8')] = bytes(destdllname,'utf-8')

        print("copying from: ", dll_path, " to ", dest_path)
        if not os.path.exists(dest_path):
            shutil.copy(dll_path, dest_path)

    # copy in the module (base library)
    shutil.copy(myarg, os.path.join(dest_folder, base_lib))

    for lib in [os.path.join(dest_folder, f) for f in os.listdir(dest_folder) if os.path.isfile(os.path.join(dest_folder, f))]:
        if re.search(".+\.py$", lib):
            continue
        print("patching symbols in file: ", lib)

        #returned_val = 0
        #if not re.search("pyblitzdg\.pyd", lib):
        #    returned_val = subprocess.call("C:\\mingw64\\bin\\strip.exe " + lib, shell=False)
        #print("strip returned: " + str(returned_val))
        buf = None
        with open(lib, "rb") as f:
            buf = f.read()

        try:
            new_buf = redll(buf, manglermap)
        except ValueError as ve:
            print(ve)
            continue

        with open(lib, "wb") as f:
            f.write(new_buf)

    print(deps)
  