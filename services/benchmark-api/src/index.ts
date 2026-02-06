import express from 'express';
import { getChallenges } from './challengeService'; // Hypothetical service to fetch challenges

const app = express();
app.use(express.json());

app.post('/api/v1/challenge/start', (req, res) => {
    const { agent_name, difficulty } = req.body;

    // Validate input
    if (!agent_name) {
        return res.status(400).send({ error: 'agent_name is required' });
    }

    // Fetch challenges
    let challenges = getChallenges(); // Fetch all challenges first

    // Filter by difficulty if specified
    if (difficulty) {
        challenges = challenges.filter(challenge => challenge.difficulty === difficulty);
    }

    if (challenges.length === 0) {
        return res.status(404).send({ error: 'No challenges found for the specified difficulty' });
    }

    // Start the first challenge (or handle selection logic)
    const challenge = challenges[0];
    res.send({ challenge });
});

export default app;