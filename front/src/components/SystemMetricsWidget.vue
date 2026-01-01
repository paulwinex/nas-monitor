<template>
  <MetricsPanel :cols="2" min-col-width="200px">
    <template #title>
      <span class="text-subtitle2 text-weight-bolder text-blue-4 uppercase tracking-1">System</span>
    </template>

    <template #header-right>
      <div class="text-mono text-grey-5" style="font-size: 11px;">
        UPTIME: <span class="text-white q-ml-xs">{{ formattedUptime }}</span>
      </div>
      <q-btn icon="info" size="sm" class="q-ml-md" dense color="grey" flat />
    </template>


    <MetricBaseWidget
      label="CPU" :value="sysState.cpu.load + '%'"
      :temp="sysState.cpu.temp" :progress="sysState.cpu.load/100"
      :history="sysState.cpu.history" color="#2E93FA"
      @click="handleWidgetClick"
    />

    <MetricBaseWidget
      label="RAM" :value="sysState.ram.used + ' GB'"
      :temp="sysState.ram.temp" :progress="sysState.ram.used/sysState.ram.total"
      :history="sysState.ram.history" color="#00E396"
      @click="handleWidgetClick"
    />

    <NetworkWidget
      :upSpeed="sysState.net.up + ' MB/s'" :downSpeed="sysState.net.down + ' MB/s'"
      :upHistory="sysState.net.upHistory" :downHistory="sysState.net.downHistory"
      @click="handleWidgetClick"
    />

    <DiskUsageWidget
      :path="sysState.osDisk.path" :temp="sysState.osDisk.temp"
      :used="sysState.osDisk.used" :total="sysState.osDisk.total"
      @click="handleWidgetClick"
    />
  </MetricsPanel>
</template>

<script setup>
import { reactive, onMounted, onUnmounted, computed, ref } from 'vue';
import MetricBaseWidget from './MetricBaseWidget.vue';
import NetworkWidget from './NetworkWidget.vue';
import DiskUsageWidget from './DiskUsageWidget.vue';
import MetricsPanel from "./MetricsPanel.vue";

const sysState = reactive({
  cpu: { load: 0, temp: 0, history: Array(40).fill(0) },
  ram: { used: 0, total: 32, temp: 0, history: Array(40).fill(0) },
  net: { up: 0, down: 0, upHistory: Array(40).fill(0), downHistory: Array(40).fill(0) },
  osDisk: { path: '/dev/nvme', used: 120, total: 500, temp: 31 }
});

const handleWidgetClick = (id) => {
  console.log('Widget clicked:', id);
  // Здесь может быть вызов модального окна или роутинг
};

// ... (остальная логика updateData и таймеров без изменений)
const updateData = () => {
  sysState.cpu.load = Math.floor(Math.random() * 100);
  sysState.cpu.temp = 40 + Math.floor(Math.random() * 20);
  sysState.cpu.history.push(sysState.cpu.load);
  sysState.cpu.history.shift();

  sysState.ram.used = +(10 + Math.random() * 10).toFixed(1);
  sysState.ram.temp = 35 + Math.floor(Math.random() * 10);
  sysState.ram.history.push(sysState.ram.used);
  sysState.ram.history.shift();

  sysState.net.up = +(Math.random() * 5).toFixed(1);
  sysState.net.down = +(Math.random() * 50).toFixed(1);
  sysState.net.upHistory.push(sysState.net.up);
  sysState.net.downHistory.push(sysState.net.down);
  sysState.net.upHistory.shift();
  sysState.net.downHistory.shift();
};

const uptimeSeconds = ref(1052100);
const formattedUptime = computed(() => {
  const d = Math.floor(uptimeSeconds.value / 86400);
  const h = Math.floor((uptimeSeconds.value % 86400) / 3600);
  return `${d}d ${h}h`;
});

let timer;
onMounted(() => {
  updateData();
  timer = setInterval(updateData, 5000);
  setInterval(() => uptimeSeconds.value++, 1000);
});
onUnmounted(() => clearInterval(timer));
</script>

<style scoped>
.bg-dark-page { background: #0a0a0a; }
.bg-header { background: #121212; }
.border-bottom-dark { border-bottom: 1px solid #1f1f1f; }
.system-metrics-widget { border: 1px solid #1f1f1f; border-radius: 4px; overflow: hidden; }
.metrics-grid {
  display: grid;
  grid-template-rows: repeat(2, 48px);
  grid-auto-flow: column;
  grid-auto-columns: minmax(220px, 1fr);
  gap: 8px;
}
</style>
