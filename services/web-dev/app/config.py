import os

if 'DEBUG' in os.environ and os.environ['DEBUG'] == 'True':
    DEBUG = True
    TESTING = True
    NBR_SECONDS_PER_DAY = int(os.environ['NBR_SECONDS_PER_DAY'])
else:
    DEBUG = False
    TESTING = False
    NBR_SECONDS_PER_DAY = 86400

####################
# CSRF configuration
####################

SECRET_KEY = os.environ['SECRET_KEY']
WTF_CSRF_ENABLED = True # activates the cross-site request forgery prevention in Flask-WTF

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
SQLALCHEMY_POOL_SIZE=0
UPLOAD_FOLDER = os.environ['UPLOAD_FOLDER']

###############################
# Challenge's related variables
###############################

CHALLENGE_MAX_SOURCE_SIZE_IN_MB = int(os.environ['CHALLENGE_MAX_SOURCE_SIZE_IN_MB'])
CHALLENGE_MAX_MEM_COMPILATION_IN_MB = int(os.environ['CHALLENGE_MAX_MEM_COMPILATION_IN_MB'])
CHALLENGE_MAX_TIME_COMPILATION_IN_SECS = int(os.environ['CHALLENGE_MAX_TIME_COMPILATION_IN_SECS'])
CHALLENGE_MAX_BINARY_SIZE_IN_MB = int(os.environ['CHALLENGE_MAX_BINARY_SIZE_IN_MB'])
CHALLENGE_MAX_MEM_EXECUTION_IN_MB = int(os.environ['CHALLENGE_MAX_MEM_EXECUTION_IN_MB'])
CHALLENGE_MAX_TIME_EXECUTION_IN_SECS = int(os.environ['CHALLENGE_MAX_TIME_EXECUTION_IN_SECS'])
CHALLENGE_NUMBER_OF_TEST_VECTORS = int(os.environ['CHALLENGE_NUMBER_OF_TEST_VECTORS'])
MAX_CONTENT_LENGTH = CHALLENGE_MAX_SOURCE_SIZE_IN_MB<<20

STARTING_DATE = int(os.environ['STARTING_DATE'])
POSTING_DEADLINE = int(os.environ['POSTING_DEADLINE'])
FINAL_DEADLINE = int(os.environ['FINAL_DEADLINE'])


#############
# Other stuff
#############

URL_COMPILE_AND_TEST = os.environ['URL_COMPILE_AND_TEST']

RECAPTCHA_PUBLIC_KEY = os.environ['RECAPTCHA_PUBLIC_KEY']
RECAPTCHA_PRIVATE_KEY = os.environ['RECAPTCHA_PRIVATE_KEY']
RECAPTCHA_PARAMETERS = {'hl': 'en'}

MAX_RANK_OF_PLOTED_CHALLENGES = 30
