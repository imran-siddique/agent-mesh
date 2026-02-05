import express from 'express';
import { getChallenges } from './challenges';

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

app.post('/api/v1/challenge/start', (req, res) => {
    const { agent_name, difficulty } = req.body;
    const challenges = getChallenges(difficulty);
    res.json({ agent_name, challenges });
});

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});