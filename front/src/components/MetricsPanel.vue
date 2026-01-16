<template>
  <q-card class="metrics-panel bg-dark-page text-white shadow-2" bordered>
    <div class="row items-center q-px-md border-bottom-dark bg-header header-height no-wrap">

      <div class="col-4 flex items-center no-wrap">
        <slot name="title"></slot>
      </div>

      <div class="col-4 flex flex-center no-wrap">
        <slot name="header-center"></slot>
      </div>

      <div class="col-4 flex justify-end items-center no-wrap">
        <slot name="header-right"></slot>
      </div>

    </div>

    <div class="q-pa-sm">
      <div
        class="base-metrics-grid"
        :style="gridStyles"
      >
        <slot></slot>
      </div>
    </div>
  </q-card>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  cols: {
    type: Number,
    default: 2
  },
  minColWidth: {
    type: String,
    default: '200px'
  }
});

const gridStyles = computed(() => ({
  '--desktop-cols': props.cols,
  '--min-width': props.minColWidth
}));
</script>

<style scoped>
.bg-dark-page { background: #0a0a0a; }
.bg-header { background: #121212; }
.border-bottom-dark { border-bottom: 1px solid #1f1f1f; }
.metrics-panel {
  border: 1px solid #1f1f1f;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 15px;
}

.header-height {
  height: 36px;
}

.base-metrics-grid {
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(auto-fit, minmax(min(var(--min-width), 100%), 1fr));
  grid-auto-rows: 48px;
}


@media (min-width: 768px) {
  .base-metrics-grid {
    grid-template-columns: repeat(var(--desktop-cols), 1fr);
  }
}

.flex-center {
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>
