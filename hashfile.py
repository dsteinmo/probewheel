#copied from: https://github.com/pypa/auditwheel/blob/2d9bb0b3b0742f5fc6000d56cb7d65a6e6dc5567/auditwheel/hashfile.py    
import hashlib

def hashfile(afile, blocksize=65536):
    """Hash the contents of an open file handle with SHA256"""
    hasher = hashlib.sha256()
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    return hasher.hexdigest()