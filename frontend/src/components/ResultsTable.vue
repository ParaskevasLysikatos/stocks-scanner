<template>
  <div class="results-section">
    <h2 class="results-title">Top {{ results.length }} Speculative Picks</h2>
    <div class="table-wrapper">
      <table class="results-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Ticker</th>
            <th>Company</th>
            <th>Score</th>
            <th>Price</th>
            <th>52W Range</th>
            <th>Target</th>
            <th>Rating</th>
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
            <td class="price">${{ formatPrice(stock.current_price) }}</td>
            <td class="range">
              <span class="range-text">
                ${{ formatPrice(stock.week52_low) }} — ${{ formatPrice(stock.week52_high) }}
              </span>
              <div class="range-bar" v-if="stock.week52_low && stock.week52_high && stock.current_price">
                <div
                  class="range-bar-pos"
                  :style="{ left: rangePosition(stock) + '%' }"
                ></div>
              </div>
            </td>
            <td class="target">
              <template v-if="stock.target_price">
                <span>${{ formatPrice(stock.target_price) }}</span>
                <span
                  v-if="stock.upside_pct != null"
                  class="upside"
                  :class="stock.upside_pct >= 0 ? 'upside-pos' : 'upside-neg'"
                >
                  {{ stock.upside_pct >= 0 ? '+' : '' }}{{ stock.upside_pct }}%
                </span>
                <span class="analyst-count" v-if="stock.num_analysts">
                  ({{ stock.num_analysts }} analysts)
                </span>
              </template>
              <span v-else class="na">N/A</span>
            </td>
            <td>
              <span class="rating-badge" :class="ratingClass(stock.recommendation)">
                {{ formatRating(stock.recommendation) }}
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

function formatPrice(val) {
  if (val == null) return '—'
  return Number(val).toFixed(2)
}

function rangePosition(stock) {
  const range = stock.week52_high - stock.week52_low
  if (range <= 0) return 50
  const pos = ((stock.current_price - stock.week52_low) / range) * 100
  return Math.max(0, Math.min(100, pos))
}

function ratingClass(rec) {
  if (!rec || rec === 'N/A') return 'rating-na'
  if (rec === 'strong_buy' || rec === 'buy') return 'rating-buy'
  if (rec === 'hold') return 'rating-hold'
  return 'rating-sell'
}

function formatRating(rec) {
  if (!rec || rec === 'N/A') return 'N/A'
  return rec.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())
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
  font-size: 0.85rem;
}

.results-table th,
.results-table td {
  padding: 0.6rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}

.results-table th {
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 0.75rem;
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
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.score-badge {
  display: inline-block;
  padding: 0.2rem 0.5rem;
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

.price {
  font-weight: 600;
  font-family: 'Courier New', monospace;
}

.range {
  min-width: 140px;
}

.range-text {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.range-bar {
  position: relative;
  height: 4px;
  background: var(--bg-card);
  border-radius: 2px;
  margin-top: 4px;
}

.range-bar-pos {
  position: absolute;
  top: -3px;
  width: 10px;
  height: 10px;
  background: var(--accent-blue);
  border-radius: 50%;
  transform: translateX(-50%);
}

.target {
  min-width: 120px;
}

.upside {
  display: inline-block;
  margin-left: 0.3rem;
  font-weight: 700;
  font-size: 0.8rem;
}

.upside-pos {
  color: var(--accent-green);
}

.upside-neg {
  color: var(--accent-red);
}

.analyst-count {
  display: block;
  font-size: 0.7rem;
  color: var(--text-secondary);
}

.rating-badge {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: capitalize;
}

.rating-buy {
  background: rgba(0, 200, 83, 0.2);
  color: var(--accent-green);
}

.rating-hold {
  background: rgba(255, 193, 7, 0.2);
  color: #ffc107;
}

.rating-sell {
  background: rgba(255, 82, 82, 0.15);
  color: var(--accent-red);
}

.rating-na {
  background: var(--bg-card);
  color: var(--text-secondary);
}

.na {
  color: var(--text-secondary);
}

.notes {
  font-size: 0.75rem;
  color: var(--text-secondary);
  max-width: 220px;
  white-space: normal;
}
</style>
