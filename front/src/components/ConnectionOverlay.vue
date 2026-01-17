<template>
  <q-transition
    appear
    enter-active-class="animated fadeIn"
    leave-active-class="animated fadeOut"
  >
    <div v-if="!deviceStore.isConnected" class="connection-overlay flex flex-center">
      <div class="text-center">
        <q-spinner-dots
          color="blue-4"
          size="80px"
        />
        <div class="text-h5 text-blue-4 text-weight-bold q-mt-lg tracking-2 uppercase">
          Waiting for connection
        </div>
        <div class="text-grey-6 q-mt-sm">
          Attempting to connect to backend at:
          <div class="text-mono text-grey-4 q-mt-xs">{{ apiBase }}</div>
        </div>
        <div class="text-grey-7 q-mt-md text-caption">
          Reconnecting shortly...
        </div>
      </div>
    </div>
  </q-transition>
</template>

<script setup>
import { useDeviceStore } from 'src/stores/deviceStore';
import { API_BASE } from 'src/services/api';

const deviceStore = useDeviceStore();
const apiBase = API_BASE;
</script>

<style scoped>
.connection-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(8px);
  z-index: 9999;
  color: white;
}

.tracking-2 {
  letter-spacing: 2px;
}

.animated {
  animation-duration: 0.5s;
}
</style>
