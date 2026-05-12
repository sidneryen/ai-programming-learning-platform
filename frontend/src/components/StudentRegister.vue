<template>
  <div class="student-register">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>学生注册</span>
        </div>
      </template>
      
      <el-form :model="form" label-width="80px">
        <el-form-item label="学号">
          <el-input v-model="form.studentId" placeholder="请输入学号" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.realName" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="班级">
          <el-input v-model="form.className" placeholder="请输入班级（可选）" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="submit">注册</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>Excel批量导入</span>
        </div>
      </template>
      
      <el-upload
        class="upload-demo"
        drag
        :auto-upload="false"
        :on-change="handleFileChange"
        accept=".xlsx,.xls"
      >
        <i class="el-icon-upload"></i>
        <div class="el-upload__text">将Excel文件拖到此处，或<em>点击上传</em></div>
        <div class="el-upload__tip" slot="tip">仅支持 .xlsx/.xls 格式</div>
      </el-upload>
      
      <el-button 
        type="primary" 
        style="margin-top: 20px;" 
        :disabled="!selectedFile"
        @click="submitImport"
      >
        开始导入
      </el-button>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const form = ref({
  studentId: '',
  realName: '',
  className: ''
})

const selectedFile = ref(null)

// 单个注册
const submit = async () => {
  try {
    const res = await axios.post('/api/students/register', form.value)
    if (res.data.code === 200) {
      ElMessage.success(res.data.msg)
      form.value = { studentId: '', realName: '', className: '' }
    } else {
      ElMessage.error(res.data.msg)
    }
  } catch (e) {
    ElMessage.error('请求失败')
  }
}

// 文件选择
const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

// 批量导入
const submitImport = async () => {
  if (!selectedFile.value) return
  
  const formData = new FormData()
  formData.append('file', selectedFile.value)
  
  try {
    const res = await axios.post('/api/students/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    if (res.data.code === 200) {
      ElMessage.success(res.data.msg)
      selectedFile.value = null
    } else {
      ElMessage.error(res.data.msg)
    }
  } catch (e) {
    ElMessage.error('导入失败')
  }
}
</script>

<style scoped>
.student-register {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}
</style>