import express from 'express';
import { getChallenges } from './challenges';

const app = express();
app.use(express.json());

app.post('/api/v1/challenge/start', (req, res) => {
  const { agent_name, difficulty } = req.body;

  // Fetch challenges and filter by difficulty if specified
  let challenges = getChallenges();
  if (difficulty) {
    challenges = challenges.filter(challenge => challenge.difficulty === difficulty);
  }

  res.json({ challenges });
});

// Other existing routes...

app.listen(3000, () => {
  console.log('Benchmark API running on port 3000');
});