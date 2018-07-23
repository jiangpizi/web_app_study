PROJ_DIR=`pwd`
VENV=${PROJ_DIR}/.env
PROJ_NAME=webapp

if [ ! -e ${VENV} ];then
    virtualenv --prompt "(${PROJ_NAME})" ${VENV} -p $(type -p python2.7)
fi

source ${VENV}/bin/activate

#export PYTHONPATH=${PROJ_DIR}/server:${PROJ_DIR}/modules:${PROJ_DIR}/draco:${PROJ_DIR}:$HOME/lib
export PROJ_DIR
export PROJ_NAME
