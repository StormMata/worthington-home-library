#!/bin/zsh
cd "${0:A:h}"
python3 -c 'import app; app.init_db(); result = app.build_public_site(); print("Public catalogue generated with {} items in {}".format(result["items"], result["path"]))'
