<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1>高职Python编程学情系统</h1>
        <p>智能诊断与推荐平台</p>
      </div>
      
      <el-form
        ref="loginForm"
        :model="form"
        :rules="rules"
        class="login-form"
      >
        <el-form-item prop="role">
          <el-radio-group v-model="form.role">
            <el-radio label="student">学生</el-radio>
            <el-radio label="teacher">教师</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            prefix-icon="el-icon-user"
            size="large"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="el-icon-lock"
            size="large"
            show-password
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleLogin"
            style="width: 100%;"
          >
            登录
          </el-button>
        </el-form-item>
        
        <div class="demo-login">
          <p>演示账号：</p>
          <p>学生：请使用您的学号作为用户名，密码为123456</p>
          <p>教师：username: teacher, password: teacher123</p>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

export default {
  name: 'LoginView',
  setup() {
    const router = useRouter()
    const loginForm = ref()
    const loading = ref(false)

    const form = reactive({
      role: 'student',
      username: '',
      password: ''
    })

    const rules = {
      role: [
        { required: true, message: '请选择角色', trigger: 'change' }
      ],
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' }
      ]
    }

    const handleLogin = () => {
      loginForm.value.validate(valid => {
        if (valid) {
          loading.value = true
          
          // 教师和学生登录验证 - 通过统一API
          fetch('http://localhost:5002/api/login', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              username: form.username,
              password: form.password
            })
          })
          .then(response => response.json())
          .then(data => {
            if (data.success) {
              // 保存登录状态
              localStorage.setItem('isAuthenticated', 'true')
              localStorage.setItem('userRole', form.role)
              localStorage.setItem('username', form.username)
              localStorage.setItem('userId', data.user.id)
              localStorage.setItem('token', data.token)
              
              ElMessage.success('登录成功')
              if (form.role === 'teacher') {
                router.push('/teacher')
              } else {
                router.push('/student')
              }
            } else {
              ElMessage.error(data.error || '用户名或密码错误')
            }
            loading.value = false
          })
          .catch(error => {
            console.error('登录失败:', error)
            ElMessage.error('登录失败，请稍后重试')
            loading.value = false
          })
        }
      })
    }

    return {
      loginForm,
      loading,
      form,
      rules,
      handleLogin
    }
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-box {
  width: 400px;
  padding: 40px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h1 {
  font-size: 24px;
  color: #333;
  margin-bottom: 10px;
}

.login-header p {
  color: #666;
  font-size: 14px;
}

.login-form {
  margin-top: 20px;
}

.demo-login {
  margin-top: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
  line-height: 1.6;
}
</style>