import express from 'express';
import { getChallenges } from './challenges';

const app = express();
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

    // Return filtered challenges
    res.json({ challenges: filteredChallenges });
});

app.listen(PORT, () => {
    console.log(`Benchmark API listening at http://localhost:${PORT}`);
});