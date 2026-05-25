<template>
  <div class="scan-section">
    <button
      class="scan-button"
      :disabled="isScanning"
      @click="$emit('startScan')"
    >
      <span v-if="!isScanning">Scan Market</span>
      <span v-else>Scanning...</span>
    </button>

    <div v-if="isScanning" class="progress-section">
      <div class="progress-bar-container">
        <div
          class="progress-bar-fill"
          :style="{ width: progress + '%' }"
        ></div>
      </div>
      <p class="progress-text">{{ progress }}% &mdash; {{ progressMessage }}</p>
      <p class="progress-hint">
        This scan analyzes ~2,700 tickers across multiple signals.
        Expected duration: 10-15 minutes. Please keep this tab open.
      </p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  isScanning: { type: Boolean, required: true },
  progress: { type: Number, default: 0 },
  progressMessage: { type: String, default: '' },
})

defineEmits(['startScan'])
</script>

<style scoped>
.scan-section {
  text-align: center;
  margin-bottom: 2rem;
}

.scan-button {
  background: linear-gradient(135deg, #00c853, #00e676);
  color: #0f1923;
  border: none;
  padding: 1rem 3rem;
  font-size: 1.2rem;
  font-weight: 700;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.scan-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 200, 83, 0.3);
}

.scan-button:disabled {
  background: var(--bg-card);
  color: var(--text-secondary);
  cursor: not-allowed;
}

.progress-section {
  margin-top: 1.5rem;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
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
  background: linear-gradient(90deg, #00c853, #2196f3);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.progress-text {
  margin-top: 0.75rem;
  font-size: 0.9rem;
  color: var(--text-primary);
}

.progress-hint {
  margin-top: 0.5rem;
  font-size: 0.8rem;
  color: var(--text-secondary);
}
</style>
