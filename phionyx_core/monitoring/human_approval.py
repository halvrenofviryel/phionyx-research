"""
Human Approval Workflow
Human-in-the-loop mechanism for circuit breaker OPEN state.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ApprovalStatus(Enum):
    """Approval request status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class ApprovalRequest:
    """Human approval request."""
    request_id: str
    session_id: str
    circuit_state: str
    drift_report: Dict[str, Any]
    user_input: str
    blocked_output: Optional[str]
    created_at: datetime
    expires_at: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["status"] = self.status.value
        data["created_at"] = self.created_at.isoformat()
        data["expires_at"] = self.expires_at.isoformat()
        if self.approved_at:
            data["approved_at"] = self.approved_at.isoformat()
        return data

    def is_expired(self) -> bool:
        """Check if request is expired."""
        return datetime.now() > self.expires_at

    def is_pending(self) -> bool:
        """Check if request is pending."""
        return self.status == ApprovalStatus.PENDING and not self.is_expired()


class HumanApprovalService:
    """
    Human approval service for circuit breaker.

    Manages approval requests when circuit breaker is OPEN.
    """

    def __init__(
        self,
        approval_timeout_minutes: int = 30,
        max_pending_requests: int = 100
    ):
        """
        Initialize human approval service.

        Args:
            approval_timeout_minutes: Timeout for approval requests (minutes)
            max_pending_requests: Maximum pending requests
        """
        self.approval_timeout = approval_timeout_minutes
        self.max_pending = max_pending_requests

        # In-memory storage (can be replaced with database)
        self._requests: Dict[str, ApprovalRequest] = {}
        self._session_requests: Dict[str, List[str]] = {}  # session_id -> [request_ids]

    def create_approval_request(
        self,
        session_id: str,
        circuit_state: str,
        drift_report: Dict[str, Any],
        user_input: str,
        blocked_output: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ApprovalRequest:
        """
        Create approval request.

        Args:
            session_id: Session ID
            circuit_state: Circuit breaker state
            drift_report: Drift detection report
            user_input: User input that triggered the block
            blocked_output: Optional blocked output
            metadata: Optional metadata

        Returns:
            ApprovalRequest instance
        """
        # Generate request ID
        request_id = f"approval_{datetime.now().isoformat()}_{session_id[:8]}"

        # Check max pending requests
        pending_count = sum(
            1 for req in self._requests.values()
            if req.status == ApprovalStatus.PENDING and not req.is_expired()
        )
        if pending_count >= self.max_pending:
            logger.warning(f"Max pending requests reached ({self.max_pending}), rejecting oldest")
            self._expire_oldest_requests(10)

        # Create request
        request = ApprovalRequest(
            request_id=request_id,
            session_id=session_id,
            circuit_state=circuit_state,
            drift_report=drift_report,
            user_input=user_input,
            blocked_output=blocked_output,
            created_at=datetime.now(),
            expires_at=datetime.now().replace(
                minute=datetime.now().minute + self.approval_timeout
            ),
            status=ApprovalStatus.PENDING,
            metadata=metadata or {}
        )

        # Store request
        self._requests[request_id] = request

        # Track by session
        if session_id not in self._session_requests:
            self._session_requests[session_id] = []
        self._session_requests[session_id].append(request_id)

        logger.info(f"Created approval request: {request_id} for session {session_id}")
        return request

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get approval request by ID."""
        request = self._requests.get(request_id)
        if request and request.is_expired() and request.status == ApprovalStatus.PENDING:
            request.status = ApprovalStatus.EXPIRED
        return request

    def approve_request(
        self,
        request_id: str,
        approved_by: str
    ) -> bool:
        """
        Approve request.

        Args:
            request_id: Request ID
            approved_by: User/agent who approved

        Returns:
            True if approved, False otherwise
        """
        request = self._requests.get(request_id)
        if not request:
            return False

        if not request.is_pending():
            logger.warning(f"Request {request_id} is not pending (status={request.status.value})")
            return False

        request.status = ApprovalStatus.APPROVED
        request.approved_by = approved_by
        request.approved_at = datetime.now()

        logger.info(f"Request {request_id} approved by {approved_by}")
        return True

    def reject_request(
        self,
        request_id: str,
        rejection_reason: str
    ) -> bool:
        """
        Reject request.

        Args:
            request_id: Request ID
            rejection_reason: Reason for rejection

        Returns:
            True if rejected, False otherwise
        """
        request = self._requests.get(request_id)
        if not request:
            return False

        if not request.is_pending():
            logger.warning(f"Request {request_id} is not pending (status={request.status.value})")
            return False

        request.status = ApprovalStatus.REJECTED
        request.rejection_reason = rejection_reason

        logger.info(f"Request {request_id} rejected: {rejection_reason}")
        return True

    def get_pending_requests(
        self,
        session_id: Optional[str] = None
    ) -> List[ApprovalRequest]:
        """
        Get pending requests.

        Args:
            session_id: Optional session ID filter

        Returns:
            List of pending approval requests
        """
        requests = []
        for request in self._requests.values():
            if request.is_expired() and request.status == ApprovalStatus.PENDING:
                request.status = ApprovalStatus.EXPIRED
                continue

            if request.status == ApprovalStatus.PENDING:
                if session_id is None or request.session_id == session_id:
                    requests.append(request)

        return sorted(requests, key=lambda x: x.created_at, reverse=True)

    def get_session_requests(
        self,
        session_id: str
    ) -> List[ApprovalRequest]:
        """Get all requests for a session."""
        request_ids = self._session_requests.get(session_id, [])
        requests = [self._requests[rid] for rid in request_ids if rid in self._requests]
        return sorted(requests, key=lambda x: x.created_at, reverse=True)

    def _expire_oldest_requests(self, count: int) -> None:
        """Expire oldest pending requests."""
        pending = [
            req for req in self._requests.values()
            if req.status == ApprovalStatus.PENDING
        ]
        pending.sort(key=lambda x: x.created_at)

        for req in pending[:count]:
            req.status = ApprovalStatus.EXPIRED
            logger.info(f"Expired request {req.request_id} (oldest)")

