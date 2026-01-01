<template>
  <q-card
    flat v-ripple
    class="metric-item bg-disk border-dark-thin relative-position overflow-hidden cursor-pointer"
    @click="$emit('click', label)"
  >
    <div class="row no-wrap full-height items-center relative-position z-top">
      <div class="col-auto flex flex-center bg-grey-10 full-height border-right-dark" style="width: 40px; z-index: 3;">
        <span class="text-subtitle2 text-weight-bold" :class="temp > 50 ? 'text-orange' : 'text-blue-3'">{{ temp }}°</span>
      </div>
      <div class="col q-px-sm relative-position full-height flex items-center">
        <div class="absolute-full" style="opacity: 0.15; pointer-events: none; margin-top: 10px;">
          <apexchart type="area" height="100%" width="100%" :options="chartOptions" :series="[{ data: history }]" />
        </div>
        <div class="full-width relative-position" style="z-index: 2;">
          <div class="row justify-between items-center no-wrap">
            <div class="text-blue-4 text-weight-bold- text-mono" style="font-size: 11px;">{{ label }}</div>
            <div class="text-white text-weight-bolder- text-mono" style="font-size: 12px;">{{ value }}</div>
          </div>
          <q-linear-progress :value="progress" color="blue-6" size="3px" class="q-mt-xs" />
        </div>
      </div>
    </div>
  </q-card>
</template>

<script setup>
import { computed } from 'vue';
import VueApexCharts from 'vue3-apexcharts';

const apexchart = VueApexCharts;
const props = defineProps(['label', 'value', 'temp', 'progress', 'history', 'color']);
defineEmits(['click']);

const chartOptions = computed(() => ({
  chart: { sparkline: { enabled: true }, animations: { enabled: false }, background: 'transparent' },
  stroke: { curve: 'straight', width: 1 },
  fill: { type: 'solid', opacity: 0.2 },
  colors: [props.color || '#2E93FA'],
  tooltip: { enabled: false }
}));
</script>

<style scoped>
.bg-disk { background: #161616; }
.border-dark-thin { border: 1px solid #1f1f1f !important; }
.border-right-dark { border-right: 1px solid #1f1f1f; }
.metric-item { height: 48px; border-radius: 3px; }

.text-mono { font-family: 'JetBrains Mono', monospace; }
</style>
