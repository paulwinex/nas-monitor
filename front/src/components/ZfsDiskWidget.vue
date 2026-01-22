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
        <span class="text-subtitle2 text-weight-bold" :class="currentTemp > 45 ? 'text-orange' : 'text-blue-3'">
          {{ currentTemp }}°
        </span>
      </div>

      <div class="col q-px-sm relative-position full-height flex items-center">
        <div class="absolute-full" style="opacity: 0.2; pointer-events: none; margin-top: 12px;">
          <apexchart
            v-if="tempHistory.length > 0"
            type="area"
            height="100%"
            width="100%"
            :options="chartOptions"
            :series="[{ data: tempHistory }]"
          />
        </div>

        <div class="full-width relative-position" style="z-index: 2;">
          <div class="row justify-between no-wrap">
            <div class="text-blue-4 text-weight-bold text-mono" style="font-size: 11px;">{{ diskPath }}</div>
            <div class="text-grey-4 ellipsis q-ml-xs" style="font-size: 10px; max-width: 90px;">{{ diskModel }}</div>
          </div>
          <div class="row justify-between no-wrap">
            <div class="text-grey-6 text-mono" style="font-size: 9px;">SN: {{ disk.name }}</div>
            <q-badge :color="smartStatusColor" rounded style="width: 5px; height: 5px;" />
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
import { useDeviceStore } from 'src/stores/deviceStore';
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

const deviceStore = useDeviceStore();

// Get current temperature
const currentTemp = computed(() => {
  const temp = deviceStore.getLatestValue(props.disk.name, 'temp');
  return temp !== undefined ? Math.round(temp) : '--';
});

// Get SMART health status
const smartHealth = computed(() => {
  const health = deviceStore.getLatestValue(props.disk.name, 'health');
  return health !== undefined ? health : 0;
});

const smartStatusColor = computed(() => {
  const health = smartHealth.value;
  if (health === 0) return 'positive';  // OK
  if (health === 1) return 'warning';   // Warning
  return 'negative';  // Critical or Failed
});

// Get temperature history from metrics
const tempHistory = computed(() => {
  const metrics = deviceStore.getDeviceMetrics(props.disk.name);
  const tempMetrics = metrics
    .filter(m => m.label === 'temp')
    .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
    .slice(-40)  // Last 40 points
    .map(m => Math.round(m.value));
  
  return tempMetrics.length > 0 ? tempMetrics : [currentTemp.value];
});

// Get disk details
const diskPath = computed(() => props.disk.details?.path || '');
const diskModel = computed(() => props.disk.details?.model || '');

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
  stroke: { curve: 'smooth', width: 1 },
  fill: { type: 'solid', opacity: 0.2 },
  colors: [props.accentColor],
  tooltip: { enabled: false },
  yaxis: {
    min: 0,
    max: 70
  }
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
