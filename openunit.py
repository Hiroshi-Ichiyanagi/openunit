#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
openunit -- deprecated name of the Worldyard engine (compatibility shim).

The project formerly called openunit is now Worldyard; the engine lives in
`worldyard.py`. This module keeps old code working:

    import openunit              # DeprecationWarning; returns the worldyard
    openunit.build_artifact(...) # module itself: same functions, same
                                 # constants, same bytes and hashes

`python3 openunit.py [spec.json]` still runs the demo. New code should
`import worldyard`.
"""

import sys
import warnings

import worldyard as _worldyard

_MESSAGE = ("the 'openunit' module is deprecated: the project is now Worldyard; "
            "use 'import worldyard' (same API, same hashes)")

if __name__ == "__main__":
    warnings.warn(_MESSAGE, DeprecationWarning, stacklevel=1)
    _worldyard._demo(sys.argv[1] if len(sys.argv) > 1 else "sample_input.json")
else:
    warnings.warn(_MESSAGE, DeprecationWarning, stacklevel=2)
    # `import openunit` binds the worldyard module object itself, so every
    # attribute (private ones included) is the same object under both names.
    sys.modules[__name__] = _worldyard
