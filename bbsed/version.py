import os

VERSION = "0.0.1"
REVISION = None


def _set_revision():
    global REVISION

    rev_dir = os.path.dirname(os.path.abspath(__file__))
    rev_path = os.path.join(rev_dir, "revision.txt")

    if os.path.exists(rev_path):
        with open(rev_path, "r") as rev_fp:
            REVISION = rev_fp.read()


_set_revision()
