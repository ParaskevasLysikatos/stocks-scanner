<template>
  <div class="custom-scan-section">
    <h2 class="section-title">Custom Ticker Scanner</h2>
    <p class="section-subtitle">Enter up to 10 specific tickers to analyze</p>

    <div class="chip-input-area">
      <div class="chips-container">
        <span class="chip" v-for="(ticker, idx) in tickers" :key="ticker">
          {{ ticker }}
          <button class="chip-remove" @click="removeTicker(idx)">&times;</button>
        </span>
        <input
          v-if="tickers.length < 10"
          v-model="inputValue"
          class="chip-input"
          type="text"
          placeholder="Type ticker and press Enter..."
          @keydown.enter.prevent="addTicker"
          @keydown.,="addTicker"
        />
      </div>
      <span class="chip-count">{{ tickers.length }}/10</span>
    </div>

    <button
      v-if="tickers.length > 0"
      class="scan-btn"
      :disabled="isScanning"
      @click="startCustomScan"
    >
      <span v-if="!isScanning">Scan Selected ({{ tickers.length }})</span>
      <span v-else>Scanning...</span>
    </button>

    <div v-if="isScanning" class="progress-section">
      <div class="progress-bar-container">
        <div class="progress-bar-fill" :style="{ width: progress + '%' }"></div>
      </div>
      <p class="progress-text">{{ progress }}% &mdash; {{ progressMessage }}</p>
    </div>

    <ResultsTable
      v-if="results.length > 0 && !isScanning"
      :results="results"
    />

    <div v-if="scanDone && results.length === 0" class="no-results">
      No valid data found for the entered tickers. Check that the symbols are correct.
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ResultsTable from './ResultsTable.vue'

const tickers = ref([])
const inputValue = ref('')
const isScanning = ref(false)
const progress = ref(0)
const progressMessage = ref('')
const results = ref([])
const scanDone = ref(false)

function addTicker() {
  const val = inputValue.value.trim().toUpperCase().replace(',', '')
  if (!val || tickers.value.includes(val) || tickers.value.length >= 10) return
  tickers.value.push(val)
  inputValue.value = ''
}

function removeTicker(idx) {
  tickers.value.splice(idx, 1)
}

async function startCustomScan() {
  isScanning.value = true
  progress.value = 0
  progressMessage.value = 'Initializing...'
  results.value = []
  scanDone.value = false

  try {
    const response = await fetch('/api/scan/custom', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify({ tickers: tickers.value }),
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
          try {
            const data = JSON.parse(eventData)
            if (eventType === 'progress') {
              progress.value = data.percent
              progressMessage.value = data.message
            } else if (eventType === 'result') {
              results.value = data.stocks
            }
          } catch (e) {
            console.warn('Failed to parse SSE event:', eventData)
          }
          eventType = ''
          eventData = ''
        }
      }
    }
  } catch (e) {
    progressMessage.value = `Scan failed: ${e.message}`
  } finally {
    isScanning.value = false
    scanDone.value = true
  }
}
</script>

<style scoped>
.custom-scan-section {
  margin-top: 3rem;
  padding-top: 2rem;
  border-top: 1px solid var(--border);
}

.section-title {
  font-size: 1.3rem;
  color: var(--accent-blue);
  margin-bottom: 0.25rem;
}

.section-subtitle {
  color: var(--text-secondary);
  font-size: 0.85rem;
  margin-bottom: 1rem;
}

.chip-input-area {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.chips-container {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.5rem 0.75rem;
  flex: 1;
  min-height: 42px;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  background: var(--bg-card);
  border: 1px solid var(--accent-blue);
  color: var(--accent-blue);
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: 700;
  font-family: 'Courier New', monospace;
}

.chip-remove {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 1rem;
  padding: 0 0.15rem;
  line-height: 1;
}

.chip-remove:hover {
  color: var(--accent-red);
}

.chip-input {
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 0.9rem;
  outline: none;
  min-width: 180px;
  font-family: 'Courier New', monospace;
}

.chip-input::placeholder {
  color: var(--text-secondary);
  font-family: 'Segoe UI', system-ui, sans-serif;
}

.chip-count {
  color: var(--text-secondary);
  font-size: 0.8rem;
  white-space: nowrap;
}

.scan-btn {
  background: linear-gradient(135deg, #2196f3, #42a5f5);
  color: white;
  border: none;
  padding: 0.7rem 2rem;
  font-size: 1rem;
  font-weight: 700;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 1rem;
}

.scan-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(33, 150, 243, 0.3);
}

.scan-btn:disabled {
  background: var(--bg-card);
  color: var(--text-secondary);
  cursor: not-allowed;
}

.progress-section {
  margin-bottom: 1.5rem;
  max-width: 600px;
}

.progress-bar-container {
  width: 100%;
  height: 8px;
  background: var(--bg-card);
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #2196f3, #00c853);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.progress-text {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: var(--text-primary);
}

.no-results {
  text-align: center;
  color: var(--text-secondary);
  padding: 1.5rem;
  font-size: 0.9rem;
  border: 1px dashed var(--border);
  border-radius: 8px;
  margin-top: 1rem;
}
</style>
