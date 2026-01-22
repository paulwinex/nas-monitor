<template>
  <q-card
    flat v-ripple
    class="metric-item bg-disk border-dark-thin relative-position overflow-hidden cursor-pointer"
    @click="$emit('click', 'network')"
  >
    <div class="row no-wrap full-height items-center relative-position z-top">
      <div class="col-auto flex flex-center bg-grey-10 full-height border-right-dark" style="width: 40px; z-index: 3;">
        <q-icon name="swap_vertical_circle" color="blue-4" size="20px" />
      </div>
      <div class="col relative-position full-height flex items-center">
        <div class="absolute-full" style="opacity: 0.25; pointer-events: none; margin-top: 5px;">
          <apexchart type="area" height="100%" width="100%" :options="chartOptions" :series="series" />
        </div>
        <div class="full-width q-px-sm relative-position" style="z-index: 2;">
          <div class="row justify-between items-center no-wrap">
            <div class="text-blue-4 text-mono" style="font-size: 11px;">NET</div>
            <div class="column items-end">
              <div class="text-orange-3 text-weight-bold text-mono" style="font-size: 11px; line-height: 1;">{{ formatSpeed(upSpeed) }} <q-icon name="arrow_drop_up" size="xs"/></div>
              <div class="text-green-3 text-weight-bold text-mono q-mt-xs" style="font-size: 11px; line-height: 1;">{{ formatSpeed(downSpeed) }} <q-icon name="arrow_drop_down" size="xs"/></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </q-card>
</template>

<script setup>
import { computed } from 'vue';
import VueApexCharts from 'vue3-apexcharts';

const apexchart = VueApexCharts;
const props = defineProps(['upSpeed', 'downSpeed', 'upHistory', 'downHistory']);
defineEmits(['click']);

const formatSpeed = (val) => {
  if (val === undefined || val === null) return '0 KB/s';
  const num = parseFloat(val);
  if (isNaN(num)) return val;
  if (num >= 1024) {
    return (num / 1024).toFixed(1) + ' MB/s';
  }
  return num.toFixed(1) + ' KB/s';
};

const series = computed(() => [
  { name: 'Down', data: props.downHistory || [] },
  { name: 'Up', data: props.upHistory || [] }
]);

const chartOptions = {
  chart: { sparkline: { enabled: true }, animations: { enabled: false }, background: 'transparent' },
  stroke: { curve: 'smooth', width: 1 },
  colors: ['#00E396', '#FEB019'],
  fill: { type: 'solid', opacity: 0.15 },
  tooltip: { enabled: false }
};
</script>

<style scoped>
.bg-disk { background: #161616; }
.border-dark-thin { border: 1px solid #1f1f1f !important; }
.border-right-dark { border-right: 1px solid #1f1f1f; }
.metric-item { height: 48px; border-radius: 3px; }
.z-top { z-index: 5; }
.text-mono { font-family: 'JetBrains Mono', monospace; }
</style>
