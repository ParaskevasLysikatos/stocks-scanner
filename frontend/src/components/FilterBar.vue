<template>
  <div class="filter-bar">
    <h3 class="filter-title">Filters</h3>
    <div class="filter-controls">

      <div class="filter-group">
        <label class="filter-label">Max Price</label>
        <div class="price-input-wrapper">
          <span class="price-prefix">$</span>
          <input
            type="number"
            class="price-input"
            :value="filters.maxPrice"
            @input="update('maxPrice', Number($event.target.value))"
            min="1"
            step="50"
          />
        </div>
      </div>

      <div class="filter-group">
        <label class="filter-label">Analyst Rating</label>
        <div class="rating-checks">
          <label class="check-item" v-for="r in ratingOptions" :key="r.value">
            <input
              type="checkbox"
              :checked="filters.ratings.includes(r.value)"
              @change="toggleRating(r.value)"
            />
            <span class="check-label" :class="r.cls">{{ r.label }}</span>
          </label>
        </div>
      </div>

      <div class="filter-group">
        <label class="check-item">
          <input
            type="checkbox"
            :checked="filters.lowerHalfOnly"
            @change="update('lowerHalfOnly', $event.target.checked)"
          />
          <span class="check-label">52W Lower Half Only</span>
        </label>
      </div>

    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  filters: { type: Object, required: true },
})

const emit = defineEmits(['update:filters'])

const ratingOptions = [
  { value: 'strong_buy', label: 'Strong Buy', cls: 'rating-buy' },
  { value: 'buy', label: 'Buy', cls: 'rating-buy' },
  { value: 'hold', label: 'Hold', cls: 'rating-hold' },
  { value: 'sell', label: 'Sell', cls: 'rating-sell' },
]

function update(key, value) {
  emit('update:filters', { ...props.filters, [key]: value })
}

function toggleRating(value) {
  const current = [...props.filters.ratings]
  const idx = current.indexOf(value)
  if (idx >= 0) {
    current.splice(idx, 1)
  } else {
    current.push(value)
  }
  emit('update:filters', { ...props.filters, ratings: current })
}
</script>

<style scoped>
.filter-bar {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1rem 1.25rem;
  margin-bottom: 1.5rem;
}

.filter-title {
  font-size: 0.85rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.75rem;
}

.filter-controls {
  display: flex;
  align-items: flex-start;
  gap: 2rem;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.filter-label {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.price-input-wrapper {
  display: flex;
  align-items: center;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 0.3rem 0.5rem;
  width: 120px;
}

.price-prefix {
  color: var(--text-secondary);
  margin-right: 0.3rem;
  font-size: 0.9rem;
}

.price-input {
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 0.9rem;
  width: 100%;
  outline: none;
  font-family: 'Courier New', monospace;
}

.price-input::-webkit-inner-spin-button {
  opacity: 0.5;
}

.rating-checks {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.check-item {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  cursor: pointer;
  font-size: 0.85rem;
}

.check-item input[type="checkbox"] {
  accent-color: var(--accent-green);
  cursor: pointer;
}

.check-label {
  color: var(--text-primary);
}

.rating-buy { color: var(--accent-green); }
.rating-hold { color: #ffc107; }
.rating-sell { color: var(--accent-red); }
</style>
