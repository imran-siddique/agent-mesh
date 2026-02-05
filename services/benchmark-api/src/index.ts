import express from 'express';
import { getChallenges } from './challenges';

const app = express();
app.use(express.json());
const PORT = process.env.PORT || 3000;

app.post('/api/v1/challenge/start', (req, res) => {
    const { agent_name, difficulty } = req.body;

    // Validate input
    if (!agent_name || !difficulty) {
        return res.status(400).json({ error: 'Agent name and difficulty are required.' });
    }

    // Fetch challenges and filter by difficulty
    const challenges = getChallenges();
    const filteredChallenges = challenges.filter(challenge => challenge.difficulty === difficulty);

    // Build session response matching original API contract
    const session_id = `session_${Date.now()}_${Math.random().toString(36).slice(2)}`;
    const categories = Array.from(
        new Set(
            filteredChallenges
                .map((challenge: any) => (challenge && (challenge as any).category) || null)
                .filter((category: string | null) => category !== null)
        )
    );
    const total_challenges = filteredChallenges.length;
    const expires_at = new Date(Date.now() + 60 * 60 * 1000).toISOString();

    res.json({
        session_id,
        agent_name,
        categories,
        total_challenges,
        expires_at,
        challenges: filteredChallenges,
    });
});

app.listen(PORT, () => {
    console.log(`Benchmark API listening at http://localhost:${PORT}`);
});