<template>
  <div class="login-container" :style="{ backgroundImage: `url(${techBg})` }">
    <div class="login-box">
      <h2 class="login-title">{{ isRegister ? '学生注册' : '编程学情智能平台' }}</h2>
      <div v-if="!isRegister" class="login-subtitle">智能诊断 · 个性推荐 · 知识图谱 · 精准分析</div>
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        label-width="0"
        size="large"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            prefix-icon="User"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-form-item v-if="isRegister" prop="confirmPassword">
          <el-input
            v-model="loginForm.confirmPassword"
            type="password"
            placeholder="请确认密码"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-form-item v-if="isRegister" prop="studentId">
          <el-input
            v-model="loginForm.studentId"
            placeholder="请输入学号"
            prefix-icon="Document"
          />
        </el-form-item>
        <el-form-item v-if="isRegister" prop="name">
          <el-input
            v-model="loginForm.name"
            placeholder="请输入姓名"
            prefix-icon="UserFilled"
          />
        </el-form-item>
        <el-form-item v-if="isRegister" prop="className">
          <el-input
            v-model="loginForm.className"
            placeholder="请输入班级"
            prefix-icon="CollectionTag"
          />
        </el-form-item>
        <el-form-item v-if="isRegister" prop="email">
          <el-input
            v-model="loginForm.email"
            placeholder="请输入邮箱"
            prefix-icon="Message"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            @click="isRegister ? handleRegister() : handleLogin()"
            style="width: 100%"
          >
            {{ isRegister ? '注册' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>
      <div class="switch-mode">
        <el-link type="primary" @click="isRegister = !isRegister">
          {{ isRegister ? '已有账号？立即登录' : '没有账号？立即注册' }}
        </el-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Document, UserFilled, CollectionTag, Message } from '@element-plus/icons-vue'
import api from '../services/api'
import techBg from '../assets/images/tech-bg.jpg'

const router = useRouter()
const loginFormRef = ref()
const loading = ref(false)
const isRegister = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  studentId: '',
  name: '',
  className: '',
  email: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (isRegister.value && value !== loginForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ],
  studentId: [
    { required: true, message: '请输入学号', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  className: [
    { required: true, message: '请输入班级', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ]
}

const handleRegister = async () => {
  if (!loginFormRef.value) return

  try {
    await loginFormRef.value.validate()
    loading.value = true

    const response = await api.register({
      username: loginForm.username,
      password: loginForm.password,
      studentId: loginForm.studentId,
      name: loginForm.name,
      className: loginForm.className,
      email: loginForm.email
    })

    if (response.success) {
      ElMessage.success('注册成功！请登录')
      isRegister.value = false
      loginForm.password = ''
      loginForm.confirmPassword = ''
      loginForm.studentId = ''
      loginForm.name = ''
      loginForm.className = ''
      loginForm.email = ''
    } else {
      ElMessage.error(response.error || '注册失败')
    }
  } catch (error) {
    console.error('注册错误:', error)
    if (error.response) {
      ElMessage.error(`服务器错误: ${error.response.status} - ${error.response.data?.error || error.message}`)
    } else if (error.request) {
      ElMessage.error('网络错误: 无法连接到服务器，请检查后端是否启动')
    } else {
      ElMessage.error(`请求错误: ${error.message}`)
    }
  } finally {
    loading.value = false
  }
}

const handleLogin = async () => {
  if (!loginFormRef.value) return

  try {
    await loginFormRef.value.validate()
    loading.value = true

    const response = await api.login(loginForm.username, loginForm.password)

    if (response.success) {
      localStorage.setItem('isAuthenticated', 'true')
      localStorage.setItem('userRole', response.user?.role || 'student')
      localStorage.setItem('username', response.user?.username || loginForm.username)
      localStorage.setItem('userId', response.user?.id || '')
      localStorage.setItem('name', response.user?.name || '')

      if (response.token) {
        localStorage.setItem('token', response.token)
      }

      ElMessage.success('登录成功！')
      // 根据角色跳转到不同页面
      if (response.user?.role === 'teacher') {
        router.push('/teacher/dashboard')
      } else {
        router.push('/dashboard')
      }
    } else {
      ElMessage.error(response.error || response.message || '登录失败')
    }
  } catch (error) {
    console.error('登录错误:', error)
    if (error.response) {
      ElMessage.error(`服务器错误: ${error.response.status} - ${error.response.data?.error || error.message}`)
    } else if (error.request) {
      ElMessage.error('网络错误: 无法连接到服务器，请检查后端是否启动')
    } else {
      ElMessage.error(`请求错误: ${error.message}`)
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

.login-box {
  background: rgba(255, 255, 255, 0.85); /* 半透明白色，模拟磨砂玻璃 */
  backdrop-filter: blur(10px); /* 关键：毛玻璃模糊效果（需浏览器支持） */
  -webkit-backdrop-filter: blur(10px); /* 兼容 Safari */
  border-radius: 16px; /* 圆角更柔和 */
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2); /* 增强立体感 */
  padding: 32px;
  width: 480px;
  max-width: 98%;
  transition: all 0.3s ease; /* 整体过渡动画 */
}

.login-box:hover {
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.25); /* 悬浮时阴影加深 */
  transform: translateY(-2px); /* 轻微上浮，增强交互感 */
}

.login-title {
  font-size: 24px;
  font-weight: 700;
  background: linear-gradient(90deg, #409EFF, #764BA2); /* 品牌渐变 */
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent; /* 文字渐变 */
  margin-bottom: 8px;
  text-align: center;
}

.login-subtitle {
  font-size: 16px;
  font-weight: 500;
  background: linear-gradient(90deg, #409EFF, #764BA2); /* 品牌渐变 */
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent; /* 文字渐变 */
  text-align: center;
  margin-bottom: 24px;
  letter-spacing: 1px; /* 字间距更舒展 */
}

.el-form-item {
  margin-bottom: 20px;
  position: relative;
}

/* 输入框容器 */
.el-input {
  position: relative;
}

/* 输入框样式 */
.el-input__wrapper {
  border-radius: 8px !important;
  background-color: #f9fafb !important;
  transition: all 0.3s ease !important;
}

/* 输入框聚焦时 */
.el-input__wrapper.is-focus {
  border-color: #409EFF !important;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.1) !important;
  background-color: #fff !important;
}

/* 输入框图标 */
.el-input__prefix {
  left: 12px !important;
  color: #999 !important;
  transition: color 0.3s ease !important;
}

/* 输入框聚焦时图标颜色 */
.el-input__wrapper.is-focus .el-input__prefix {
  color: #409EFF !important;
}

/* 密码显示/隐藏按钮 */
.el-input__suffix-inner .el-input__icon {
  color: #999 !important;
  transition: color 0.3s ease !important;
  cursor: pointer !important;
}

/* 密码按钮hover时 */
.el-input__suffix-inner .el-input__icon:hover {
  color: #409EFF !important;
}

/* 输入框内容 */
.el-input__inner {
  padding-left: 44px !important;
  font-size: 14px !important;
  border: none !important;
  background: transparent !important;
}

.switch-mode {
  text-align: center;
  margin-top: 15px;
}
</style>