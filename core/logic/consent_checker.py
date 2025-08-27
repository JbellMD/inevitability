"""
Consent Checker (Python Mirror)
-----------------------------
Python implementation of the consent checker that validates consent tickets
based on scope, time-to-live (TTL), and max invocations. This mirrors the
TypeScript implementation in consent_types.d.ts.
"""

from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass
import time
from enum import Enum

# Consent scope lattice (more constrained to less constrained)
class ConsentScope(str, Enum):
    SELF = "self"        # Individual only
    DYAD = "dyad"        # Two-person interaction
    GROUP = "group"      # Closed group (e.g., team)
    ORG = "org"          # Organization
    PUBLIC = "public"    # Public/open access
    
    @classmethod
    def can_escalate(cls, from_scope: str, to_scope: str) -> bool:
        """Check if scope can escalate from one to another."""
        scope_levels = {
            cls.SELF: 0,
            cls.DYAD: 1,
            cls.GROUP: 2,
            cls.ORG: 3,
            cls.PUBLIC: 4
        }
        
        if from_scope not in scope_levels or to_scope not in scope_levels:
            return False
            
        # Can only de-escalate (go to more constrained scope)
        return scope_levels[from_scope] >= scope_levels[to_scope]

@dataclass
class ConsentTicket:
    """Represents a consent validation ticket with TTL and scope constraints."""
    scope: str
    issued_at: float
    ttl_seconds: int
    max_invocations: int = 1
    invocations: int = 0
    
    def is_valid(self) -> bool:
        """Check if ticket is still valid (not expired, invocations remaining)."""
        # Check TTL
        now = time.time()
        if now > (self.issued_at + self.ttl_seconds):
            return False
            
        # Check invocations
        if self.invocations >= self.max_invocations:
            return False
            
        return True
    
    def use(self) -> bool:
        """Use the ticket, incrementing invocation count. Returns True if successful."""
        if not self.is_valid():
            return False
            
        self.invocations += 1
        return True
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "scope": self.scope,
            "issued_at": self.issued_at,
            "ttl_seconds": self.ttl_seconds,
            "max_invocations": self.max_invocations,
            "invocations": self.invocations,
            "valid": self.is_valid()
        }

class ConsentChecker:
    """Validates consent across various contexts and operations."""
    
    @staticmethod
    def validate_ticket(ticket: ConsentTicket) -> bool:
        """Validate a single consent ticket."""
        return ticket.is_valid()
    
    @staticmethod
    def validate_scope_escalation(ticket: ConsentTicket, target_scope: str) -> bool:
        """Check if the ticket allows escalation to the target scope."""
        return ConsentScope.can_escalate(ticket.scope, target_scope)
    
    @staticmethod
    def create_ticket(scope: str, ttl_seconds: int = 3600, max_invocations: int = 1) -> ConsentTicket:
        """Create a new consent ticket with current timestamp."""
        return ConsentTicket(
            scope=scope,
            issued_at=time.time(),
            ttl_seconds=ttl_seconds,
            max_invocations=max_invocations
        )
    
    @staticmethod
    def extract_from_context(context: Dict[str, Any]) -> List[ConsentTicket]:
        """Extract consent tickets from a context dictionary."""
        tickets = []
        
        # Handle case where consent is a dictionary with scope
        if "consent" in context:
            c = context["consent"]
            if isinstance(c, dict):
                if "scope" in c and "valid" in c and c["valid"]:
                    # Create a basic ticket from consent info
                    tickets.append(ConsentTicket(
                        scope=c["scope"],
                        issued_at=c.get("issued_at", time.time() - 60),  # Default to 1 min ago
                        ttl_seconds=c.get("ttl_seconds", 3600),
                        max_invocations=c.get("max_invocations", 1),
                        invocations=c.get("invocations", 0)
                    ))
        
        # Handle explicit tickets list
        if "consent_tickets" in context and isinstance(context["consent_tickets"], list):
            for t in context["consent_tickets"]:
                if isinstance(t, dict):
                    tickets.append(ConsentTicket(
                        scope=t.get("scope", "self"),
                        issued_at=t.get("issued_at", time.time() - 60),
                        ttl_seconds=t.get("ttl_seconds", 3600),
                        max_invocations=t.get("max_invocations", 1),
                        invocations=t.get("invocations", 0)
                    ))
                elif isinstance(t, ConsentTicket):
                    tickets.append(t)
                    
        return tickets
    
    @staticmethod
    def check_context(context: Dict[str, Any], target_scope: Optional[str] = None) -> bool:
        """Check if context has valid consent for target_scope."""
        tickets = ConsentChecker.extract_from_context(context)
        
        if not tickets:
            return False
        
        # If no specific scope required, any valid ticket is sufficient
        if target_scope is None:
            return any(t.is_valid() for t in tickets)
        
        # Otherwise, need valid ticket with appropriate scope
        return any(t.is_valid() and ConsentScope.can_escalate(t.scope, target_scope) for t in tickets)

# Test function
def test_consent_checker():
    """Test the consent checker with various inputs."""
    # Create a ticket for 'group' scope with short TTL
    ticket1 = ConsentChecker.create_ticket("group", ttl_seconds=10, max_invocations=2)
    print(f"Ticket valid: {ticket1.is_valid()}")
    
    # Check escalation
    print(f"Can use for self: {ConsentChecker.validate_scope_escalation(ticket1, 'self')}")
    print(f"Can use for public: {ConsentChecker.validate_scope_escalation(ticket1, 'public')}")
    
    # Use the ticket
    ticket1.use()
    print(f"After use, still valid: {ticket1.is_valid()}")
    ticket1.use()
    print(f"After second use, valid: {ticket1.is_valid()}")
    
    # Check from context
    context = {
        "consent": {
            "scope": "dyad", 
            "valid": True,
            "ttl_seconds": 3600
        }
    }
    
    print(f"Context has valid consent: {ConsentChecker.check_context(context)}")
    print(f"Context allows self: {ConsentChecker.check_context(context, 'self')}")
    print(f"Context allows org: {ConsentChecker.check_context(context, 'org')}")

if __name__ == "__main__":
    test_consent_checker()
