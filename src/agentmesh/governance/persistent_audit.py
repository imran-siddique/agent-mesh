"""
Persistent Audit Log

Extends the in-memory AuditLog with durable storage backends.
Audit entries are written to the storage provider and can survive
process restarts. The Merkle chain is rebuilt on load.

Usage:
    from agentmesh.governance.persistent_audit import PersistentAuditLog
    from agentmesh.storage.memory_provider import MemoryStorageProvider

    store = MemoryStorageProvider()
    await store.connect()

    audit = PersistentAuditLog(store, namespace="prod")
    entry = await audit.append(
        event_type="tool_invocation",
        agent_did="did:mesh:agent1",
        action="database_query",
    )

    # Entries survive across instances
    audit2 = PersistentAuditLog(store, namespace="prod")
    await audit2.load()
    assert len(audit2) > 0
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from agentmesh.governance.audit import AuditEntry, AuditLog, MerkleAuditChain
from agentmesh.storage.provider import AbstractStorageProvider


class PersistentAuditLog:
    """
    Audit log with durable storage.

    Writes every entry to the storage backend as it's appended.
    Supports:
    - Append-only writes (immutable once stored)
    - Load/rebuild from storage
    - Integrity verification across restarts
    - Namespace isolation (multiple audit streams)
    """

    def __init__(
        self,
        storage: AbstractStorageProvider,
        namespace: str = "default",
        verify_on_load: bool = True,
    ):
        self._storage = storage
        self._namespace = namespace
        self._verify_on_load = verify_on_load
        self._log = AuditLog()
        self._loaded = False

    # ── Keys ──────────────────────────────────────────────────

    def _entries_key(self) -> str:
        return f"audit:{self._namespace}:entries"

    def _meta_key(self) -> str:
        return f"audit:{self._namespace}:meta"

    def _entry_key(self, entry_id: str) -> str:
        return f"audit:{self._namespace}:entry:{entry_id}"

    def _agent_index_key(self, agent_did: str) -> str:
        return f"audit:{self._namespace}:agent:{agent_did}"

    # ── Write operations ──────────────────────────────────────

    async def append(
        self,
        event_type: str,
        agent_did: str,
        action: str,
        resource: Optional[str] = None,
        data: Optional[dict] = None,
        outcome: str = "success",
        policy_decision: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> AuditEntry:
        """
        Append an audit entry and persist it.

        The entry is written to both the in-memory log and the storage backend.
        """
        # Add to in-memory log (handles Merkle chaining)
        entry = self._log.log(
            event_type=event_type,
            agent_did=agent_did,
            action=action,
            resource=resource,
            data=data,
            outcome=outcome,
            policy_decision=policy_decision,
            trace_id=trace_id,
        )

        # Persist entry
        entry_json = json.dumps(entry.model_dump(), default=str, sort_keys=True)
        await self._storage.rpush(self._entries_key(), entry.entry_id)
        await self._storage.set(self._entry_key(entry.entry_id), entry_json)

        # Update agent index
        await self._storage.rpush(self._agent_index_key(agent_did), entry.entry_id)

        # Update metadata
        await self._storage.hset(self._meta_key(), "last_entry_id", entry.entry_id)
        await self._storage.hset(self._meta_key(), "entry_count", str(len(self._log._chain._entries)))
        root = self._log._chain.get_root_hash()
        if root:
            await self._storage.hset(self._meta_key(), "merkle_root", root)

        return entry

    # ── Read operations ───────────────────────────────────────

    async def load(self) -> int:
        """
        Load audit entries from storage and rebuild the Merkle chain.

        Returns the number of entries loaded.
        """
        entry_ids = await self._storage.lrange(self._entries_key(), 0, -1)
        if not entry_ids:
            self._loaded = True
            return 0

        self._log = AuditLog()

        for entry_id in entry_ids:
            raw = await self._storage.get(self._entry_key(entry_id))
            if raw:
                data = json.loads(raw)
                # Convert timestamp string back to datetime
                if isinstance(data.get("timestamp"), str):
                    data["timestamp"] = datetime.fromisoformat(data["timestamp"])
                entry = AuditEntry(**data)
                # Re-add to chain (recomputes hashes to verify)
                self._log._chain.add_entry(entry)
                # Rebuild indexes
                if entry.agent_did not in self._log._by_agent:
                    self._log._by_agent[entry.agent_did] = []
                self._log._by_agent[entry.agent_did].append(entry.entry_id)
                if entry.event_type not in self._log._by_type:
                    self._log._by_type[entry.event_type] = []
                self._log._by_type[entry.event_type].append(entry.entry_id)

        if self._verify_on_load:
            valid, error = self._log.verify_integrity()
            if not valid:
                raise RuntimeError(f"Audit log integrity check failed: {error}")

        self._loaded = True
        return len(entry_ids)

    async def get_entry(self, entry_id: str) -> Optional[AuditEntry]:
        """Get an entry by ID (from memory or storage)."""
        # Check in-memory first
        entry = self._log.get_entry(entry_id)
        if entry:
            return entry

        # Fall back to storage
        raw = await self._storage.get(self._entry_key(entry_id))
        if raw:
            data = json.loads(raw)
            if isinstance(data.get("timestamp"), str):
                data["timestamp"] = datetime.fromisoformat(data["timestamp"])
            return AuditEntry(**data)
        return None

    async def get_entries_for_agent(self, agent_did: str, limit: int = 100) -> List[AuditEntry]:
        """Get recent entries for an agent."""
        return self._log.get_entries_for_agent(agent_did, limit)

    async def query(
        self,
        agent_did: Optional[str] = None,
        event_type: Optional[str] = None,
        outcome: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """Query audit entries with filters."""
        return self._log.query(
            agent_did=agent_did,
            event_type=event_type,
            outcome=outcome,
            limit=limit,
        )

    # ── Integrity ─────────────────────────────────────────────

    async def verify_integrity(self) -> tuple[bool, Optional[str]]:
        """Verify in-memory chain integrity."""
        return self._log.verify_integrity()

    async def verify_against_storage(self) -> tuple[bool, Optional[str]]:
        """
        Verify that in-memory state matches persisted state.

        Checks:
        1. Entry count matches
        2. Merkle root matches
        3. Chain integrity
        """
        meta = await self._storage.hgetall(self._meta_key())
        if not meta:
            if len(self._log._chain._entries) == 0:
                return True, None
            return False, "No metadata in storage but entries exist in memory"

        stored_count = int(meta.get("entry_count", "0"))
        memory_count = len(self._log._chain._entries)
        if stored_count != memory_count:
            return False, f"Count mismatch: storage={stored_count}, memory={memory_count}"

        stored_root = meta.get("merkle_root", "")
        memory_root = self._log._chain.get_root_hash() or ""
        if stored_root != memory_root:
            return False, f"Merkle root mismatch: storage={stored_root[:16]}..., memory={memory_root[:16]}..."

        return self._log.verify_integrity()

    # ── Export ────────────────────────────────────────────────

    async def export(self) -> dict:
        """Export the audit log with integrity proof."""
        return self._log.export()

    async def export_cloudevents(self) -> List[dict]:
        """Export as CloudEvents."""
        return [e.to_cloudevent() for e in self._log._chain._entries]

    # ── Properties ────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self._log._chain._entries)

    @property
    def merkle_root(self) -> Optional[str]:
        return self._log._chain.get_root_hash()

    @property
    def inner(self) -> AuditLog:
        """Access the underlying in-memory AuditLog."""
        return self._log
