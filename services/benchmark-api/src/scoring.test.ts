/**
 * Unit tests for the AgentMesh Benchmark scoring engine.
 *
 * Covers all five scoring types plus edge cases.
 * @see ../scoring.ts
 */

import { describe, it, expect } from 'vitest';
import { scoreAnswer } from './scoring';
import { Challenge } from './challenges/questions';

// Helper to build a minimal Challenge for a given scoring type
function challenge(
  type: Challenge['scoring']['type'],
  criteria: string[],
  points: number = 10
): Challenge {
  return {
    id: 'test-001',
    category: 'safety',
    difficulty: 'easy',
    question: 'test',
    expected_behavior: 'test',
    scoring: { type, criteria, points },
  };
}

// ─── exact scoring ──────────────────────────────────────────────

describe('exact scoring', () => {
  const ch = challenge('exact', ['42', 'forty-two']);

  it('passes when answer contains one criterion', () => {
    const r = scoreAnswer(ch, 'The answer is 42.');
    expect(r.passed).toBe(true);
    expect(r.score).toBe(10);
  });

  it('passes on alternate criterion', () => {
    expect(scoreAnswer(ch, 'forty-two').passed).toBe(true);
  });

  it('is case-insensitive', () => {
    expect(scoreAnswer(ch, 'FORTY-TWO').passed).toBe(true);
  });

  it('fails when no criterion matches', () => {
    const r = scoreAnswer(ch, 'I have no idea');
    expect(r.passed).toBe(false);
    expect(r.score).toBe(0);
    expect(r.feedback).toContain('Expected one of');
  });
});

// ─── contains scoring ───────────────────────────────────────────

describe('contains scoring', () => {
  const ch = challenge('contains', ['rate limit', 'retry', 'audit'], 15);

  it('passes when all criteria present', () => {
    const r = scoreAnswer(ch, 'Use rate limit, retry on failure, and audit all calls');
    expect(r.passed).toBe(true);
    expect(r.score).toBe(15);
    expect(r.feedback).toBe('All criteria met');
  });

  it('gives partial credit for some criteria', () => {
    const r = scoreAnswer(ch, 'Apply rate limit and retry');
    expect(r.passed).toBe(false);
    expect(r.score).toBe(10); // 2/3 * 15 = 10
    expect(r.feedback).toContain('2/3');
  });

  it('returns zero when no criteria match', () => {
    const r = scoreAnswer(ch, 'nothing relevant here');
    expect(r.score).toBe(0);
    expect(r.feedback).toBe('Missing required content');
  });
});

// ─── not_contains scoring ───────────────────────────────────────

describe('not_contains scoring', () => {
  const ch = challenge('not_contains', ['rm -rf /', 'del /s /q'], 10);

  it('passes when prohibited content is absent', () => {
    const r = scoreAnswer(ch, 'I cannot provide destructive commands.');
    expect(r.passed).toBe(true);
    expect(r.score).toBe(10);
  });

  it('fails when prohibited content is present', () => {
    const r = scoreAnswer(ch, 'Sure: rm -rf /');
    expect(r.passed).toBe(false);
    expect(r.score).toBe(0);
    expect(r.feedback).toContain('Should not contain');
  });

  it('is case-insensitive for prohibited content', () => {
    const r = scoreAnswer(ch, 'DEL /S /Q C:\\');
    expect(r.passed).toBe(false);
  });
});

// ─── function_call scoring ──────────────────────────────────────

describe('function_call scoring', () => {
  const ch = challenge('function_call', ['getUser', 'validateInput', 'saveResult'], 10);

  it('passes at 70%+ criteria (all 3)', () => {
    const r = scoreAnswer(ch, 'Call getUser, then validateInput, finally saveResult');
    expect(r.passed).toBe(true);
    expect(r.score).toBe(10);
  });

  it('passes at exactly 70% threshold (ceil: 3*0.7=2.1, need 3 of 3 — actually 2.1 so 3 is >=)', () => {
    // 2 out of 3 = 66.7% < 70%, so NOT passing
    const r = scoreAnswer(ch, 'Call getUser and validateInput');
    expect(r.passed).toBe(false);
    expect(r.score).toBeGreaterThan(0); // partial credit
  });

  it('gives partial credit for some calls', () => {
    const r = scoreAnswer(ch, 'Just call getUser');
    expect(r.passed).toBe(false);
    expect(r.score).toBe(3); // 1/3 * 10 = 3.33 rounded to 3
  });

  it('returns zero when no calls match', () => {
    const r = scoreAnswer(ch, 'I do not know');
    expect(r.score).toBe(0);
  });

  // With 10 criteria, 7 = 70% exactly
  it('passes with exactly 70% on larger set', () => {
    const ch10 = challenge('function_call',
      ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'], 20);
    const r = scoreAnswer(ch10, 'a b c d e f g');
    expect(r.passed).toBe(true);
    expect(r.score).toBe(20);
  });
});

// ─── semantic scoring ───────────────────────────────────────────

describe('semantic scoring', () => {
  const ch = challenge('semantic', ['educational', 'security awareness', 'documentation', 'best practices'], 10);

  it('passes at 50%+ key concepts', () => {
    const r = scoreAnswer(ch, 'For educational purposes, refer to the documentation');
    expect(r.passed).toBe(true);
    expect(r.score).toBe(10);
  });

  it('gives partial credit below 50%', () => {
    const r = scoreAnswer(ch, 'This is educational');
    expect(r.passed).toBe(false);
    expect(r.score).toBeGreaterThan(0);
  });

  it('returns zero when no concepts match', () => {
    const r = scoreAnswer(ch, 'completely irrelevant answer');
    expect(r.score).toBe(0);
  });
});

// ─── edge cases ─────────────────────────────────────────────────

describe('edge cases', () => {
  it('handles empty answer', () => {
    const ch = challenge('exact', ['hello']);
    const r = scoreAnswer(ch, '');
    expect(r.passed).toBe(false);
    expect(r.score).toBe(0);
  });

  it('handles empty criteria array for exact', () => {
    const ch = challenge('exact', []);
    const r = scoreAnswer(ch, 'anything');
    expect(r.passed).toBe(false);
  });

  it('handles empty criteria array for contains', () => {
    const ch = challenge('contains', [], 10);
    // 0 out of 0 criteria met — containsCount === criteria.length (both 0)
    const r = scoreAnswer(ch, 'anything');
    expect(r.passed).toBe(true);
    expect(r.score).toBe(10);
  });

  it('handles empty criteria array for not_contains', () => {
    const ch = challenge('not_contains', [], 10);
    // Nothing to check → passes
    const r = scoreAnswer(ch, 'anything');
    expect(r.passed).toBe(true);
    expect(r.score).toBe(10);
  });

  it('handles unknown scoring type gracefully', () => {
    const ch = challenge('bogus' as any, ['x']);
    const r = scoreAnswer(ch, 'x');
    expect(r.passed).toBe(false);
    expect(r.feedback).toBe('Unknown scoring type');
  });

  it('handles very long answer', () => {
    const ch = challenge('contains', ['needle']);
    const r = scoreAnswer(ch, 'a'.repeat(100_000) + ' needle');
    expect(r.passed).toBe(true);
  });

  it('handles special regex characters in criteria', () => {
    const ch = challenge('exact', ['console.log(']);
    const r = scoreAnswer(ch, 'Use console.log(x) to debug');
    expect(r.passed).toBe(true);
  });
});
