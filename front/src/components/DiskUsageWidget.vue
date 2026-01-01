<template>
  <q-card
    flat
    v-ripple
    class="metric-item bg-disk border-dark-thin relative-position overflow-hidden cursor-pointer"
    @click="$emit('click', path)"
  >
    <div class="row no-wrap full-height items-center relative-position z-top">
      <div class="col-auto flex flex-center bg-grey-10 full-height border-right-dark" style="width: 40px; z-index: 3;">
        <span class="text-subtitle2 text-weight-bold text-amber-3">{{ temp }}°</span>
      </div>
      <div class="col q-px-sm relative-position full-height flex items-center">
        <div class="full-width">
          <div class="row justify-between no-wrap items-baseline">
            <div class="text-blue-4  text-mono" style="font-size: 12px;">{{ path }}</div>
            <div class="text-grey-4 text-mono" style="font-size: 12px;">{{ used }} / {{ total }} GB</div>
          </div>
          <q-linear-progress :value="used / total" color="green-6" size="3px" class="q-mt-xs" />
<!--          <q-linear-progress :value="progress" color="blue-6" size="3px" class="q-mt-xs" />-->
        </div>
      </div>
    </div>
  </q-card>
</template>

<script setup>
defineProps(['path', 'used', 'total', 'temp']);
defineEmits(['click']);
</script>
<style scoped>
.bg-disk { background: #161616; }
.border-dark-thin { border: 1px solid #1f1f1f !important; }
.border-right-dark { border-right: 1px solid #1f1f1f; }
.metric-item { height: 48px; border-radius: 3px; }
</style>
