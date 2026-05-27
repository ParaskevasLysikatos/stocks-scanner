<template>
  <div id="app">
    <header class="header">
      <h1>Stock Speculation Scanner</h1>
      <p class="subtitle">S&amp;P 500 + NASDAQ 100 + Russell 2000 &bull; Technical + Volume + Sentiment + Fundamentals</p>
    </header>

    <main class="main">
      <ScanButton
        :is-scanning="isScanning"
        :progress="progress"
        :progress-message="progressMessage"
        @start-scan="startScan"
      />

      <FilterBar
        v-if="rawResults.length > 0"
        :filters="filters"
        @update:filters="filters = $event"
      />

      <ResultsTable
        v-if="filteredResults.length > 0"
        :results="filteredResults"
      />

      <div v-if="rawResults.length > 0 && filteredResults.length === 0" class="no-results">
        No stocks match the current filters. Try adjusting the criteria above.
      </div>

      <div v-if="error" class="error-banner">
        {{ error }}
      </div>
    </main>

    <footer class="footer">
      <p class="disclaimer">
        This tool is for educational and research purposes only.
        It does not constitute financial advice. All signals are speculative
        and based on publicly available data. Always do your own due diligence
        before making investment decisions.
      </p>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import ScanButton from './components/ScanButton.vue'
import FilterBar from './components/FilterBar.vue'
import ResultsTable from './components/ResultsTable.vue'

const isScanning = ref(false)
const progress = ref(0)
const progressMessage = ref('')
const rawResults = ref([])
const error = ref('')

const filters = ref({
  maxPrice: 500,
  ratings: ['strong_buy', 'buy'],
  lowerHalfOnly: true,
})

const filteredResults = computed(() => {
  return rawResults.value.filter(stock => {
    if (stock.current_price != null && stock.current_price >= filters.value.maxPrice) {
      return false
    }
    if (filters.value.ratings.length > 0 && !filters.value.ratings.includes(stock.recommendation)) {
      return false
    }
    if (filters.value.lowerHalfOnly && stock.week52_low && stock.week52_high && stock.current_price) {
      const mid = (stock.week52_low + stock.week52_high) / 2
      if (stock.current_price > mid) return false
    }
    return true
  }).map((stock, idx) => ({ ...stock, rank: idx + 1 }))
})

async function startScan() {
  isScanning.value = true
  progress.value = 0
  progressMessage.value = 'Initializing scan...'
  rawResults.value = []
  error.value = ''

  try {
    const response = await fetch('/api/scan', {
      method: 'POST',
      headers: { 'Accept': 'text/event-stream' },
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { value, done } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      const lines = buffer.split('\n')
      buffer = lines.pop()

      let eventType = ''
      let eventData = ''

      for (const rawLine of lines) {
        const line = rawLine.replace('\r', '')
        if (line.startsWith('event:')) {
          eventType = line.slice(6).trim()
        } else if (line.startsWith('data:')) {
          eventData = line.slice(5).trim()
        } else if (line === '' && eventData) {
          handleEvent(eventType, eventData)
          eventType = ''
          eventData = ''
        }
      }
    }
  } catch (e) {
    error.value = `Scan failed: ${e.message}`
  } finally {
    isScanning.value = false
  }
}

function handleEvent(type, dataStr) {
  try {
    const data = JSON.parse(dataStr)

    if (type === 'progress') {
      progress.value = data.percent
      progressMessage.value = data.message
    } else if (type === 'result') {
      rawResults.value = data.stocks
    } else if (type === 'error') {
      error.value = data.message
    }
  } catch (e) {
    console.warn('Failed to parse SSE event:', dataStr)
  }
}
</script>

<style>
:root {
  --bg-primary: #0f1923;
  --bg-secondary: #1a2332;
  --bg-card: #1e2d3d;
  --text-primary: #e0e6ed;
  --text-secondary: #8899a6;
  --accent-green: #00c853;
  --accent-blue: #2196f3;
  --accent-red: #ff5252;
  --border: #2d3f50;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  min-height: 100vh;
}

#app {
  max-width: 1600px;
  margin: 0 auto;
  padding: 2rem;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  text-align: center;
  margin-bottom: 2rem;
}

.header h1 {
  font-size: 2rem;
  color: var(--accent-green);
  margin-bottom: 0.5rem;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.main {
  flex: 1;
}

.no-results {
  text-align: center;
  color: var(--text-secondary);
  padding: 2rem;
  font-size: 0.95rem;
  border: 1px dashed var(--border);
  border-radius: 8px;
  margin-top: 1rem;
}

.error-banner {
  background: rgba(255, 82, 82, 0.15);
  border: 1px solid var(--accent-red);
  color: var(--accent-red);
  padding: 1rem;
  border-radius: 8px;
  margin-top: 1rem;
}

.footer {
  margin-top: 3rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border);
}

.disclaimer {
  color: var(--text-secondary);
  font-size: 0.8rem;
  text-align: center;
  line-height: 1.5;
}
</style>
