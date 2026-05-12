<template>
  <div class="dashboard">
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <h2>智学编程 - 智能诊断与推荐平台</h2>
        </div>
        <div class="header-right">
          <el-dropdown trigger="click">
            <span class="user-info" v-if="username">欢迎，{{ username }}{{ userFullName ? ' ' + userFullName : '' }}</span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="openUserInfoDialog">个人信息</el-dropdown-item>
                <el-dropdown-item @click="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>

        <!-- 个人信息修改对话框 -->
        <el-dialog
          v-model="userInfoDialogVisible"
          title="个人信息修改"
          width="400px"
        >
          <el-form :model="userInfoForm" :rules="userInfoRules" ref="userInfoFormRef">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="userInfoForm.username" disabled />
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="userInfoForm.email" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input v-model="userInfoForm.password" type="password" placeholder="请输入新密码，留空则不修改" />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input v-model="userInfoForm.confirmPassword" type="password" placeholder="请确认新密码" />
            </el-form-item>
          </el-form>
          <template #footer>
            <span class="dialog-footer">
              <el-button @click="userInfoDialogVisible = false">取消</el-button>
              <el-button type="primary" @click="updateUserInfo" :loading="updatingUserInfo">保存修改</el-button>
            </span>
          </template>
        </el-dialog>
      </el-header>

      <el-main>
        <el-tabs v-model="activeTab" type="border-card">
          <el-tab-pane name="code">
            <template #label>
              <div class="tab-label">
                <el-icon class="tab-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M14.6,16.6L19.2,12L14.6,7.4L16,6L22,12L16,18L14.6,16.6M9.4,16.6L4.8,12L9.4,7.4L8,6L2,12L8,18L9.4,16.6Z"/></svg></el-icon>
                <span>代码提交与分析</span>
              </div>
            </template>
            <CodeSubmitPanel />
          </el-tab-pane>

          <el-tab-pane name="homework">
            <template #label>
              <div class="tab-label">
                <el-icon class="tab-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M19,3H5C3.9,3,3,3.9,3,5V19A2,2,0,0,0,5,21H19A2,2,0,0,0,21,19V5C21,3.9,20.1,3,19,3M19,19H5V5H19V19Z"/></svg></el-icon>
                <span>作业与测验</span>
              </div>
            </template>
            <HomeworkPanel />
          </el-tab-pane>

          <el-tab-pane name="knowledge">
            <template #label>
              <div class="tab-label">
                <el-icon class="tab-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M3,3H21V21H3V3M11,15H13V17H11V15M9,9H11V13H9V9M15,11H17V13H15V11M13,9H15V11H13V9Z"/></svg></el-icon>
                <span>知识掌握图谱</span>
              </div>
            </template>
            <KnowledgeGraphPanel />
          </el-tab-pane>

          <el-tab-pane name="recommend">
            <template #label>
              <div class="tab-label">
                <el-icon class="tab-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12,17.27L18.18,21L16.54,13.97L22,9.24L14.81,8.63L12,2L9.19,8.63L2,9.24L7.45,13.97L5.82,21L12,17.27Z"/></svg></el-icon>
                <span>个性化推荐</span>
              </div>
            </template>
            <PersonalRecommendation />
          </el-tab-pane>
        </el-tabs>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElForm } from 'element-plus'
import api from '../services/api'

import CodeSubmitPanel from '../components/CodeSubmitPanel.vue'
import KnowledgeGraphPanel from '../components/KnowledgeGraphPanel.vue'
import PersonalRecommendation from '../components/PersonalRecommendation.vue'
import HomeworkPanel from '../components/HomeworkPanel.vue'

const router = useRouter()
const activeTab = ref('code')
const username = ref('')
const userFullName = ref('')

// 个人信息修改相关
const userInfoDialogVisible = ref(false)
const userInfoFormRef = ref(null)
const updatingUserInfo = ref(false)
const userInfoForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})
const userInfoRules = {
  email: [
    {
      type: 'email',
      message: '请输入正确的邮箱地址',
      trigger: 'blur'
    }
  ],
  password: [
    {
      min: 6,
      message: '密码长度不能少于6个字符',
      trigger: 'blur',
      required: false
    }
  ],
  confirmPassword: [
    {
      validator: (rule, value, callback) => {
        if (value !== userInfoForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
      required: false
    }
  ]
}

onMounted(() => {
  const isAuthenticated = localStorage.getItem('isAuthenticated')
  const storedUsername = localStorage.getItem('username')
  const storedName = localStorage.getItem('name')

  if (!isAuthenticated || isAuthenticated !== 'true') {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }

  username.value = storedUsername || '学生用户'
  userFullName.value = storedName || ''
  loadUserInfo()
})

const loadUserInfo = async () => {
  try {
    const userId = localStorage.getItem('userId')
    if (userId) {
      const response = await api.getUserInfo(userId)
      if (response.success) {
        userInfoForm.username = response.user.username
        userInfoForm.email = response.user.email
        if (response.user.name) {
          userFullName.value = response.user.name
          localStorage.setItem('name', response.user.name)
        }
      }
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }
}

const openUserInfoDialog = () => {
  loadUserInfo()
  userInfoDialogVisible.value = true
}

const updateUserInfo = async () => {
  if (!userInfoFormRef.value) return
  
  try {
    await userInfoFormRef.value.validate()
    updatingUserInfo.value = true
    
    const userId = localStorage.getItem('userId')
    if (!userId) {
      ElMessage.error('用户未登录')
      return
    }
    
    // 构建更新数据
    const updateData = {
      email: userInfoForm.email
    }
    
    // 如果输入了密码，则更新密码
    if (userInfoForm.password) {
      updateData.password = userInfoForm.password
    }
    
    // 调用后端API更新用户信息
    const response = await api.updateUserInfo(userId, updateData)
    if (response.success) {
      ElMessage.success('个人信息更新成功')
      userInfoDialogVisible.value = false
    } else {
      ElMessage.error(response.error || '更新失败')
    }
  } catch (error) {
    console.error('更新个人信息失败:', error)
    ElMessage.error('更新个人信息失败')
  } finally {
    updatingUserInfo.value = false
  }
}

const logout = () => {
  localStorage.removeItem('isAuthenticated')
  localStorage.removeItem('userRole')
  localStorage.removeItem('username')
  localStorage.removeItem('userId')
  localStorage.removeItem('name')
  localStorage.removeItem('token')
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.dashboard {
  height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #409eff, #667eea);
  color: white;
  padding: 0 30px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  height: 64px;
  transition: all 0.3s ease;
}

.header:hover {
  box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.15);
}

.header-left h2 {
  margin: 0;
  color: white;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 1px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-info {
  color: white;
  font-size: 14px;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.1);
  padding: 6px 12px;
  border-radius: 20px;
  backdrop-filter: blur(10px);
}

.header-right .el-button {
  border-color: white;
  color: white;
  transition: all 0.3s ease;
}

.header-right .el-button:hover {
  background-color: white;
  color: #409eff;
}

.el-main {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 64px);
}

.el-tabs {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.el-tabs__header {
  background-color: #fafafa;
  border-bottom: 1px solid #ebeef5;
  margin: 0;
  padding: 0 20px;
}

.el-tabs__nav {
  height: 52px;
}

.el-tabs__item {
  font-size: 16px;
  font-weight: 500;
  color: #606266;
  margin-right: 30px;
  height: 52px;
  line-height: 52px;
  transition: all 0.3s ease;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tab-icon {
  font-size: 16px;
  transition: all 0.3s ease;
}

.el-tabs__item:hover .tab-icon {
  color: #409eff;
}

.el-tabs__item.is-active .tab-icon {
  color: #409eff;
}

.el-tabs__item:hover {
  color: #409eff;
}

.el-tabs__item.is-active {
  color: #409eff;
  font-weight: 600;
}

.el-tabs__active-bar {
  background-color: #409eff;
  height: 3px;
  border-radius: 3px;
  transition: all 0.3s ease;
}

.el-tabs__content {
  padding: 20px;
}
</style>