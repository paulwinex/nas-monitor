<template>
  <q-card class="metrics-panel bg-dark-page text-white shadow-2" bordered>
    <div class="row items-center q-px-md q-py-xs border-bottom-dark bg-header header-height">
      <div class="col-6 flex items-center">
        <slot name="title"></slot>
      </div>
      <div class="col-6 flex justify-end items-center">
        <slot name="header-right"></slot>
      </div>
    </div>

    <div class="q-pa-sm">
      <div
        class="base-metrics-grid"
        :style="gridStyle"
      >
        <slot></slot>
      </div>
    </div>
  </q-card>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  // Количество строк (по умолчанию 2, как в ваших примерах)
  rows: {
    type: Number,
    default: 2
  },
  // Минимальная ширина колонки
  minColWidth: {
    type: String,
    default: '200px'
  }
});

const gridStyle = computed(() => ({
  gridTemplateRows: `repeat(${props.rows}, 48px)`,
  gridAutoColumns: `minmax(${props.minColWidth}, 1fr)`
}));
</script>

<style scoped>
.bg-dark-page { background: #0a0a0a; }
.bg-header { background: #121212; }
.border-bottom-dark { border-bottom: 1px solid #1f1f1f; }
.metrics-panel { border: 1px solid #1f1f1f; border-radius: 4px; overflow: hidden; }

.header-height {
  height: 32px; /* Фиксируем высоту заголовка для идеального выравнивания */
}

.base-metrics-grid {
  display: grid;
  grid-auto-flow: column;
  gap: 8px;
  overflow-x: auto;
  /* Прячем скроллбар, если он не нужен, но оставляем функционал */
  scrollbar-width: thin;
  scrollbar-color: #333 transparent;
}
</style>
