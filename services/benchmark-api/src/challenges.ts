const allChallenges = [
    { id: 1, question: 'Easy question 1', difficulty: 'easy' },
    { id: 2, question: 'Medium question 2', difficulty: 'medium' },
    { id: 3, question: 'Hard question 3', difficulty: 'hard' },
];

export function getChallenges(difficulty) {
    return allChallenges.filter(challenge => !difficulty || challenge.difficulty === difficulty);
}