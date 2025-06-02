
import logging
import colorlog

SIGN_IN_URL = "https://zambeel.lums.edu.pk/psp/ps/?cmd=login&languageCd=ENG"
ENROLLMENT_TAB_URL = "https://zambeel.lums.edu.pk/psc/ps/EMPLOYEE/SA/c/NUI_FRAMEWORK.PT_AGSTARTPAGE_NUI.GBL?CONTEXTIDPARAMS=TEMPLATE_ID%3aPTPPNAVCOL&scname=ADMN_ENROLLMENT&PanelCollapsible=Y&PTPPB_GROUPLET_ID=ENROLLMENT&CRefName=ADMN_NAVCOLL_8"
GRADES_SEMESTER_URL = "https://zambeel.lums.edu.pk/psc/ps_newwin/EMPLOYEE/SA/c/SA_LEARNER_SERVICES.SSR_SSENRL_GRADE.GBL?NavColl=true"

DEFAULT_CHECK_INTERVAL = 60 * 5  # seconds
DEFAULT_RETRY_DELAY = 30
MAX_RETRIES = 3

SEMESTER_NAME = "Spring Semester 2024-25"


def init_logging():
    logger = logging.getLogger('covidence')
    logger.setLevel(logging.DEBUG)

    color_formatter = colorlog.ColoredFormatter(
        "%(log_color)s - %(levelname)s - %(message)s",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
        }
    )
    # console logs. Uncomment this if you do not want console output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(color_formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(f'grades.log', mode='w')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    return logger
