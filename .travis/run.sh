#!/bin/bash -ex

if [[ "${TOXENV}" == "pypy" ]]; then
    PYENV_ROOT="$HOME/.pyenv"
    PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
fi
if [ -n "${LIBRESSL}" ]; then
    OPENSSL=$LIBRESSL
    export CFLAGS="-Werror -Wno-error=deprecated-declarations -Wno-error=discarded-qualifiers -Wno-error=unused-function"
fi

if [ -n "${OPENSSL}" ]; then
    OPENSSL_DIR="ossl-2/${OPENSSL}"

    export PATH="$HOME/$OPENSSL_DIR/bin:$PATH"
    export CFLAGS="${CFLAGS} -I$HOME/$OPENSSL_DIR/include"
    # rpath on linux will cause it to use an absolute path so we don't need to
    # do LD_LIBRARY_PATH
    export LDFLAGS="-L$HOME/$OPENSSL_DIR/lib -Wl,-rpath=$HOME/$OPENSSL_DIR/lib"
fi

source ~/.venv/bin/activate

if [ -n "${DOCKER}" ]; then
    # We will be able to drop the -u once we switch the default container user in the
    # dockerfiles.
    docker run --rm -u 2000:2000 \
        -v "${TRAVIS_BUILD_DIR}":"${TRAVIS_BUILD_DIR}" \
        -v "${HOME}/wycheproof":/wycheproof \
        -e TOXENV "${DOCKER}" \
        /bin/sh -c "cd ${TRAVIS_BUILD_DIR}; tox -- --wycheproof-root='/wycheproof'"
elif [ -n "${TOXENV}" ]; then
    tox -- --wycheproof-root="$HOME/wycheproof"
else
    downstream_script="${TRAVIS_BUILD_DIR}/.travis/downstream.d/${DOWNSTREAM}.sh"
    if [ ! -x "$downstream_script" ]; then
        exit 1
    fi
    $downstream_script install
    pip install .
    $downstream_script run
fi
