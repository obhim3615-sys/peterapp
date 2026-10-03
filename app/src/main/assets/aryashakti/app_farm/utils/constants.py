# REQUEST BODY CONSTANTS
EMPTY_REQ_BODY = 'Request body can not be empty! Mandatory fields are required!'
INVALID_BODY = 'Invalid request body! Please enter a valid request body!'
INVALID_ORG_ID = 'Invalid organization id! Please enter a valid organization id!'

# FARM CONSTANTS
FARM_CREATION_SUCCESS = 'Farm created successfully!'
FARM_CREATION_ERR = 'OOPS! Something went wrong! Please try after sometime!'

# SURVEY CONSTANTS
SURVEY_NOT_FOUND = 'Survey not found!'

# USER CONSTANTS
DUPLICATE_USER = 'User already exists.'
USER_CREATION_SUCCESS = 'User created successfully!'
USER_NOT_FOUND = 'User not found!'

# USER CONSTANTS
DUPLICATE_ORG = 'Organization already exists.'

# SUCCESS CONSTANTS
SUCCESS = 'Success'

# ERROR CONSTANTS
ERROR = 'Error'

# NO CONTENT CONSTANTS
NO_CONTENT = 'No content.'

# KEY RELATED CONSTANTS
INVALID_KEY = 'You are not authorized to access this service!'

# OTP RELATED CONSTANTS
INVALID_OTP = 'OTP verification failed! Please try again.'
VALID_OTP = 'OTP verified.'
SUCCESS_OTP = 'OTP has been sent successfully to your phone number.'
SENT_OTP = 'OTP has been sent successfully to your phone number.'
SEND_OTP_FAILED = 'Error in sending the OTP.'

# PAGINATION CONSTANTS
DEFAULT_PAGE_RECORDS = 10
DEFAULT_HOME_PAGE_RECORDS = 5

# AADHAAR CONSTANTS
INVALID_AADHAAR = 'Failed to fetch your Aadhaar data. Please try again.'

# COMMON CONSTANTS
GENERAL_ERROR = 'Something went wrong! Please try again.'

# CONSTANT VARIABLES
LAND_SIZE_UNIT_TELEGU = [("एकड़", "एकड़"),("हैक्टर", "हैक्टर")]
LAND_SIZE_UNIT = [("Acre", "Acre"),("Hectare", "Hectare")]
GENDERS = [("Male", "Male"),("Female", "Female"),("Other", "Other")]
INSURANCE_GENDERS = [("Male", "Male"),("Female", "Female")]
USER_DESIGNATIONS = [("Member", "Member"),("Shareholder", "Shareholder")]
SUB_SECTION_TYPES = [("Carousel", "Carousel"),("Grid", "Grid"),("Banner", "Banner")]
FARM_TYPES = [("biotic", "biotic"),("abiotic", "abiotic"),("micro_nutrient", "micro_nutrient"),("moisture", "moisture")]
ORDER_STATUS = [("Pending", "Pending"),("Paid", "Paid"),("Unpaid", "Unpaid")]
VALUE_TYPES = [("Int", "Int"),("String", "String"),("Double", "Double"),("Bool", "Bool")]
SUBSCRIPTION_TYPES = [('trial','Trial'),('subscription','Subscription')]
SURVEY_STATUS = [('active','Active'),('completed','Completed'),('expired','Expired')]
SURVEY_STATUS_USER = [('pending','Pending'),('accepted','Accepted'),('rejected','Rejected')]
SMS_TEMPLATE_FIELDS_TYPES = [("string","String"),("integer","Integer"),("optional","Optional"),("date","Date"),("fpo_number","Fpo Number"),("fpo_name","Fpo Name"),("phone_no","Phone Number"),("multi-optional","Multi optional")]
MSG_TYPES = [("text","Text"),("unicode","Unicode")]
CUSTOM_FORM_TYPES = [("bd_activity_sub_task","BD Activity (Sub Task)"),("bd_activity_task","BD Activity (Task)"),("sms_template","SMS Template"),("project","Project"),("project_task","Project Task"),("training","Training"),("drone_spray","Drone Spray")]
CUSTOM_FORM_FIELDS_TYPES = [("string","String"),("integer","Integer"),("optional","Optional"),("date","Date"),('pancard',"Pan card"),("aadhar","Aadhar"),('phone-number',"Phone number"),('image',"Image"),("multi-optional","Multi optional")]
DRONE_SPRAY_STATUS = [("PENDING", "Pending"),("IN_PROGRESS", "In Progress"),("COMPLETED", "Completed"),("FAILED", "Failed"),("CANCELLED", "Cancelled"),("REJECTED", "Rejected")]
LOCATION_ALREADY_EXIST="Location already exist"
KUTUMB_MODEL_COMPLETION_STATUS = [('husband_aadhaar','Husband Aadhaar'),('husband_bank','Husband Bank'),('husband_consent','Husband Consent'),('wife_aadhaar','Wife Aadhaar'),('wife_bank','Wife Bank'),('wife_consent','Wife Consent'),('completed','Completed'),("reconcilation_pending", "Reconcilation Pending"),('coi_generated','COI Generated')]
RELATIONSHIPS = [("father", "Father"),("mother", "Mother"),("son", "Son"),("daughter", "Daughter"),("brother", "Brother"),("sister", "Sister")]
ASSIGNEE_RELATIONSHIPS = [("uncle", "Uncle"),("aunty", "Aunty"),("grandfather", "Grandfather"),("grandmother", "Grandmother")]
PAYMENT_STATUS = [("pending", "Pending"),("paid", "Paid"),("unpaid", "Unpaid")]
TYPE_OF_PROCUREMENT=[("single","Single"),("bulk","Bulk")]
# ONEMONEY CONSTANTS
CONSENT_NOT_FOUND = 'Consent not found, please try again.'
CONSENT_REJECTED = 'Consent was rejected.'
URL_NOT_FOUND = 'URL not found'
DECRYPT_URL_NOT_FOUND = 'Decrypt URL not found'
CONSENT_LIST_NOT_FOUND = 'Consent list not found'
TRANSACTIONS_NOT_FOUND = 'Transactions not found'
CSV_NOT_EXPORTED = 'CSV not exported.'

SERVICE="service"
SUBSCRIPTION="subscription"

# PAYMENT CONSTANTS
PAYMENT_SUCCESS = 'Your services are activated. Please enjoy.'
COMMON_PAYMENT_SUCCESS = 'We have received your payment.'
SPONSOR_PAYMENT_SUCCESS = 'Congratulation, Your generous contribution of sponsor amount ₹{}, for {} farmers which we received. We greatly appreciate of your support.'
TRIAL_NOT_AVAILABLE = 'Trial not available for selected farmer.'
NOT_SUFFICIENT_FARMERS = 'Only {} are available in this organization.'

#SLUGS
SLUGS = {
    "SERVICES": {
        "SMS": "sms",
        "VIDEO": "video-call",
        "MY Farm": "my-farm",
        "FARMER CARD": "farmer-card"
    },
    "USER_ROLES": {
        "SPONSOR": "Sponsor",
        "ADMIN": "Admin",
        "FARMER": "Farmer",
        "BD":"BD",
        "BD_MANAGER":"BDManager",
        "ZONAL_HEAD":"ZONAL_HEAD"
    }
}


STRESS_THRESHOLD=20
BIOTIC_PRODUCT_TYPE=['pesticides','herbicides']
ABIOTIC_PRODUCT_TYPE=[]
NUTRIENT_PRODUCT_TYPE=['fertilizers',]

PAYMENT_TYPE=[('cash',"Cash"),('online',"Online"),('aryamitra',"Aryamitra")]

INDIAN_STATES = {
    "Andaman and Nicobar Islands": "AN",
    "Andhra Pradesh": "AP",
    "Arunachal Pradesh": "AR",
    "Assam": "AS",
    "Bihar": "BR",
    "Chandigarh": "CH",
    "Chhattisgarh": "CT",
    "Dadra and Nagar Haveli": "DN",
    "Daman and Diu": "DD",
    "Delhi": "DL",
    "Goa": "GA",
    "Gujarat": "GJ",
    "Haryana": "HR",
    "Himachal Pradesh": "HP",
    "Jammu and Kashmir": "JK",
    "Jharkhand": "JH",
    "Karnataka": "KA",
    "Kerala": "KL",
    "Lakshadweep": "LD",
    "Madhya Pradesh": "MP",
    "Maharashtra": "MH",
    "Manipur": "MN",
    "Meghalaya": "ML",
    "Mizoram": "MZ",
    "Nagaland": "NL",
    "Odisha": "OR",
    "Puducherry": "PY",
    "Punjab": "PB",
    "Rajasthan": "RJ",
    "Sikkim": "SK",
    "Tamil Nadu": "TN",
    "Telangana": "TG",
    "Tripura": "TR",
    "Uttar Pradesh": "UP",
    "Uttarakhand": "UT",
    "West Bengal": "WB"
}