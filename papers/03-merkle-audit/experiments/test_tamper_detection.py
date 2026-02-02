"""
Merkle Audit Tamper Detection Test

Tests the tamper detection capabilities of the Merkle-chained audit log.
Verifies that any modification to entries is detected.

Attack scenarios:
1. Modify entry content
2. Delete an entry
3. Insert a fake entry
4. Reorder entries
5. Modify entry timestamp
6. Modify entry hash (hash collision attempt)

Expected: 100% detection rate for all scenarios.
"""

import sys
import copy
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass
from typing import Callable, Any
from datetime import datetime, timedelta
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from agentmesh.governance.audit import AuditLog, AuditEntry, MerkleAuditChain


@dataclass
class TamperTestResult:
    """Result from a tamper detection test."""
    
    attack_type: str
    entries_modified: int
    detected: bool
    detection_method: str
    detection_time_ms: float


def create_test_log(size: int = 100) -> AuditLog:
    """Create a populated audit log for testing."""
    log = AuditLog()
    
    for i in range(size):
        log.log(
            event_type=f"event_{i % 5}",
            agent_did=f"did:mesh:agent_{i % 10}",
            action=f"action_{i % 3}",
            resource=f"/resource/{i}",
            data={"value": i, "timestamp": datetime.utcnow().isoformat()},
            outcome="success" if i % 7 != 0 else "failure",
        )
    
    return log


def attack_modify_content(log: AuditLog) -> AuditLog:
    """Attack: Modify entry content without updating hash."""
    modified = copy.deepcopy(log)
    
    if modified._chain._entries:
        # Modify middle entry
        idx = len(modified._chain._entries) // 2
        modified._chain._entries[idx].data["value"] = "TAMPERED"
    
    return modified


def attack_modify_with_new_hash(log: AuditLog) -> AuditLog:
    """Attack: Modify content and recompute hash (but breaks chain)."""
    modified = copy.deepcopy(log)
    
    if modified._chain._entries:
        idx = len(modified._chain._entries) // 2
        entry = modified._chain._entries[idx]
        entry.data["value"] = "TAMPERED"
        # Recompute hash - but this breaks the chain to next entry
        entry.entry_hash = entry.compute_hash()
    
    return modified


def attack_delete_entry(log: AuditLog) -> AuditLog:
    """Attack: Delete an entry from the middle."""
    modified = copy.deepcopy(log)
    
    if len(modified._chain._entries) > 2:
        idx = len(modified._chain._entries) // 2
        del modified._chain._entries[idx]
        
        # Update indices
        for agent_entries in modified._by_agent.values():
            entry_id = modified._chain._entries[idx].entry_id if idx < len(modified._chain._entries) else None
            if entry_id in agent_entries:
                agent_entries.remove(entry_id)
    
    return modified


def attack_insert_fake_entry(log: AuditLog) -> AuditLog:
    """Attack: Insert a fake entry."""
    modified = copy.deepcopy(log)
    
    fake_entry = AuditEntry(
        event_type="fake_event",
        agent_did="did:mesh:fake_agent",
        action="fake_action",
        data={"fake": True},
    )
    
    if modified._chain._entries:
        # Insert in middle
        idx = len(modified._chain._entries) // 2
        modified._chain._entries.insert(idx, fake_entry)
    
    return modified


def attack_reorder_entries(log: AuditLog) -> AuditLog:
    """Attack: Swap two entries."""
    modified = copy.deepcopy(log)
    
    entries = modified._chain._entries
    if len(entries) >= 4:
        idx1 = len(entries) // 4
        idx2 = 3 * len(entries) // 4
        entries[idx1], entries[idx2] = entries[idx2], entries[idx1]
    
    return modified


def attack_modify_timestamp(log: AuditLog) -> AuditLog:
    """Attack: Backdate an entry timestamp."""
    modified = copy.deepcopy(log)
    
    if modified._chain._entries:
        idx = len(modified._chain._entries) // 2
        modified._chain._entries[idx].timestamp = datetime(2020, 1, 1)
    
    return modified


def attack_hash_without_previous(log: AuditLog) -> AuditLog:
    """Attack: Compute valid hash but with wrong previous_hash."""
    modified = copy.deepcopy(log)
    
    if len(modified._chain._entries) > 1:
        idx = len(modified._chain._entries) // 2
        entry = modified._chain._entries[idx]
        # Set wrong previous hash
        entry.previous_hash = "0" * 64
        # Recompute hash with wrong previous
        entry.entry_hash = entry.compute_hash()
    
    return modified


def run_tamper_tests(
    log_size: int = 100,
    verbose: bool = True,
) -> list[TamperTestResult]:
    """Run all tamper detection tests."""
    
    attacks = [
        ("Modify content (no rehash)", attack_modify_content),
        ("Modify content (with rehash)", attack_modify_with_new_hash),
        ("Delete entry", attack_delete_entry),
        ("Insert fake entry", attack_insert_fake_entry),
        ("Reorder entries", attack_reorder_entries),
        ("Modify timestamp", attack_modify_timestamp),
        ("Wrong previous hash", attack_hash_without_previous),
    ]
    
    results = []
    
    if verbose:
        print(f"\n{'='*70}")
        print("Merkle Audit Tamper Detection Tests")
        print(f"Log size: {log_size} entries")
        print(f"{'='*70}\n")
    
    # Create pristine log
    original_log = create_test_log(log_size)
    
    # Verify original is valid
    is_valid, error = original_log.verify_integrity()
    assert is_valid, f"Original log should be valid: {error}"
    
    if verbose:
        print(f"{'Attack Type':<35} {'Detected':>10} {'Method':>20}")
        print("-" * 70)
    
    for attack_name, attack_func in attacks:
        import time
        
        # Apply attack
        tampered_log = attack_func(original_log)
        
        # Time detection
        start = time.perf_counter()
        is_valid, error = tampered_log.verify_integrity()
        end = time.perf_counter()
        
        detected = not is_valid
        detection_method = error if error else "N/A"
        
        result = TamperTestResult(
            attack_type=attack_name,
            entries_modified=1,
            detected=detected,
            detection_method=detection_method[:50] if detection_method else "N/A",
            detection_time_ms=(end - start) * 1000,
        )
        results.append(result)
        
        if verbose:
            status = "✓ DETECTED" if detected else "✗ MISSED"
            print(f"{attack_name:<35} {status:>10} {detection_method[:20]:>20}")
    
    # Summary
    if verbose:
        detected_count = sum(1 for r in results if r.detected)
        total = len(results)
        
        print(f"\n{'='*70}")
        print(f"Detection Rate: {detected_count}/{total} ({100*detected_count/total:.1f}%)")
        print(f"{'='*70}")
        
        if detected_count == total:
            print("✓ All tamper attempts detected successfully")
        else:
            print("✗ WARNING: Some attacks were not detected!")
            for r in results:
                if not r.detected:
                    print(f"  - {r.attack_type}")
    
    return results


def run_proof_tamper_tests(log_size: int = 100, verbose: bool = True) -> list[TamperTestResult]:
    """Test tamper detection via Merkle proofs."""
    
    results = []
    
    if verbose:
        print(f"\n{'='*70}")
        print("Merkle Proof Tamper Detection Tests")
        print(f"{'='*70}\n")
    
    log = create_test_log(log_size)
    
    # Get a proof for middle entry
    entries = log._chain._entries
    target_entry = entries[len(entries) // 2]
    original_proof = log.get_proof(target_entry.entry_id)
    original_root = log._chain.get_root_hash()
    
    assert original_proof, "Should get proof for existing entry"
    assert original_proof["verified"], "Original proof should verify"
    
    # Test 1: Tamper with entry, verify proof fails
    tampered_entry_hash = hashlib.sha256(b"tampered").hexdigest()
    
    import time
    start = time.perf_counter()
    is_valid = log._chain.verify_proof(
        tampered_entry_hash,
        original_proof["merkle_proof"],
        original_root,
    )
    end = time.perf_counter()
    
    result = TamperTestResult(
        attack_type="Tampered entry hash",
        entries_modified=1,
        detected=not is_valid,
        detection_method="Proof verification failed",
        detection_time_ms=(end - start) * 1000,
    )
    results.append(result)
    
    if verbose:
        status = "✓ DETECTED" if result.detected else "✗ MISSED"
        print(f"Tampered entry hash: {status}")
    
    # Test 2: Wrong root hash
    fake_root = "0" * 64
    
    start = time.perf_counter()
    is_valid = log._chain.verify_proof(
        target_entry.entry_hash,
        original_proof["merkle_proof"],
        fake_root,
    )
    end = time.perf_counter()
    
    result = TamperTestResult(
        attack_type="Wrong root hash",
        entries_modified=0,
        detected=not is_valid,
        detection_method="Root hash mismatch",
        detection_time_ms=(end - start) * 1000,
    )
    results.append(result)
    
    if verbose:
        status = "✓ DETECTED" if result.detected else "✗ MISSED"
        print(f"Wrong root hash: {status}")
    
    # Test 3: Tampered proof path
    tampered_proof = copy.deepcopy(original_proof["merkle_proof"])
    if tampered_proof:
        tampered_proof[0] = ("0" * 64, tampered_proof[0][1])
    
    start = time.perf_counter()
    is_valid = log._chain.verify_proof(
        target_entry.entry_hash,
        tampered_proof,
        original_root,
    )
    end = time.perf_counter()
    
    result = TamperTestResult(
        attack_type="Tampered proof path",
        entries_modified=0,
        detected=not is_valid,
        detection_method="Proof path invalid",
        detection_time_ms=(end - start) * 1000,
    )
    results.append(result)
    
    if verbose:
        status = "✓ DETECTED" if result.detected else "✗ MISSED"
        print(f"Tampered proof path: {status}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Test Merkle audit tamper detection"
    )
    parser.add_argument(
        "--size", type=int, default=100,
        help="Log size for tests (default: 100)"
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress verbose output"
    )
    
    args = parser.parse_args()
    
    # Run chain verification tests
    chain_results = run_tamper_tests(
        log_size=args.size,
        verbose=not args.quiet,
    )
    
    # Run proof verification tests
    proof_results = run_proof_tamper_tests(
        log_size=args.size,
        verbose=not args.quiet,
    )
    
    # Final summary
    all_results = chain_results + proof_results
    detected = sum(1 for r in all_results if r.detected)
    total = len(all_results)
    
    print(f"\n{'='*70}")
    print(f"FINAL RESULT: {detected}/{total} attacks detected ({100*detected/total:.1f}%)")
    print(f"{'='*70}")
    
    # Exit with error if any attacks missed
    if detected < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
