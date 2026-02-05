import express from 'express';

const app = express();
app.use(express.json());

const challenges = [
  { id: 1, difficulty: 'easy', question: 'What is 2 + 2?' },
  { id: 2, difficulty: 'medium', question: 'What is the capital of France?' },
  { id: 3, difficulty: 'hard', question: 'Explain quantum mechanics.' },
];

app.post('/api/v1/challenge/start', (req, res) => {
  const { agent_name, difficulty } = req.body;
  if (!agent_name) {
    return res.status(400).send({ error: 'Agent name is required.' });
  }

  const filteredChallenges = difficulty 
    ? challenges.filter(challenge => challenge.difficulty === difficulty) 
    : challenges;

  return res.send({ agent_name, challenges: filteredChallenges });
});

app.listen(3000, () => {
  console.log('Benchmark API listening on port 3000');
});