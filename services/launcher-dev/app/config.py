import os

if 'DEBUG' in os.environ and os.environ['DEBUG'] == 'True':
    DEBUG = True
    TESTING = True
else:
    DEBUG = False
    TESTING = False

########################
# Database configuration
########################

MYSQL_DATABASE = os.environ['MYSQL_DATABASE']
MYSQL_USER = os.environ['MYSQL_USER']
MYSQL_PASSWORD = os.environ['MYSQL_PASSWORD']
MYSQL_HOST = os.environ['MYSQL_HOST']
MYSQL_PORT = os.environ['MYSQL_PORT']
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://{0}:{1}@{2}:{3}/{4}'.format(
    MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE
)


###############################
# Challenge's related variables
###############################

CHALLENGE_MAX_SOURCE_SIZE_IN_MB = int(
    os.environ['CHALLENGE_MAX_SOURCE_SIZE_IN_MB'])
CHALLENGE_MAX_MEM_COMPILATION_IN_MB = int(
    os.environ['CHALLENGE_MAX_MEM_COMPILATION_IN_MB'])
CHALLENGE_MAX_TIME_COMPILATION_IN_SECS = int(
    os.environ['CHALLENGE_MAX_TIME_COMPILATION_IN_SECS'])
CHALLENGE_MAX_BINARY_SIZE_IN_MB = int(
    os.environ['CHALLENGE_MAX_BINARY_SIZE_IN_MB'])
CHALLENGE_MAX_MEM_EXECUTION_IN_MB = int(
    os.environ['CHALLENGE_MAX_MEM_EXECUTION_IN_MB'])
CHALLENGE_MAX_TIME_EXECUTION_IN_SECS = int(
    os.environ['CHALLENGE_MAX_TIME_EXECUTION_IN_SECS'])
CHALLENGE_NUMBER_OF_TEST_VECTORS = int(
    os.environ['CHALLENGE_NUMBER_OF_TEST_VECTORS'])

STARTING_DATE = int(os.environ['STARTING_DATE'])
POSTING_DEADLINE = int(os.environ['POSTING_DEADLINE'])
FINAL_DEADLINE = int(os.environ['FINAL_DEADLINE'])

CHALLENGE_TEST_EDGE_CASES = [
    0,
    2**256 - 1,
    0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551,  # n
]

#############
# Other stuff
#############

NAME_OF_COMPILE_AND_TEST_SERVICE = os.environ['NAME_OF_COMPILE_AND_TEST_SERVICE']
SOCK = os.environ['SOCK']
COMPILE_AND_TEST_SERVICE_NETWORK = os.environ['COMPILE_AND_TEST_SERVICE_NETWORK']
