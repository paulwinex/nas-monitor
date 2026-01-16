<template>
  <q-dialog v-model="isOpen">
    <q-card style="min-width: 450px;" class="bg-disk text-white border-dark-thin shadow-24">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6 text-blue-4 uppercase tracking-1">System Information</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>

      <q-card-section class="q-pt-md" v-if="info">
        <q-list dark separator class="border-dark-thin rounded-borders">
          <q-item>
            <q-item-section>
              <q-item-label caption class="text-grey-6 uppercase">Hostname</q-item-label>
              <q-item-label class="text-weight-bold">{{ info.hostname }}</q-item-label>
            </q-item-section>
          </q-item>

          <q-item>
            <q-item-section>
              <q-item-label caption class="text-grey-6 uppercase">Operating System</q-item-label>
              <q-item-label>{{ info.os_pretty || info.os }}</q-item-label>
              <q-item-label caption>{{ info.os_version }}</q-item-label>
            </q-item-section>
          </q-item>

          <q-item>
            <q-item-section>
              <q-item-label caption class="text-grey-6 uppercase">Kernel Version</q-item-label>
              <q-item-label class="text-mono">{{ info.kernel }}</q-item-label>
            </q-item-section>
          </q-item>

          <q-item>
            <q-item-section>
              <q-item-label caption class="text-grey-6 uppercase">Architecture</q-item-label>
              <q-item-label>{{ info.architecture }}</q-item-label>
            </q-item-section>
          </q-item>

          <q-item>
            <q-item-section>
              <q-item-label caption class="text-grey-6 uppercase">Processor</q-item-label>
              <q-item-label>{{ info.cpu_count }} Threads <span v-if="info.cpu_freq">@ {{ info.cpu_freq }}</span></q-item-label>
            </q-item-section>
          </q-item>

          <q-item>
            <q-item-section>
              <q-item-label caption class="text-grey-6 uppercase">Boot Time</q-item-label>
              <q-item-label>{{ formatDateTime(info.boot_time) }}</q-item-label>
            </q-item-section>
          </q-item>
        </q-list>
      </q-card-section>

      <q-card-section v-else class="text-center q-pa-xl">
        <q-spinner-dots color="blue-4" size="40px" />
        <div class="text-grey-6 q-mt-sm">Loading system data...</div>
      </q-card-section>

      <q-card-actions align="right" class="q-pb-md q-px-md">
        <q-btn flat label="Close" color="blue-4" v-close-popup />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { computed, watch } from 'vue';
import { useDeviceStore } from 'src/stores/deviceStore';

const props = defineProps({
  modelValue: Boolean
});

const emit = defineEmits(['update:modelValue']);

const deviceStore = useDeviceStore();
const info = computed(() => deviceStore.systemInfo);

const isOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
});

watch(isOpen, (val) => {
  if (val) {
    deviceStore.fetchSystemInfo();
  }
});

const formatDateTime = (isoString) => {
  if (!isoString) return '—';
  const date = new Date(isoString);
  return date.toLocaleString();
};
</script>

<style scoped>
.bg-disk { background: #121212; }
.border-dark-thin { border: 1px solid #1f1f1f; }
.tracking-1 { letter-spacing: 1px; }
.text-mono { font-family: 'Roboto Mono', monospace; }
</style>
