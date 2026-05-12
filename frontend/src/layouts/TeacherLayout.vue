<template>
  <div class="teacher-layout">
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <h3 style="text-align: center; line-height: 1.2; margin: 0; font-size: 20px; font-weight: 600; background: linear-gradient(135deg, #409eff, #667eea); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            编程学情智能<br>
            管理系统
          </h3>
        </div>
        <div class="header-right">
          <el-dropdown>
            <span class="user-info">
              <el-icon><User /></el-icon>
              教师用户
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>个人中心</el-dropdown-item>
                <el-dropdown-item>退出登录</el-link>
                <el-dropdown-item>系统设置</el-dropdown-item>
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
.teacher-layout {
  height: 100vh;
}

.header {
  background: #67c23a;
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