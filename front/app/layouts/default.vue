<template>
  <div class="wrapper_page">
    <aside class="sidebar_block" :style="{ width: sidebarWidth + '%' }">
      <LayoutsSidebar />
      <div class="resize_handle" @pointerdown="startResize"></div>
    </aside>
    <!-- Start Body -->
    <div class="body_block">
      <!-- Start Header -->
      <div class="header_block">
        <LayoutsHeader />
      </div>
      <!-- / Header -->
      <slot />
    </div>
    <!-- / Body -->
    <UiToastContainer />
  </div>
</template>

<script setup>

import UiToastContainer from '~/components/ui/ToastContainer.vue'
const MIN_WIDTH_PCT = 14
const MAX_WIDTH_PCT = 40

const sidebarWidth = useState('sidebarWidth', () => 20) // percent

let startX = 0
let startWidth = 0

function startResize(e) {
  startX = e.clientX
  startWidth = sidebarWidth.value
  e.target.setPointerCapture(e.pointerId)
  document.addEventListener('pointermove', onResize)
  document.addEventListener('pointerup', stopResize)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function onResize(e) {
  const deltaPx = e.clientX - startX
  const deltaPct = (deltaPx / window.innerWidth) * 100
  sidebarWidth.value = Math.min(MAX_WIDTH_PCT, Math.max(MIN_WIDTH_PCT, startWidth + deltaPct))
}

function stopResize() {
  document.removeEventListener('pointermove', onResize)
  document.removeEventListener('pointerup', stopResize)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
  localStorage.setItem('sidebarWidth', sidebarWidth.value)
}

onMounted(() => {
  const saved = localStorage.getItem('sidebarWidth')
  if (saved) sidebarWidth.value = parseFloat(saved)
})

</script>

<style scoped>
.wrapper_page {
  display: flex;
}

.sidebar_block {
  height: 100vh;
  flex-shrink: 0;
  border-right: var(--border);
  position: relative;
  overflow: hidden;
}

.resize_handle {
  position: absolute;
  top: 0;
  right: 0;
  width: 4px;
  height: 100%;
  cursor: col-resize;
  z-index: 9999;
}

.resize_handle:hover,
.resize_handle:active {
  background: var(--border);
}

.body_block {
  height: 100vh;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
</style>

