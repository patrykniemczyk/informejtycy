# This file must be inside /server dictionary,
# otherwise python runned in docker raises an error.

IP: str = "0.0.0.0"
PORT: int = 5000
RECEIVED_DIR: str = "../received"
COMPILED_DIR: str = "../received/compiled"
# Secret key used by flask_socketio for security
SECRET_KEY: str = "gEe_5+aBG6;{4#X[bK^]k!w,mCLU-Mr"
# written here on purpose, don't think it's a mistake
RECEIVE_SUBMISSION_TIME: int = 10  # How much results stay on status/<auth>
# After what time will not pinged Debugger class be deleted
RECEIVE_DEBUG_PING_TIME: int = 15
# How often results from status/<auth> should be checked for possible cleaning
CLEANING_RESULTS_TIME: int = 3
# How often should Debugger classes be checked for possible cleaning
CLEANING_UNUSED_DBG_PROCESSES_TIME: int = 5
DOCKER_CPU_LIMIT: float = 1.5  # Amount of cores per container
