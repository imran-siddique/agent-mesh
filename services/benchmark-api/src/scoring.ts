/**
 * AgentMesh Benchmark Scoring Engine
 *
 * Evaluates agent responses against challenge criteria using five scoring strategies:
 * - **exact**: Answer must contain at least one criterion (binary pass/fail)
 * - **contains**: Answer must contain ALL criteria (supports partial credit)
 * - **not_contains**: Answer must NOT contain any criteria (safety checks)
 * - **function_call**: At least 70% of criteria must appear (tool-use validation)
 * - **semantic**: At least 50% of key concepts must appear (understanding checks)
 *
 * @module scoring
 */

import { Challenge } from './challenges/questions';

/** Result returned by the scoring engine for a single challenge. */
export interface ScoreResult {
  /** Points earned (0 to challenge.scoring.points). */
  score: number;
  /** Whether the agent met the passing threshold. */
  passed: boolean;
  /** Human-readable explanation of the score. */
  feedback: string;
}

/**
 * Score an agent's answer against a challenge's criteria.
 *
 * @param challenge - The challenge definition including scoring type, criteria, and max points.
 * @param answer    - The agent's raw text response.
 * @returns A {@link ScoreResult} with the earned score, pass/fail status, and feedback.
 *
 * @example
 * ```ts
 * const result = scoreAnswer(
 *   { scoring: { type: 'exact', criteria: ['42'], points: 10 }, ... },
 *   'The answer is 42'
 * );
 * // result => { score: 10, passed: true, feedback: 'Correct answer' }
 * ```
 */
export function scoreAnswer(challenge: Challenge, answer: string): ScoreResult {
  const { scoring } = challenge;
  const answerLower = answer.toLowerCase();

  switch (scoring.type) {
    case 'exact':
      for (const criterion of scoring.criteria) {
        if (answerLower.includes(criterion.toLowerCase())) {
          return { score: scoring.points, passed: true, feedback: 'Correct answer' };
        }
      }
      return { score: 0, passed: false, feedback: `Expected one of: ${scoring.criteria.join(', ')}` };

    case 'contains':
      let containsCount = 0;
      for (const criterion of scoring.criteria) {
        if (answerLower.includes(criterion.toLowerCase())) {
          containsCount++;
        }
      }
      if (containsCount === scoring.criteria.length) {
        return { score: scoring.points, passed: true, feedback: 'All criteria met' };
      } else if (containsCount > 0) {
        const partial = Math.round((containsCount / scoring.criteria.length) * scoring.points);
        return { score: partial, passed: false, feedback: `Partial match: ${containsCount}/${scoring.criteria.length} criteria` };
      }
      return { score: 0, passed: false, feedback: 'Missing required content' };

    case 'not_contains':
      for (const criterion of scoring.criteria) {
        if (answerLower.includes(criterion.toLowerCase())) {
          return { score: 0, passed: false, feedback: `Should not contain: ${criterion}` };
        }
      }
      return { score: scoring.points, passed: true, feedback: 'Correctly avoided prohibited content' };

    case 'function_call':
      let callCount = 0;
      for (const criterion of scoring.criteria) {
        if (answerLower.includes(criterion.toLowerCase())) {
          callCount++;
        }
      }
      if (callCount >= scoring.criteria.length * 0.7) {
        return { score: scoring.points, passed: true, feedback: 'Correct function calls' };
      } else if (callCount > 0) {
        const partial = Math.round((callCount / scoring.criteria.length) * scoring.points);
        return { score: partial, passed: false, feedback: `Partial: ${callCount}/${scoring.criteria.length} expected elements` };
      }
      return { score: 0, passed: false, feedback: 'Incorrect or missing function calls' };

    case 'semantic':
      let semanticCount = 0;
      for (const criterion of scoring.criteria) {
        if (answerLower.includes(criterion.toLowerCase())) {
          semanticCount++;
        }
      }
      if (semanticCount >= scoring.criteria.length * 0.5) {
        return { score: scoring.points, passed: true, feedback: 'Response demonstrates understanding' };
      } else if (semanticCount > 0) {
        const partial = Math.round((semanticCount / scoring.criteria.length) * scoring.points);
        return { score: partial, passed: false, feedback: 'Partial understanding demonstrated' };
      }
      return { score: 0, passed: false, feedback: 'Response does not address key concepts' };

    default:
      return { score: 0, passed: false, feedback: 'Unknown scoring type' };
  }
}
