<template>
  <q-card class="system-metrics-widget bg-dark-page text-white shadow-2" bordered>
    <div class="row items-center q-px-md q-py-xs border-bottom-dark bg-header">
      <div class="col-6">
        <span class="text-subtitle2 text-weight-bolder text-blue-4 uppercase tracking-1">System Metrics</span>
        <q-badge color="blue-9" class="q-ml-sm text-weight-bold" label="NODE_01" size="10px" />
      </div>
      <div class="col-6 flex justify-end items-center">
        <span class="text-grey-5 text-mono text-uppercase" style="font-size: 11px;">
          UPTIME: <span class="text-white">{{ formattedUptime }}</span>
        </span>
      </div>
    </div>

    <div class="q-pa-sm">
      <div class="metrics-grid">
        <q-card
          v-for="m in metricConfigs" :key="m.id"
          flat class="metric-item bg-disk border-dark-thin relative-position cursor-pointer"
          :class="{
            'metric-active': hoveredGroup === m.id || selectedGroup === m.id,
            'metric-selected': selectedGroup === m.id
          }"
          @mouseenter="onGroupEnter(m.id)"
          @mouseleave="onGroupLeave"
          @click="toggleSelect(m.id)"
        >
          <q-icon v-if="selectedGroup === m.id" name="push_pin" class="absolute-top-right q-pa-xs text-blue-4" size="12px" />
          <div class="row no-wrap full-height items-center">
            <div class="col-auto flex flex-center bg-grey-10 full-height border-right-dark" style="width: 40px;">
              <span class="text-subtitle2 text-weight-bold" :class="m.colorClass">{{ m.temp }}°</span>
            </div>
            <div class="col q-px-sm">
              <div class="row justify-between items-center">
                <div class="text-blue-4 text-weight-bold text-mono" style="font-size: 10px;">{{ m.label }}</div>
                <div class="text-grey-4 text-mono" style="font-size: 10px;">{{ m.value }}</div>
              </div>
              <q-linear-progress :value="m.progress" :color="m.barColor" size="4px" class="q-mt-xs" />
            </div>
          </div>
          <div class="absolute-bottom full-width row" style="height: 3px;">
            <div class="col" :style="{ background: CHART_COLORS[m.colorIdx] }"></div>
            <div class="col" :style="{ background: CHART_COLORS[m.colorIdx + 1] }"></div>
          </div>
        </q-card>
      </div>
    </div>

    <div class="q-px-sm q-pb-sm">
      <div class="chart-box bg-dark-page rounded-borders border-dark-thin relative-position">
        <div class="absolute-top-right q-pa-xs z-top row q-gutter-xs items-center">
          <q-badge v-if="selectedGroup" outline color="blue-4" label="FIXED VIEW" class="q-mr-sm" size="9px" />
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
            :key="timeRange"
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
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import VueApexCharts from 'vue3-apexcharts';

const apexchart = VueApexCharts;
const chartRef = ref(null);

const CHART_COLORS = ['#2E93FA', '#66DAFF', '#00E396', '#26E7A6', '#FEB019', '#FF4560', '#775DD0', '#A389D4'];
const timeRange = ref('1h');
const hoveredGroup = ref(null);
const selectedGroup = ref(null);
let restoreTimer = null;

// --- UPTIME ---
const uptimeSeconds = ref(1052100);
let uptimeInterval = null;
const formattedUptime = computed(() => {
  const s = uptimeSeconds.value;
  const d = Math.floor(s / 86400);
  const h = Math.floor((s % 86400) / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  return `${d}d ${h}h ${m}m ${sec}s`;
});
onMounted(() => { uptimeInterval = setInterval(() => { uptimeSeconds.value++; }, 1000); });
onUnmounted(() => { clearInterval(uptimeInterval); });

// --- DATA ---
const sysData = {
  cpu: { load: 24, temp: 42 },
  ram: { used: 14.2, total: 32, temp: 38 },
  net: { up: 124, down: 840 },
  osDisk: { used: 120, total: 500, free: 380, temp: 31 }
};

const metricConfigs = computed(() => [
  { id: 'cpu', label: 'CPU', value: sysData.cpu.load + '%', temp: sysData.cpu.temp, progress: sysData.cpu.load/100, colorClass: 'text-blue-3', barColor: 'blue-4', colorIdx: 0 },
  { id: 'ram', label: 'RAM', value: sysData.ram.used + 'GB', temp: sysData.ram.temp, progress: sysData.ram.used/sysData.ram.total, colorClass: 'text-green-3', barColor: 'green-4', colorIdx: 2 },
  { id: 'net', label: 'NET', value: 'UP/DL', temp: 'ACT', progress: 0.5, colorClass: 'text-orange-3', barColor: 'orange-4', colorIdx: 4 },
  { id: 'os', label: 'DISK', value: sysData.osDisk.free + 'GB', temp: sysData.osDisk.temp, progress: sysData.osDisk.used/sysData.osDisk.total, colorClass: 'text-amber-3', barColor: 'amber-4', colorIdx: 6 }
]);

// Исправленная генерация серий с учетом диапазона
const chartSeries = computed(() => {
  const now = Date.now();
  let duration = 3600000;
  if (timeRange.value === '1d') duration = 86400000;
  if (timeRange.value === '1w') duration = 604800000;
  const step = duration / 20;

  // Все возможные серии
  const allGroups = [
    { name: 'Load', g: 'cpu', cIdx: 0 }, { name: 'Temp', g: 'cpu', cIdx: 1 },
    { name: 'Used', g: 'ram', cIdx: 2 }, { name: 'Temp', g: 'ram', cIdx: 3 },
    { name: 'Up', g: 'net', cIdx: 4 }, { name: 'Down', g: 'net', cIdx: 5 },
    { name: 'Usage', g: 'os', cIdx: 6 }, { name: 'Temp', g: 'os', cIdx: 7 }
  ];

  // Фильтруем: если группа выбрана, оставляем только её. Если нет — все.
  const activeGroups = selectedGroup.value
    ? allGroups.filter(img => img.g === selectedGroup.value)
    : allGroups;

  return activeGroups.map(group => ({
    name: group.name,
    data: Array.from({ length: 20 }, (_, idx) => [
      now - (20 - idx) * step,
      20 + Math.random() * 40
    ])
  }));
});

// Исправленные опции с динамической осью X
const chartOptions = computed(() => {
  const now = Date.now();
  let minX = now - 3600000;
  if (timeRange.value === '1d') minX = now - 86400000;
  if (timeRange.value === '1w') minX = now - 604800000;

  // Определяем набор цветов в зависимости от выбранной группы
  let currentColors = CHART_COLORS;
  if (selectedGroup.value) {
    const colorMapping = { cpu: [0,1], ram: [2,3], net: [4,5], os: [6,7] };
    const indices = colorMapping[selectedGroup.value];
    currentColors = [CHART_COLORS[indices[0]], CHART_COLORS[indices[1]]];
  }

  return {
    theme: { mode: 'dark' },
    chart: { background: 'transparent', toolbar: { show: false }, animations: { enabled: false } },
    colors: currentColors, // Применяем отфильтрованные цвета
    stroke: { curve: 'smooth', width: 2 },
    grid: { borderColor: '#1a1a1a' },
    xaxis: {
      type: 'datetime',
      min: minX,
      max: now,
      labels: { style: { colors: '#444', fontSize: '9px' } }
    },
    yaxis: {
      min: 0, max: 100, tickAmount: 4,
      labels: { style: { colors: '#444' }, formatter: (v) => Math.floor(v).toString() }
    },
    legend: { show: false },
    tooltip: {
      theme: 'dark',
      shared: true,
      intersect: false,
      y: { formatter: (v) => Math.floor(v).toString() }
    }
  };
});

// --- LOGIC (без изменений) ---
const updateChartOpacity = () => {
  if (!chartRef.value) return;

  // Если есть фиксация (selectedGroup), принудительно ставим непрозрачность 1 для всех видимых линий
  if (selectedGroup.value) {
    chartRef.value.updateOptions({
      fill: { opacity: [1, 1] }, // В fixed view у нас всегда 2 линии
      stroke: { width: [3, 3] },
      tooltip: { enabled: true }
    }, false, false);
    return;
  }

  // Логика для Hover (когда ничего не выбрано)
  const active = hoveredGroup.value;
  const seriesMeta = ['cpu','cpu','ram','ram','net','net','os','os'];
  const opacities = seriesMeta.map(g => (active === null ? 1 : (g === active ? 1 : 0.05)));
  const widths = seriesMeta.map(g => (active === null ? 2 : (g === active ? 3 : 1)));

  chartRef.value.updateOptions({
    fill: { opacity: opacities },
    stroke: { width: widths },
    tooltip: { enabled: true }
  }, false, false);
};

const onGroupEnter = (name) => {
  if (selectedGroup.value) return; // Блокируем hover эффекты, если выбран виджет
  if (restoreTimer) clearTimeout(restoreTimer);
  hoveredGroup.value = name;
  updateChartOpacity();
};

const onGroupLeave = () => {
  if (selectedGroup.value) return;
  restoreTimer = setTimeout(() => {
    hoveredGroup.value = null;
    updateChartOpacity();
  }, 300);
};

const toggleSelect = (name) => {
  if (selectedGroup.value === name) {
    selectedGroup.value = null;
    // Сброс к 8 линиям произойдет через computed,
    // но нам нужно вернуть им всем прозрачность 1
    setTimeout(() => updateChartOpacity(), 10);
  } else {
    selectedGroup.value = name;
    hoveredGroup.value = null;
    // При переключении на 2 линии, сбрасываем их прозрачность в 1
    setTimeout(() => updateChartOpacity(), 10);
  }
};

watch(timeRange, () => {
  selectedGroup.value = null;
  hoveredGroup.value = null;
  // График перерисуется из-за :key, прозрачность сбросится сама
});
</script>

<style scoped>
/* Стили остаются без изменений */
.bg-dark-page { background: #0a0a0a; }
.bg-header { background: #121212; }
.bg-disk { background: #161616; }
.border-dark-thin { border: 1px solid #1f1f1f !important; }
.border-bottom-dark { border-bottom: 1px solid #1f1f1f; }
.border-right-dark { border-right: 1px solid #1f1f1f; }
.system-metrics-widget { border: 1px solid #1f1f1f; border-radius: 4px; overflow: hidden; }
.metrics-grid { display: grid; grid-template-rows: repeat(2, 48px); grid-auto-flow: column; grid-auto-columns: minmax(180px, 1fr); gap: 8px; padding: 2px; overflow-x: auto; }
.metric-item { border-radius: 3px; opacity: 0.8; transition: all 0.2s; }
.metric-active { background: #1e1e1e !important; opacity: 1; box-shadow: inset 0 0 0 1px #333; }
.metric-selected { background: #252525 !important; box-shadow: inset 0 0 0 1px #444; border-color: #3e3e3e !important; }
.chart-box { border: 1px solid #1f1f1f; }
.z-top { z-index: 100; }
.text-mono { font-family: 'JetBrains Mono', monospace; }
</style>
