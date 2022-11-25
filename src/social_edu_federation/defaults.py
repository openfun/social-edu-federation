"""Module providing default values for the social_edu_federation app."""
from enum import Enum


class EduPersonAffiliationEnum(Enum):
    """Enumeration of eduPersonAffiliation values"""

    STUDENT = "student"
    FACULTY = "faculty"
    STAFF = "staff"
    EMPLOYEE = "employee"
    MEMBER = "member"
    AFFILIATE = "affiliate"
    ALUM = "alum"
    LIBRARY_WALK_IN = "library-walk-in"
    RESEARCHER = "researcher"
    RETIRED = "retired"
    EMERITUS = "emeritus"
    TEACHER = "teacher"
    REGISTERED_READER = "registered-reader"

    @classmethod
    def get_choices(cls):
        """Get the choices for the eduPersonAffiliation possible values (for Django mostly)."""
        return [(member.value, member.value) for member in cls.__members__.values()]
