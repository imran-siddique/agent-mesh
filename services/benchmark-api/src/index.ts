/**
 * AgentMesh Benchmark API - Main Entry Point
 *
 * Cloudflare Workers / Hono-based API for the AgentMesh Benchmark.
 * Provides challenge-based evaluation of AI agents across five categories:
 * Safety, Reasoning, Tool Use, Collaboration, and Memory.
 *
 * @see {@link https://github.com/imran-siddique/agent-mesh} AgentMesh repository
 * @module benchmark-api
 */

import { Hono } from 'hono';
import { cors } from 'hono/cors';
import {
  allChallenges,
  getChallengesByCategory,
  getRandomChallenges,
  Challenge,
  Difficulty,
  validDifficulties
} from './challenges/questions';
import { scoreAnswer } from './scoring';

/** Cloudflare Workers binding types. */
interface Env {
  /** KV namespace for session and score storage. */
  SCORES: KVNamespace;
  /** D1 database (reserved for future relational queries). */
  DB: D1Database;
}

/** Active benchmark session tracking challenges and timing. */
interface ChallengeSession {
  id: string;
  agent_name: string;
  categories: string[];
  challenges: Challenge[];
  started_at: string;
  expires_at: string;
}

/** Individual challenge submission result after scoring. */
interface SubmissionResult {
  challenge_id: string;
  score: number;
  max_score: number;
  passed: boolean;
  feedback: string;
}

/** Aggregate score result for a completed benchmark session. */
interface AgentScoreResult {
  agent: string;
  timestamp: string;
  session_id: string;
  scores: {
    safety: number;
    reasoning: number;
    tool_use: number;
    collaboration: number;
    memory: number;
  };
  overall: number;
  total_challenges: number;
  passed_challenges: number;
  badge_url: string;
  certificate_url: string;
}

// Initialize Hono app
const app = new Hono<{ Bindings: Env }>();

// CORS middleware
app.use('*', cors({
  origin: '*',
  allowMethods: ['GET', 'POST', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization'],
}));

/** Rate-limit metadata headers on every response (#54). */
app.use('*', async (c, next) => {
  await next();
  c.res.headers.set('X-RateLimit-Limit', '60');
  c.res.headers.set('X-RateLimit-Remaining', '59');
  c.res.headers.set('X-RateLimit-Reset', String(Math.floor(Date.now() / 1000) + 60));
});

// ============================================
// ROUTES
// ============================================

// Health check
app.get('/', (c) => {
  return c.json({
    name: 'AgentMesh Benchmark API',
    version: '1.0.0',
    status: 'healthy',
    endpoints: {
      'POST /api/v1/challenge/start': 'Start a benchmark session (supports optional "difficulty": "easy"|"medium"|"hard")',
      'POST /api/v1/challenge/:id/submit': 'Submit answers',
      'GET /api/v1/leaderboard': 'Get leaderboard',
      'GET /api/v1/badge/:agent': 'Get badge SVG',
      'GET /api/v1/categories': 'List challenge categories'
    }
  });
});

// List categories
app.get('/api/v1/categories', (c) => {
  return c.json({
    categories: [
      { id: 'safety', name: 'Safety', description: 'Policy compliance and harmful content rejection', icon: '🛡️', challenges: 10 },
      { id: 'reasoning', name: 'Reasoning', description: 'Multi-step logic, math, and planning', icon: '🧠', challenges: 10 },
      { id: 'tool_use', name: 'Tool Use', description: 'Correct API and function calling', icon: '🔧', challenges: 10 },
      { id: 'collaboration', name: 'Collaboration', description: 'Multi-agent coordination', icon: '🤝', challenges: 10 },
      { id: 'memory', name: 'Memory', description: 'Context retention across turns', icon: '💾', challenges: 10 }
    ]
  });
});

// Start a challenge session
app.post('/api/v1/challenge/start', async (c) => {
  try {
    const body = await c.req.json();
    const { agent_name, categories = ['safety', 'reasoning', 'tool_use', 'collaboration', 'memory'], challenges_per_category = 2, difficulty } = body;

    if (!agent_name) {
      return c.json({ error: 'agent_name is required' }, 400);
    }

    // Validate difficulty if provided
    if (difficulty && !validDifficulties.includes(difficulty)) {
      return c.json({ error: `Invalid difficulty: "${difficulty}". Must be one of: ${validDifficulties.join(', ')}` }, 400);
    }

    // Generate session ID
    const sessionId = crypto.randomUUID();

    // Collect challenges from selected categories, optionally filtered by difficulty
    let selectedChallenges: Challenge[] = [];
    for (const category of categories) {
      const catChallenges = getChallengesByCategory(category as keyof typeof allChallenges, difficulty);
      if (catChallenges && catChallenges.length > 0) {
        // Take random challenges from each category
        const shuffled = catChallenges.sort(() => Math.random() - 0.5);
        selectedChallenges.push(...shuffled.slice(0, challenges_per_category));
      }
    }

    // Create session
    const session: ChallengeSession = {
      id: sessionId,
      agent_name,
      categories,
      challenges: selectedChallenges,
      started_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + 30 * 60 * 1000).toISOString() // 30 min expiry
    };

    // Store session in KV
    await c.env.SCORES.put(`session:${sessionId}`, JSON.stringify(session), {
      expirationTtl: 1800 // 30 minutes
    });

    // Return challenges (without scoring criteria)
    const challengesForAgent = selectedChallenges.map(ch => ({
      id: ch.id,
      category: ch.category,
      difficulty: ch.difficulty,
      question: ch.question,
      context: ch.context
    }));

    return c.json({
      session_id: sessionId,
      agent_name,
      categories,
      difficulty: difficulty || 'all',
      total_challenges: challengesForAgent.length,
      expires_at: session.expires_at,
      challenges: challengesForAgent
    });

  } catch (error) {
    return c.json({ error: 'Failed to start challenge', details: String(error) }, 500);
  }
});

// Submit answers
app.post('/api/v1/challenge/:sessionId/submit', async (c) => {
  try {
    const sessionId = c.req.param('sessionId');
    const body = await c.req.json();
    const { answers } = body; // Array of { challenge_id, answer }

    if (!answers || !Array.isArray(answers)) {
      return c.json({ error: 'answers array is required' }, 400);
    }

    // Get session
    const sessionData = await c.env.SCORES.get(`session:${sessionId}`);
    if (!sessionData) {
      return c.json({ error: 'Session not found or expired' }, 404);
    }

    const session: ChallengeSession = JSON.parse(sessionData);

    // Score each answer
    const results: SubmissionResult[] = [];
    const categoryScores: Record<string, { earned: number; max: number }> = {
      safety: { earned: 0, max: 0 },
      reasoning: { earned: 0, max: 0 },
      tool_use: { earned: 0, max: 0 },
      collaboration: { earned: 0, max: 0 },
      memory: { earned: 0, max: 0 }
    };

    for (const challenge of session.challenges) {
      const submission = answers.find((a: any) => a.challenge_id === challenge.id);
      const answer = submission?.answer || '';
      
      // Score the answer
      const { score, passed, feedback } = scoreAnswer(challenge, answer);
      
      results.push({
        challenge_id: challenge.id,
        score,
        max_score: challenge.scoring.points,
        passed,
        feedback
      });

      categoryScores[challenge.category].earned += score;
      categoryScores[challenge.category].max += challenge.scoring.points;
    }

    // Calculate percentages
    const scores = {
      safety: categoryScores.safety.max > 0 ? Math.round((categoryScores.safety.earned / categoryScores.safety.max) * 100) : 0,
      reasoning: categoryScores.reasoning.max > 0 ? Math.round((categoryScores.reasoning.earned / categoryScores.reasoning.max) * 100) : 0,
      tool_use: categoryScores.tool_use.max > 0 ? Math.round((categoryScores.tool_use.earned / categoryScores.tool_use.max) * 100) : 0,
      collaboration: categoryScores.collaboration.max > 0 ? Math.round((categoryScores.collaboration.earned / categoryScores.collaboration.max) * 100) : 0,
      memory: categoryScores.memory.max > 0 ? Math.round((categoryScores.memory.earned / categoryScores.memory.max) * 100) : 0
    };

    const overall = Math.round(
      (scores.safety + scores.reasoning + scores.tool_use + scores.collaboration + scores.memory) / 5
    );

    const passedCount = results.filter(r => r.passed).length;

    // Create score result
    const scoreResult: AgentScoreResult = {
      agent: session.agent_name,
      timestamp: new Date().toISOString(),
      session_id: sessionId,
      scores,
      overall,
      total_challenges: session.challenges.length,
      passed_challenges: passedCount,
      badge_url: `https://agentmesh-benchmark.workers.dev/api/v1/badge/${encodeURIComponent(session.agent_name)}`,
      certificate_url: `https://agentmesh-benchmark.workers.dev/api/v1/certificate/${sessionId}`
    };

    // Store score in KV (for leaderboard)
    await c.env.SCORES.put(
      `score:${session.agent_name}:${Date.now()}`,
      JSON.stringify(scoreResult),
      { expirationTtl: 60 * 60 * 24 * 30 } // 30 days
    );

    // Store latest score for agent
    await c.env.SCORES.put(
      `latest:${session.agent_name}`,
      JSON.stringify(scoreResult)
    );

    // Delete session
    await c.env.SCORES.delete(`session:${sessionId}`);

    return c.json({
      success: true,
      ...scoreResult,
      details: results
    });

  } catch (error) {
    return c.json({ error: 'Failed to submit answers', details: String(error) }, 500);
  }
});

/** GET /api/v1/leaderboard - Ranked agents with aggregate category statistics. */
app.get('/api/v1/leaderboard', async (c) => {
  try {
    const list = await c.env.SCORES.list({ prefix: 'latest:' });
    
    const scores: AgentScoreResult[] = [];
    for (const key of list.keys) {
      const data = await c.env.SCORES.get(key.name);
      if (data) {
        scores.push(JSON.parse(data));
      }
    }

    scores.sort((a, b) => b.overall - a.overall);

    const leaderboard = scores.slice(0, 50).map((score, index) => ({
      rank: index + 1,
      ...score
    }));

    // Category statistics (#52)
    const categoryStats = {
      safety:        { avg: 0, min: 100, max: 0, agents_above_90: 0 },
      reasoning:     { avg: 0, min: 100, max: 0, agents_above_90: 0 },
      tool_use:      { avg: 0, min: 100, max: 0, agents_above_90: 0 },
      collaboration: { avg: 0, min: 100, max: 0, agents_above_90: 0 },
      memory:        { avg: 0, min: 100, max: 0, agents_above_90: 0 },
    };

    if (scores.length > 0) {
      for (const cat of Object.keys(categoryStats) as Array<keyof typeof categoryStats>) {
        const vals = scores.map(s => s.scores[cat]);
        categoryStats[cat].avg = Math.round(vals.reduce((a, b) => a + b, 0) / vals.length);
        categoryStats[cat].min = Math.min(...vals);
        categoryStats[cat].max = Math.max(...vals);
        categoryStats[cat].agents_above_90 = vals.filter(v => v >= 90).length;
      }
    }

    return c.json({
      updated_at: new Date().toISOString(),
      total_agents: leaderboard.length,
      category_stats: categoryStats,
      leaderboard
    });

  } catch (error) {
    return c.json({ error: 'Failed to fetch leaderboard', details: String(error) }, 500);
  }
});

/**
 * GET /api/v1/badge/:agent - Generate a shields.io-style SVG badge.
 *
 * Query params for customization (#57):
 * - `label`  - Left-side text (default: "AgentMesh Score")
 * - `style`  - "flat" (default) or "plastic"
 * - `color`  - Override score color (hex without #, e.g. "4c1")
 * - `category` - Show score for a specific category instead of overall
 */
app.get('/api/v1/badge/:agent', async (c) => {
  const agentName = decodeURIComponent(c.req.param('agent'));
  const label = c.req.query('label') || 'AgentMesh Score';
  const style = c.req.query('style') || 'flat';
  const colorOverride = c.req.query('color');
  const category = c.req.query('category') as keyof AgentScoreResult['scores'] | undefined;

  const data = await c.env.SCORES.get(`latest:${agentName}`);

  let score = 0;
  let color = '#9ca3af'; // gray (no data)

  if (data) {
    const agentScore: AgentScoreResult = JSON.parse(data);
    score = category && agentScore.scores[category] !== undefined
      ? agentScore.scores[category]
      : agentScore.overall;

    if (colorOverride) {
      color = `#${colorOverride}`;
    } else if (score >= 90) {
      color = '#10b981'; // green
    } else if (score >= 70) {
      color = '#3b82f6'; // blue
    } else if (score >= 50) {
      color = '#f59e0b'; // yellow
    } else {
      color = '#ef4444'; // red
    }
  }

  const radius = style === 'plastic' ? '0' : '4';
  const gradient = style === 'plastic'
    ? `<linearGradient id="b" x2="0" y2="100%"><stop offset="0" stop-color="#fff" stop-opacity=".15"/><stop offset="1" stop-opacity=".15"/></linearGradient>`
    : `<linearGradient id="b" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient>`;

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="200" height="28">
  ${gradient}
  <clipPath id="r"><rect width="200" height="28" rx="${radius}" fill="#fff"/></clipPath>
  <g clip-path="url(#r)">
    <rect width="130" height="28" fill="#555"/>
    <rect x="130" width="70" height="28" fill="${color}"/>
    <rect width="200" height="28" fill="url(#b)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
    <text x="65" y="18">${label}</text>
    <text x="165" y="18" font-weight="bold">${score}/100</text>
  </g>
</svg>`;

  return new Response(svg, {
    headers: {
      'Content-Type': 'image/svg+xml',
      'Cache-Control': 'public, max-age=300'
    }
  });
});

// Get agent score
app.get('/api/v1/score/:agent', async (c) => {
  const agentName = decodeURIComponent(c.req.param('agent'));
  const data = await c.env.SCORES.get(`latest:${agentName}`);
  
  if (!data) {
    return c.json({ error: 'Agent not found' }, 404);
  }

  return c.json(JSON.parse(data));
});

export default app;
