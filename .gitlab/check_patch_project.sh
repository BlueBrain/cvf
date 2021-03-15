#!/usr/bin/bash

sed_apply() (
    f=$1
    sedexp=$2
    echo "PATCHING $f with '$sedexp'"
    (cd $(dirname $f) && git checkout "$(basename $f)") && sed -i "$sedexp" "$f"
    grep 'version(' "$f"
)

projname="$1"
branch="$2"
if [ "$branch" ]; then
    pkg_file="$PKGS_BASE/$projname/package.py"
    sedexp='/version.*tag=/d'  # Drop tags
    sedexp="$sedexp; s#branch=[^,]*,#branch='${branch}', preferred=True,#g" # Replace package branch
    sedexp="$sedexp; s#branch=[^,)]*)#branch='${branch}', preferred=True)#g"
    sed_apply "$pkg_file" "$sedexp"
fi
