<template>

        <q-card class="zfs-pool-widget bg-dark-page text-white shadow-2" bordered>

          <div class="row items-center q-px-md q-py-xs border-bottom-dark bg-header">
            <div class="col-6">
              <span class="text-subtitle2 text-weight-bolder text-blue-4 uppercase tracking-1">{{ poolData.name }}</span>
              <q-badge color="positive" class="q-ml-sm text-weight-bold" label="ONLINE" size="10px" />
            </div>
            <div class="col-6 flex justify-end items-center">
              <span class="text-grey-5 q-mr-sm" style="font-size: 11px;">{{ poolData.usedSize }} / {{ poolData.totalSize }}</span>
              <div style="width: 50px"><q-linear-progress :value="0.6" color="blue-6" track-color="grey-9" /></div>
            </div>
          </div>

          <div class="q-pa-sm">
            <div class="disk-grid">
              <q-card
                v-for="(disk, index) in poolData.disks" :key="disk.sn" flat
                class="disk-item bg-disk border-dark-thin relative-position cursor-pointer"
                :class="{ 'disk-active': hoveredIndex === index }"
                @mouseenter="onDiskEnter(index)"
                @mouseleave="onDiskLeave"
              >
                <div class="row no-wrap full-height items-center">
                  <div class="col-auto flex flex-center bg-grey-10 full-height border-right-dark" style="width: 40px;">
                    <span class="text-subtitle2 text-weight-bold" :class="disk.temp > 40 ? 'text-orange' : 'text-blue-3'">{{ disk.temp }}°</span>
                  </div>
                  <div class="col q-px-sm">
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
                <div class="absolute-bottom full-width" :style="{ backgroundColor: CHART_COLORS[index % CHART_COLORS.length], height: '3px' }"></div>
              </q-card>
            </div>
          </div>

          <div class="q-px-sm q-pb-sm">
            <div class="chart-box bg-dark-page rounded-borders border-dark-thin relative-position">
              <div class="absolute-top-right q-pa-xs z-top">
                <q-btn-toggle
                  v-model="timeRange"
                  flat dense toggle-color="blue-4" color="grey-8" size="9px" padding="2px 6px"
                  :options="[{label: '1H', value: '1h'}, {label: '1D', value: '1d'}, {label: '1W', value: '1w'}]"
                  class="bg-header border-dark-thin"
                />
              </div>
              <div class="q-pt-md">
                <apexchart
                  ref="chartRef"
                  type="line"
                  height="160"
                  :options="chartOptions"
                  :series="chartSeries"
                />
              </div>
            </div>
          </div>
        </q-card>

</template>

<script setup>
import { ref, computed, watch } from 'vue';
import VueApexCharts from 'vue3-apexcharts';

const apexchart = VueApexCharts;
const chartRef = ref(null);
const CHART_COLORS = ['#2E93FA', '#00E396', '#FEB019', '#FF4560', '#775DD0', '#546E7A'];

const timeRange = ref('1h');
const hoveredIndex = ref(null);
let restoreTimer = null;

const poolData = {
  name: 'STORAGE_POOL_A',
  disks: [
    { path: '/dev/sda', model: 'HGST Ultrastar', sn: 'K7G8L9P0', temp: 32, smart: 'OK' },
    { path: '/dev/sdb', model: 'HGST Ultrastar', sn: 'K7G8L9P1', temp: 33, smart: 'OK' },
    { path: '/dev/sdc', model: 'HGST Ultrastar', sn: 'K7G8L9P2', temp: 41, smart: 'OK' },
    { path: '/dev/sdd', model: 'HGST Ultrastar', sn: 'K7G8L9P3', temp: 34, smart: 'OK' },
    { path: '/dev/sde', model: 'Crucial MX500', sn: 'CT500MX1', temp: 29, smart: 'OK' },
    { path: '/dev/sdf', model: 'Crucial MX500', sn: 'CT500MX2', temp: 30, smart: 'OK' },
  ],
  usedSize: '31.2 TB', totalSize: '48.0 TB'
};

// 1. Генерация данных в зависимости от диапазона
const chartSeries = computed(() => {
  const now = Date.now();
  let points = 20;
  let duration = 3600000; // 1h
  if (timeRange.value === '1d') duration = 86400000;
  if (timeRange.value === '1w') duration = 604800000;

  const step = duration / points;

  return poolData.disks.map(disk => ({
    name: disk.path,
    data: Array.from({ length: points }, (_, i) => [
      now - (points - i) * step,
      disk.temp + Math.floor(Math.random() * 5)
    ])
  }));
});

// 2. Статичные опции графика (без hoveredIndex)
const chartOptions = computed(() => {
  return {
    theme: { mode: 'dark' },
    chart: {
      background: 'transparent',
      toolbar: { show: false },
      animations: { enabled: false } // Полностью отключаем анимацию появления
    },
    colors: CHART_COLORS,
    stroke: { curve: 'smooth', width: 2 },
    grid: { borderColor: '#1a1a1a', padding: { left: 10, right: 20 } },
    xaxis: {
      type: 'datetime',
      labels: {
        show: true,
        style: { colors: '#444', fontSize: '9px' },
        format: timeRange.value === '1h' ? 'HH:mm' : 'dd MMM'
      }
    },
    yaxis: {
      min: 20, max: 60, tickAmount: 4,
      labels: { style: { colors: '#444' }, formatter: (v) => v.toFixed(0) }
    },
    legend: { show: false },
    tooltip: { theme: 'dark' }
  };
});

// 3. Логика подсветки (через API, чтобы не ломать реактивность кнопок)
const updateChartOpacity = (idx) => {
  if (!chartRef.value) return;

  const opacities = poolData.disks.map((_, i) => (idx === null ? 1 : (idx === i ? 1 : 0.1)));
  const widths = poolData.disks.map((_, i) => (idx === null ? 2 : (idx === i ? 3 : 1)));

  chartRef.value.updateOptions({
    fill: { opacity: opacities },
    stroke: { width: widths },
    tooltip: { enabled: idx === null }
  }, false, false); // false, false - не перерисовывать данные и не анимировать
};

const onDiskEnter = (index) => {
  if (restoreTimer) clearTimeout(restoreTimer);
  hoveredIndex.value = index;
  updateChartOpacity(index);
};

const onDiskLeave = () => {
  restoreTimer = setTimeout(() => {
    hoveredIndex.value = null;
    updateChartOpacity(null);
  }, 100);
};

// Сброс подсветки при смене диапазона (чтобы не забаговалось)
watch(timeRange, () => {
  hoveredIndex.value = null;
});
</script>

<style scoped>
.bg-dark-page { background: #0a0a0a; }
.bg-header { background: #121212; }
.bg-disk { background: #161616; }
.border-dark-thin { border: 1px solid #1f1f1f !important; }
.border-bottom-dark { border-bottom: 1px solid #1f1f1f; }
.border-right-dark { border-right: 1px solid #1f1f1f; }
.zfs-pool-widget { border: 1px solid #1f1f1f; border-radius: 4px; overflow: hidden; }
.disk-grid { display: grid; grid-template-rows: repeat(2, 48px); grid-auto-flow: column; grid-auto-columns: minmax(180px, 1fr); gap: 8px; padding: 2px; overflow-x: auto; }
.disk-item { border-radius: 3px; opacity: 0.85; transition: background 0.2s; }
.disk-active { background: #222 !important; opacity: 1; box-shadow: inset 0 0 0 1px #333; z-index: 2; }
.chart-box { border: 1px solid #1f1f1f; }
.z-top { z-index: 100; }
.text-mono { font-family: 'JetBrains Mono', monospace; }
</style>
