<template>
  <div class="student-layout">
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <h3>智学编程 - 智能诊断与推荐平台</h3>
        </div>
        <div class="header-right">
          <el-dropdown>
            <span class="user-info">
              <el-icon><User /></el-icon>
              学生用户
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
           <el-drop   down-menu>
                <el-dropdown-item>个人中心</el-dropdown-item>
                <el-dropdown-item>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { User, ArrowDown } from '@element-plus/icons-vue'
</script>

<style scoped>
.student-layout {
  height: 100vh;
}

.header {
  background: #409eff;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}

.header-left h3 {
  margin: 0;
}

.user-info {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
}

.main {
  background: #f5f5f5;
  padding: 20px;
}
</style>