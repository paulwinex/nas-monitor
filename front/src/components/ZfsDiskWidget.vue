<template>
  <q-card
    flat
    v-ripple
    class="disk-item bg-disk border-dark-thin relative-position overflow-hidden cursor-pointer"
    @click="$emit('click', disk)"
  >
    <div class="row no-wrap full-height items-center relative-position z-top">
      <div
        class="col-auto flex flex-center bg-grey-10 full-height border-right-dark"
        style="width: 40px; z-index: 3;"
      >
        <span class="text-subtitle2 text-weight-bold" :class="disk.temp > 40 ? 'text-orange' : 'text-blue-3'">
          {{ disk.temp }}°
        </span>
      </div>

      <div class="col q-px-sm relative-position full-height flex items-center">
        <div class="absolute-full" style="opacity: 0.2; pointer-events: none; margin-top: 12px;">
          <apexchart
            type="area"
            height="100%"
            width="100%"
            :options="chartOptions"
            :series="[{ data: disk.history }]"
          />
        </div>

        <div class="full-width relative-position" style="z-index: 2;">
          <div class="row justify-between no-wrap">
            <div class="text-blue-4 text-weight-bold text-mono" style="font-size: 11px;">{{ disk.path }}</div>
            <div class="text-grey-4 ellipsis q-ml-xs" style="font-size: 10px; max-width: 90px;">{{ disk.model }}</div>
          </div>
          <div class="row justify-between no-wrap">
            <div class="text-grey-6 text-mono" style="font-size: 9px;">SN: {{ disk.sn }}</div>
            <q-badge :color="disk.smart === 'OK' ? 'positive' : 'negative'" rounded style="width: 5px; height: 5px;" />
          </div>
        </div>
      </div>
    </div>

    <div
      class="absolute-bottom full-width"
      :style="{ backgroundColor: accentColor, height: '2px', opacity: 0.3 }"
    ></div>
  </q-card>
</template>

<script setup>
import { computed } from 'vue';
import VueApexCharts from 'vue3-apexcharts';

const apexchart = VueApexCharts;

const props = defineProps({
  disk: {
    type: Object,
    required: true
  },
  accentColor: {
    type: String,
    default: '#2E93FA'
  }
});

defineEmits(['click']);

const chartOptions = computed(() => ({
  chart: {
    sparkline: { enabled: true },
    animations: {
      enabled: true,
      easing: 'linear',
      dynamicAnimation: { speed: 1000 }
    },
    background: 'transparent'
  },
  stroke: { curve: 'straight', width: 1 },
  fill: { type: 'solid', opacity: 0.2 },
  colors: [props.accentColor],
  tooltip: { enabled: false }
}));
</script>

<style scoped>
.bg-disk { background: #161616; }
.border-dark-thin { border: 1px solid #1f1f1f !important; }
.border-right-dark { border-right: 1px solid #1f1f1f; }
.disk-item { border-radius: 3px; transition: background 0.2s; height: 48px; }
.disk-item:hover { background: #1d1d1d !important; }
.z-top { z-index: 5; }
.text-mono { font-family: 'JetBrains Mono', monospace; }
:deep(.apexcharts-canvas) { margin: 0 auto; }
</style>
