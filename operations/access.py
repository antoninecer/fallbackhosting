"""Local authorization rules, not an identity provider or capability issuer.

Identity and policy inputs must come from trusted current server-side sources.
Never construct Identity from role/claims supplied by a browser. Decisions are
in-process policy results, not signed credentials accepted by the broker.
"""
from dataclasses import dataclass
from types import MappingProxyType

from operations.core import Denied, identifier

READS = frozenset({'inspect', 'job_status'})
MANAGE = READS | {'start', 'stop', 'restart', 'deploy', 'standby_preview', 'standby_publish'}
ADMIN = MANAGE | {'logs', 'remove', 'delete_data', 'assign_members'}


@dataclass(frozen=True)
class Identity:
    principal: str
    session: str
    revision: int
    expires_at: int
    active: bool
    platform_admin: bool = False
    verified_at: int | None = None
    strong_verified: bool = False


@dataclass(frozen=True)
class Grant:
    principal: str
    node: str
    project: str
    app: str
    role: str
    logs: bool = False


@dataclass(frozen=True)
class Decision:
    principal: str
    session: str
    identity_revision: int
    policy_revision: int
    node: str
    project: str
    app: str
    action: str
    requires_write_approval: bool


class Policy:
    def __init__(self, revision, grants):
        if type(revision) is not int or revision < 1:
            raise Denied('INVALID_POLICY_REVISION')
        indexed = {}
        for grant in grants:
            if not isinstance(grant, Grant):
                raise Denied('INVALID_GRANT')
            for value in (grant.principal, grant.node, grant.project, grant.app):
                identifier(value)
            if grant.role not in {'observer', 'manager'} or type(grant.logs) is not bool:
                raise Denied('INVALID_GRANT')
            key = (grant.principal, grant.node, grant.project, grant.app)
            if key in indexed:
                raise Denied('DUPLICATE_GRANT')
            indexed[key] = grant
        self.revision = revision
        self.grants = MappingProxyType(indexed)

    def authorize(self, identity, node, project, app, action, now):
        if not isinstance(identity, Identity) or type(now) is not int:
            raise Denied('TRUSTED_IDENTITY_REQUIRED')
        for value in (identity.principal, identity.session, node, project, app):
            identifier(value)
        if (type(identity.active) is not bool or not identity.active
                or type(identity.platform_admin) is not bool
                or type(identity.revision) is not int or identity.revision < 1
                or type(identity.expires_at) is not int or identity.expires_at <= now):
            raise Denied('INACTIVE_IDENTITY')
        if not isinstance(action, str) or action not in ADMIN:
            raise Denied('UNSUPPORTED_OPERATION')
        grant = self.grants.get((identity.principal, node, project, app))
        allowed = ADMIN if identity.platform_admin else (
            MANAGE if grant and grant.role == 'manager' else READS if grant else frozenset())
        if grant and grant.logs:
            allowed = allowed | {'logs'}
        if action not in allowed:
            raise Denied('APPLICATION_ACCESS_DENIED')
        writes = action not in READS | {'logs', 'standby_preview'}
        if writes and identity.strong_verified is not True:
            raise Denied('STRONG_VERIFICATION_REQUIRED')
        # A trusted IdP must attest the required strong verification method.
        # This timestamp is not a caller-provided substitute for MFA.
        if action in {'remove', 'delete_data', 'assign_members'}:
            if type(identity.verified_at) is not int or not 0 <= now - identity.verified_at < 300:
                raise Denied('FRESH_ADMIN_VERIFICATION_REQUIRED')
        return Decision(identity.principal, identity.session, identity.revision,
                        self.revision, node, project, app, action,
                        writes)

    def recheck(self, decision, current_identity, now):
        if not isinstance(decision, Decision):
            raise Denied('INVALID_PENDING_DECISION')
        current = self.authorize(current_identity, decision.node, decision.project,
                                 decision.app, decision.action, now)
        if current != decision:
            raise Denied('PENDING_AUTHORIZATION_CHANGED')
        return current
