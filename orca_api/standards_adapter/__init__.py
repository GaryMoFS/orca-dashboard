from .core import StandardsAdapter, check_compliance
from .as3600 import AS3600
from .as4100 import AS4100
from .as1684 import AS1684
from .accessibility import AccessibilityStandards

__all__ = ["StandardsAdapter", "check_compliance", "AS3600", "AS4100", "AS1684", "AccessibilityStandards"]
