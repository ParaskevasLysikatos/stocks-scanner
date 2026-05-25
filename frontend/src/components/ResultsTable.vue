<template>
  <div class="results-section">
    <h2 class="results-title">Top 10 Speculative Picks</h2>
    <div class="table-wrapper">
      <table class="results-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Ticker</th>
            <th>Company</th>
            <th>Score</th>
            <th>Technical</th>
            <th>Volume</th>
            <th>Sentiment</th>
            <th>Fundamentals</th>
            <th>Notes</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="stock in results" :key="stock.ticker">
            <td class="rank">{{ stock.rank }}</td>
            <td class="ticker">{{ stock.ticker }}</td>
            <td class="company">{{ stock.company }}</td>
            <td class="score">
              <span class="score-badge" :class="scoreClass(stock.score)">
                {{ stock.score }}
              </span>
            </td>
            <td>{{ stock.technical_score }}/35</td>
            <td>{{ stock.volume_score }}/25</td>
            <td>{{ stock.sentiment_score }}/25</td>
            <td>{{ stock.fundamentals_score }}/15</td>
            <td class="notes">{{ stock.notes }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
defineProps({
  results: { type: Array, required: true },
})

function scoreClass(score) {
  if (score >= 70) return 'score-high'
  if (score >= 50) return 'score-mid'
  return 'score-low'
}
</script>

<style scoped>
.results-section {
  margin-top: 2rem;
}

.results-title {
  font-size: 1.3rem;
  margin-bottom: 1rem;
  color: var(--accent-green);
}

.table-wrapper {
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid var(--border);
}

.results-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.results-table th,
.results-table td {
  padding: 0.75rem 1rem;
  text-align: left;
  border-bottom: 1px solid var(--border);
}

.results-table th {
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.results-table tbody tr:hover {
  background: var(--bg-card);
}

.rank {
  font-weight: 700;
  color: var(--text-secondary);
}

.ticker {
  font-weight: 700;
  color: var(--accent-blue);
  font-family: 'Courier New', monospace;
}

.company {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.score-badge {
  display: inline-block;
  padding: 0.25rem 0.6rem;
  border-radius: 4px;
  font-weight: 700;
  font-size: 0.85rem;
}

.score-high {
  background: rgba(0, 200, 83, 0.2);
  color: var(--accent-green);
}

.score-mid {
  background: rgba(33, 150, 243, 0.2);
  color: var(--accent-blue);
}

.score-low {
  background: rgba(255, 82, 82, 0.15);
  color: var(--accent-red);
}

.notes {
  font-size: 0.8rem;
  color: var(--text-secondary);
  max-width: 200px;
}
</style>
