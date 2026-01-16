<template>
  <q-page class="flex flex-center">
    <div class="q-pa-md bg-black full-width" style="min-height: 100vh;">
      <!-- Loading state -->
      <div v-if="deviceStore.loading" class="flex flex-center" style="min-height: 50vh;">
        <q-spinner color="primary" size="50px" />
      </div>

      <!-- Main content -->
      <div v-else class="row q-col-gutter-md">
        <!-- ZFS Pools (left side) - only pools with multiple disks -->
        <div
          v-for="pool in deviceStore.zpools"
          :key="pool.name"
          class="col-12 col-md-6"
        >
          <ZPoolWidget :pool="pool" />
        </div>

        <!-- System Metrics (right side) -->
        <div class="col-12 col-md-6">
          <SystemMetricsWidget />
        </div>
      </div>

      <!-- Device Detail Dialog -->
      <DeviceDetailDialog />
      
      <!-- Connection Waiting Overlay -->
      <ConnectionOverlay />
    </div>
  </q-page>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue';
import { useDeviceStore } from 'src/stores/deviceStore';
import ZPoolWidget from "components/ZPoolWidget.vue";
import SystemMetricsWidget from "components/SystemMetricsWidget.vue";
import DeviceDetailDialog from "components/DeviceDetailDialog.vue";
import ConnectionOverlay from "components/ConnectionOverlay.vue";

const deviceStore = useDeviceStore();

onMounted(async () => {
  // Initialize store: load inventory, config, and start polling
  await deviceStore.initialize();
});

onUnmounted(() => {
  // Stop polling when leaving page
  deviceStore.stopAllPolling();
});
</script>
