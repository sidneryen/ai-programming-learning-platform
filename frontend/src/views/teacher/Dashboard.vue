<template>
  <div class="teacher-dashboard">
    <el-container style="height: 100vh">
      <!-- 左侧导航菜单 -->
      <el-aside width="200px" class="aside">
        <div class="logo">
          <h2 style="text-align: center; line-height: 1.2; margin: 0; font-size: 22px; font-weight: 600; background: linear-gradient(135deg, #409eff, #667eea); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            智学编程<br>
            智能诊断平台
          </h2>
        </div>
        <el-menu
          :default-active="activeMenu"
          class="menu"
          @select="handleMenuSelect"
        >
          <el-menu-item index="students">
            <el-icon><User /></el-icon>
            <span>学生学情管理</span>
          </el-menu-item>
          <el-menu-item index="problems">
            <el-icon><Document /></el-icon>
            <span>编程题目管理</span>
          </el-menu-item>
          <el-menu-item index="homeworks">
            <el-icon><Notebook /></el-icon>
            <span>作业与测验管理</span>
          </el-menu-item>
          <el-menu-item index="ai-recommend">
            <el-icon><Star /></el-icon>
            <span>AI推荐管理</span>
          </el-menu-item>
          <el-menu-item index="backup">
            <el-icon><Download /></el-icon>
            <span>备份数据库</span>
          </el-menu-item>
          <el-menu-item index="settings">
            <el-icon><Setting /></el-icon>
            <span>个人设置</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 右侧内容区域 -->
      <el-main class="main">
        <!-- 统计卡片 -->
        <el-row :gutter="20" style="margin-bottom: 20px">
          <el-col :span="8">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-number">{{ studentCount }}</div>
                <div class="stat-label">学生总数</div>
              </div>
              <el-icon class="stat-icon"><User /></el-icon>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-number">{{ total }}</div>
                <div class="stat-label">题目总数</div>
              </div>
              <el-icon class="stat-icon"><Document /></el-icon>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-number">{{ todaySubmissions }}</div>
                <div class="stat-label">今日提交</div>
              </div>
              <el-icon class="stat-icon"><Star /></el-icon>
            </el-card>
          </el-col>
        </el-row>

        <!-- 学生学情管理 -->
        <div v-if="activeMenu === 'students'">
          <el-card class="table-card">
            <template #header>
              <div class="card-header">
                <span>学生学情管理</span>
                <div class="header-actions">
                  <el-input
                    v-model="searchUsername"
                    placeholder="按登录名搜索学生"
                    style="width: 200px; margin-right: 12px"
                    clearable
                    @input="handleSearch"
                  />
                  <el-select
                    v-model="searchClass"
                    placeholder="按班级搜索"
                    style="width: 150px; margin-right: 12px"
                    clearable
                    @change="handleSearch"
                  >
                    <el-option label="全部班级" value="" />
                    <el-option v-for="cls in classList" :key="cls" :label="cls" :value="cls" />
                  </el-select>
                  <el-button type="success" @click="showClassKnowledgeGraph" :disabled="!searchClass">班级知识图谱</el-button>
                  <el-button type="primary" @click="showImportDialog = true">导入花名册</el-button>
                </div>
              </div>
            </template>
            <el-table :data="filteredStudents" style="width: 100%">
              <el-table-column prop="student_id" label="学号" width="120" />
              <el-table-column prop="name" label="姓名" width="120" />
              <el-table-column prop="class_name" label="班级" width="150" />
              <el-table-column prop="email" label="邮箱" width="200" />
              <el-table-column prop="username" label="登录用户名" width="150" />
              <el-table-column label="操作" width="400">
                <template #default="scope">
                  <div style="display: flex; flex-wrap: nowrap; gap: 6px;">
                    <el-button type="primary" size="small" @click="openChangePasswordDialog(scope.row)">
                      修改密码
                    </el-button>
                    <el-button type="success" size="small" @click="showStudentKnowledgeGraph(scope.row)">
                      知识图谱
                    </el-button>
                    <el-button type="warning" size="small" @click="exportStudentCode(scope.row)">
                      导出代码
                    </el-button>
                    <el-button type="danger" size="small" @click="deleteStudent(scope.row)">
                      删除
                    </el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>

        <!-- 编程题目管理 -->
        <div v-if="activeMenu === 'problems'">
          <el-card class="table-card">
            <template #header>
              <div class="card-header">
                <span>编程题目管理</span>
                <div style="display: flex; align-items: center; gap: 10px;">
                  <el-input 
                    v-model="searchProblemNumber" 
                    placeholder="题目号" 
                    style="width: 120px;"
                  />
                  <el-select 
                    v-model="searchCategory" 
                    placeholder="知识分类" 
                    style="width: 150px;"
                    @change="handleProblemSearch"
                  >
                    <el-option label="全部" value="" />
                    <el-option 
                      v-for="category in categories" 
                      :key="category" 
                      :label="category" 
                      :value="category" 
                    />
                  </el-select>
                  <el-select 
                    v-model="searchDifficulty" 
                    placeholder="难度等级" 
                    style="width: 120px;"
                    @change="handleProblemSearch"
                  >
                    <el-option label="全部" value="" />
                    <el-option 
                      v-for="level in difficultyLevels" 
                      :key="level" 
                      :label="level" 
                      :value="level" 
                    />
                  </el-select>
                  <el-button type="primary" @click="openAddProblemDialog()">添加题目</el-button>
                  <el-button type="success" @click="showGenerateDialog = true">AI生成题目</el-button>
                  <el-button type="warning" @click="exportProblems">导出题目</el-button>
                  <el-button type="info" @click="showImportProblemDialog = true">导入题目</el-button>
                </div>
              </div>
            </template>
            <el-table :data="problems" style="width: 100%">
              <el-table-column prop="problem_number" label="题目号" width="80" />
              <el-table-column label="标题" min-width="200">
                <template #default="scope">
                  <div class="title-with-ai-tag" style="display: flex; align-items: center;">
                    <span>{{ scope.row.title }}</span>
                    <el-tag v-if="scope.row.problem_number >= 10000" type="info" size="small" style="margin-left: 8px;">
                      AI生成
                    </el-tag>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="difficulty" label="难度等级" width="120">
                <template #default="scope">
                  <el-tag :type="getDifficultyType(scope.row.difficulty)" size="small">
                    {{ scope.row.difficulty || '入门' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="category" label="分类" width="200" />
              <el-table-column label="操作" width="520">
                <template #default="scope">
                  <div style="display: flex; align-items: center; gap: 6px; flex-wrap: nowrap;">
                    <el-select
                      v-model="scope.row.selectedHomeworks"
                      multiple
                      placeholder="添加到作业"
                      style="width: 180px;"
                      :popper-append-to-body="false"
                      @change="(val) => addProblemToHomeworks(scope.row, val)"
                    >
                      <el-option
                        v-for="hw in homeworks"
                        :key="hw.id"
                        :label="`${hw.title} (${hw.type === 'homework' ? '作业' : '测验'}) - ${hw.class_name || '未指定班级'} - 题目: ${hw.problem_numbers || '无'}`"
                        :value="hw.id"
                      />
                    </el-select>
                    <el-button type="primary" size="small" @click="editProblem(scope.row)">
                      编辑
                    </el-button>
                    <el-button type="success" size="small" @click="showSubmissionRecords(scope.row)">
                      提交记录
                    </el-button>
                    <el-button type="warning" size="small" @click="testProblem(scope.row)">
                      测试提交
                    </el-button>
                    <el-button type="danger" size="small" @click="deleteProblem(scope.row)">
                      删除
                    </el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>

            <!-- 分页组件 -->
            <div class="pagination-container" style="margin-top: 15px; text-align: center;">
              <el-pagination
                v-model:current-page="currentPage"
                v-model:page-size="pageSize"
                :page-sizes="[20]"
                layout="prev, pager, next"
                :total="total"
                @size-change="handleSizeChange"
                @current-change="handleCurrentChange"
              />
            </div>
          </el-card>
        </div>

        <!-- AI推荐管理 -->
        <div v-if="activeMenu === 'ai-recommend'">
          <el-card class="table-card">
            <template #header>
              <div class="card-header">
                <span>AI推荐管理</span>
                <div class="header-actions">
                  <el-input
                    v-model="searchStudentNumber"
                    placeholder="按学号搜索"
                    style="width: 150px; margin-right: 12px"
                    clearable
                    @input="handleAIHomeworkSearch"
                  />
                  <el-input
                    v-model="searchStudentName"
                    placeholder="按姓名搜索"
                    style="width: 150px; margin-right: 12px"
                    clearable
                    @input="handleAIHomeworkSearch"
                  />
                  <el-select
                    v-model="searchRecommendClass"
                    placeholder="按班级搜索"
                    style="width: 150px; margin-right: 12px"
                    clearable
                    @change="handleAIHomeworkSearch"
                  >
                    <el-option label="全部班级" value="" />
                    <el-option v-for="cls in classList" :key="cls" :label="cls" :value="cls" />
                  </el-select>
                  <el-button type="primary" size="small" @click="loadAIHomeworkList">
                    刷新
                  </el-button>
                </div>
              </div>
            </template>
            
            <!-- AI推荐作业列表管理 -->
            <div>
              <el-table :data="aiHomeworkList" style="width: 100%" v-loading="aiHomeworkLoading">
                <el-table-column prop="id" label="ID" width="120">
                  <template #default="scope">
                    <div class="id-with-status" style="display: flex; align-items: center;">
                      <span>{{ scope.row.id }}</span>
                      <el-tag v-if="scope.row.is_completed" type="success" size="small" style="margin-left: 8px;">
                        ✅ 已完成
                      </el-tag>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="student_name" label="学生姓名" width="120" />
                <el-table-column prop="student_number" label="学号" width="120" />
                <el-table-column prop="class_name" label="班级" width="150" />
                <el-table-column prop="title" label="推荐标题" min-width="200" />
                <el-table-column label="题目号" min-width="150">
                  <template #default="scope">
                    <div class="problem-numbers-container">
                      <a 
                        v-for="num in (scope.row.problem_number || '').split(',').filter(n => n.trim())" 
                        :key="num"
                        class="problem-number-link"
                        @click="viewProblemDetail(parseInt(num.trim()))"
                      >
                        {{ num.trim() }}
                      </a>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="problem_count" label="题目数量" width="100" />
                <el-table-column prop="generated_at" label="生成时间" width="180" />
                <el-table-column label="操作" width="280" fixed="right">
                  <template #default="scope">
                    <div style="display: flex; gap: 6px; align-items: center; justify-content: flex-start;">
                      <el-button type="primary" size="small" @click="viewAIHomework(scope.row)">
                        查看
                      </el-button>
                      <el-button type="success" size="small" @click="editAIHomeworkProblemNumber(scope.row)">
                        修改题目号
                      </el-button>
                      <el-button type="danger" size="small" @click="deleteAIHomework(scope.row)">
                        删除
                      </el-button>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
              
              <div v-if="aiHomeworkList.length === 0 && !aiHomeworkLoading" class="empty-state">
                <el-empty description="暂无AI推荐作业" />
              </div>
              
              <!-- 分页组件 -->
              <div v-if="aiHomeworkTotal > 0" class="pagination-container" style="margin-top: 15px; text-align: center;">
                <el-pagination
                  v-model:current-page="aiHomeworkCurrentPage"
                  v-model:page-size="aiHomeworkPageSize"
                  :page-sizes="[15]"
                  layout="prev, pager, next"
                  :total="aiHomeworkTotal"
                  @size-change="handleAIHomeworkSizeChange"
                  @current-change="handleAIHomeworkCurrentChange"
                />
              </div>
            </div>
          </el-card>
        </div>

        <!-- 备份数据库 -->
        <div v-if="activeMenu === 'backup'">
          <el-card class="table-card">
            <template #header>
              <div class="card-header">
                <span>备份数据库</span>
              </div>
            </template>
            <div class="backup-content">
              <el-alert
                title="数据库备份"
                type="info"
                :closable="false"
                show-icon
              >
                <template #default>
                  <p>点击下方按钮可备份当前数据库</p>
                  <p>备份文件将以当前时间戳命名</p>
                </template>
              </el-alert>

              <div class="backup-actions">
                <el-button
                  type="primary"
                  size="large"
                  :loading="backingUp"
                  @click="backupDatabase"
                >
                  <el-icon><Download /></el-icon>
                  立即备份数据库
                </el-button>
              </div>

              <div v-if="backupHistory.length > 0" class="backup-history">
                <h3>备份历史</h3>
                <el-table :data="backupHistory" style="width: 100%">
                  <el-table-column prop="filename" label="备份文件名" />
                  <el-table-column prop="size" label="文件大小" width="120" />
                  <el-table-column prop="timestamp" label="备份时间" width="200" />
                  <el-table-column label="操作" width="150">
                    <template #default="scope">
                      <el-button type="success" size="small" @click="downloadBackup(scope.row)">
                        下载
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </el-card>
        </div>

        <!-- 个人设置 -->
        <div v-if="activeMenu === 'settings'">
          <el-card class="table-card">
            <template #header>
              <div class="card-header">
                <span>个人设置</span>
              </div>
            </template>
            <div class="settings-content">
              <el-alert
                title="修改密码"
                type="info"
                :closable="false"
                show-icon
              >
                <template #default>
                  <p>请输入原密码和新密码来修改您的账号密码</p>
                </template>
              </el-alert>

              <el-form :model="teacherChangePasswordForm" :rules="teacherChangePasswordRules" ref="teacherChangePasswordFormRef" label-width="120px" class="change-password-form">
                <el-form-item label="原密码" prop="oldPassword">
                  <el-input v-model="teacherChangePasswordForm.oldPassword" type="password" placeholder="请输入原密码" show-password />
                </el-form-item>
                <el-form-item label="新密码" prop="newPassword">
                  <el-input v-model="teacherChangePasswordForm.newPassword" type="password" placeholder="请输入新密码" show-password />
                </el-form-item>
                <el-form-item label="确认密码" prop="confirmPassword">
                  <el-input v-model="teacherChangePasswordForm.confirmPassword" type="password" placeholder="请确认新密码" show-password />
                </el-form-item>
                <el-form-item>
                  <el-button
                    type="primary"
                    :loading="teacherChangingPassword"
                    @click="handleTeacherChangePassword"
                  >
                    确认修改密码
                  </el-button>
                </el-form-item>
              </el-form>
            </div>
          </el-card>
        </div>

        <!-- 作业与测验管理 -->
        <div v-if="activeMenu === 'homeworks'">
          <el-card class="table-card">
            <template #header>
              <div class="card-header">
                <span>作业与测验管理</span>
                <el-button type="primary" @click="showAddHomeworkDialog = true">添加作业与测验</el-button>
              </div>
            </template>
            <el-table :data="homeworks" style="width: 100%">
              <el-table-column prop="id" label="编号" width="80" />
              <el-table-column prop="title" label="标题" />
              <el-table-column prop="type" label="类型" width="100">
                <template #default="scope">
                  <el-tag :type="scope.row.type === 'homework' ? 'primary' : 'danger'">
                    {{ scope.row.type === 'homework' ? '作业' : '测验' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="problem_numbers" label="题目编号" />
              <el-table-column prop="class_name" label="班级" width="200">
                <template #default="scope">
                  <span v-if="scope.row.class_name">{{ scope.row.class_name }}</span>
                  <span v-else style="color: #909399">全部班级</span>
                </template>
              </el-table-column>
              <el-table-column prop="start_time" label="开始时间" width="180" />
              <el-table-column prop="end_time" label="结束时间" width="180" />
              <el-table-column label="操作" width="320">
                <template #default="scope">
                  <div style="display: flex; gap: 8px;">
                    <el-button type="success" size="small" @click="viewHomeworkScores(scope.row)">
                      查看成绩
                    </el-button>
                    <el-button type="primary" size="small" @click="editHomework(scope.row)">
                      编辑
                    </el-button>
                    <el-button type="warning" size="small" @click="copyHomework(scope.row)">
                      复制
                    </el-button>
                    <el-button type="danger" size="small" @click="deleteHomework(scope.row)">
                      删除
                    </el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>
      </el-main>
    </el-container>

    <el-dialog v-model="showImportDialog" title="导入学生学情" width="500px">
      <el-upload
        class="upload-demo"
        drag
        :auto-upload="false"
        :on-change="handleFileChange"
        accept=".xlsx,.xls"
      >
        <i class="el-icon-upload"></i>
        <div class="el-upload__text">将Excel文件拖到此处，或<em>点击上传</em></div>
        <div class="el-upload__tip" slot="tip">
          <p>Excel文件需包含以下列：学号、姓名、班级（可缺省）、邮箱（可缺省）</p>
          <p>导入后，学生登录用户名为学号，初始密码为123456</p>
        </div>
      </el-upload>
      <template #footer>
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="handleImport">开始导入</el-button>
      </template>
    </el-dialog>

    <!-- 导入题目对话框 -->
    <el-dialog v-model="showImportProblemDialog" title="导入编程题目" width="500px">
      <el-upload
        class="upload-demo"
        drag
        :auto-upload="false"
        :on-change="handleProblemFileChange"
        accept=".xlsx,.xls"
      >
        <i class="el-icon-upload"></i>
        <div class="el-upload__text">将Excel文件拖到此处，或<em>点击上传</em></div>
        <div class="el-upload__tip" slot="tip">
          <p>Excel文件需包含以下列：标题、题目描述、输入描述、输出描述、样例输入、样例输出、分类</p>
          <p>分类格式：语言-知识点，例如：Python-列表list</p>
        </div>
      </el-upload>
      <template #footer>
        <el-button @click="showImportProblemDialog = false">取消</el-button>
        <el-button type="primary" :loading="importingProblems" @click="handleProblemImport">开始导入</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="isProblemDialogVisible" :title="editingProblem ? '编辑编程题目' : '添加编程题目'" width="900px" top="5vh">
      <div style="max-height: 70vh; overflow-y: auto; padding-right: 10px; padding-bottom: 20px;">
        <el-form :model="problemForm" label-width="100px">
          <el-form-item label="标题">
            <el-input v-model="problemForm.title" placeholder="请输入题目标题" />
          </el-form-item>
          <el-form-item label="题目描述">
            <div class="rich-editor-container" style="width: 100%;">
              <div class="rich-editor-toolbar">
                <el-button type="primary" size="small" @click="insertImage">
                  <el-icon><Picture /></el-icon> 插入图片
                </el-button>
                <input
                  type="file"
                  ref="fileInput"
                  accept="image/*"
                  style="display: none"
                  @change="handleFileSelect"
                />
              </div>
              <div
                ref="editorContainer"
                class="rich-editor-content"
                contenteditable="true"
                @input="handleEditorInput"
                placeholder="请输入题目描述，可以插入图片"
              ></div>
            </div>
          </el-form-item>
          <el-form-item label="输入描述">
            <el-input
              v-model="problemForm.input_description"
              type="textarea"
              :rows="2"
              placeholder="请输入输入描述"
            />
          </el-form-item>
          <el-form-item label="输出描述">
            <el-input
              v-model="problemForm.output_description"
              type="textarea"
              :rows="2"
              placeholder="请输入输出描述"
            />
          </el-form-item>
          <el-form-item label="样例输入">
            <el-input
              v-model="problemForm.sample_input"
              type="textarea"
              :rows="2"
              placeholder="请输入样例输入"
            />
          </el-form-item>
          <el-form-item label="样例输出">
            <el-input
              v-model="problemForm.sample_output"
              type="textarea"
              :rows="2"
              placeholder="请输入样例输出"
            />
          </el-form-item>
          <el-form-item label="测试输入">
            <el-input
              v-model="problemForm.test_input"
              type="textarea"
              :rows="2"
              placeholder="请输入测试输入（不显示给学生，用于验证代码正确性的额外测试用例）"
            />
          </el-form-item>
          <el-form-item label="测试输出">
            <el-input
              v-model="problemForm.test_output"
              type="textarea"
              :rows="2"
              placeholder="请输入测试输出（不显示给学生，测试输入对应的预期输出）"
            />
          </el-form-item>
          <el-form-item label="难度等级">
            <el-select
              v-model="problemForm.difficulty"
              placeholder="请选择难度等级"
              style="width: 100%"
            >
              <el-option label="入门" value="入门" />
              <el-option label="基础" value="基础" />
              <el-option label="提高" value="提高" />
            </el-select>
          </el-form-item>
          <el-form-item label="必需函数">
            <el-input
              v-model="problemForm.required_functions"
              type="textarea"
              :rows="2"
              placeholder="请输入必需的函数名，多个函数用逗号分隔，如：add, subtract。学生提交的代码必须包含并调用这些函数才能得分"
            />
          </el-form-item>
          <el-form-item label="分类" style="margin-top: 40px; margin-bottom: 20px;">
            <el-select
              v-model="problemForm.category"
              placeholder="请选择或输入题目分类"
              filterable
              allow-create
              default-first-option
              style="width: 100%"
            >
              <el-option
                v-for="category in categories"
                :key="category"
                :label="category"
                :value="category"
              />
            </el-select>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="isProblemDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="addingProblem" @click="editingProblem ? handleEditProblem() : handleAddProblem()">
          {{ editingProblem ? '更新题目' : '添加题目' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 测试提交对话框 -->
    <el-dialog v-model="showTestDialog" :title="`测试提交 - ${currentTestProblem?.title || ''}`" width="95%" top="3vh">
      <div style="max-height: 80vh; overflow-y: auto; padding: 10px;">
        <!-- 题目信息 -->
        <div v-if="currentTestProblem" style="margin-bottom: 20px; padding: 20px; background: #f8f9fa; border-radius: 12px;">
          <h4 style="margin-bottom: 15px; color: #303133; font-size: 16px; border-bottom: 1px solid #e4e7ed; padding-bottom: 10px;">题目描述</h4>
          <div v-html="currentTestProblem.description" style="margin-bottom: 15px; line-height: 1.6;"></div>
          
          <!-- 输入输出描述 -->
          <div style="margin-bottom: 15px;">
            <div style="margin-bottom: 10px;">
              <span style="font-weight: bold; color: #606266;">输入描述：</span>
              <span style="color: #303133;">{{ currentTestProblem.input_description }}</span>
            </div>
            <div>
              <span style="font-weight: bold; color: #606266;">输出描述：</span>
              <span style="color: #303133;">{{ currentTestProblem.output_description }}</span>
            </div>
          </div>

          <!-- 样例输入输出 -->
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
            <div style="background: #fff; border: 1px solid #e4e7ed; border-radius: 8px; padding: 12px;">
              <div style="font-weight: bold; color: #606266; margin-bottom: 8px; font-size: 14px;">样例输入</div>
              <pre style="background: #fafafa; padding: 10px; border-radius: 6px; font-family: 'Monaco', 'Menlo', monospace; font-size: 13px; margin: 0; white-space: pre-wrap; word-break: break-all; max-height: 150px; overflow-y: auto;">{{ currentTestProblem.sample_input || '-' }}</pre>
            </div>
            <div style="background: #fff; border: 1px solid #e4e7ed; border-radius: 8px; padding: 12px;">
              <div style="font-weight: bold; color: #606266; margin-bottom: 8px; font-size: 14px;">样例输出</div>
              <pre style="background: #fafafa; padding: 10px; border-radius: 6px; font-family: 'Monaco', 'Menlo', monospace; font-size: 13px; margin: 0; white-space: pre-wrap; word-break: break-all; max-height: 150px; overflow-y: auto;">{{ currentTestProblem.sample_output || '-' }}</pre>
            </div>
          </div>

          <!-- 测试输入输出（如果有） -->
          <div v-if="currentTestProblem.test_input || currentTestProblem.test_output" style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 15px;">
            <div style="background: #fff; border: 1px dashed #dcdfe6; border-radius: 8px; padding: 12px;">
              <div style="font-weight: bold; color: #909399; margin-bottom: 8px; font-size: 14px;">测试输入 <span style="font-weight: normal; font-size: 12px;">(学生不可见)</span></div>
              <pre style="background: #fafafa; padding: 10px; border-radius: 6px; font-family: 'Monaco', 'Menlo', monospace; font-size: 13px; margin: 0; white-space: pre-wrap; word-break: break-all; max-height: 100px; overflow-y: auto;">{{ currentTestProblem.test_input || '-' }}</pre>
            </div>
            <div style="background: #fff; border: 1px dashed #dcdfe6; border-radius: 8px; padding: 12px;">
              <div style="font-weight: bold; color: #909399; margin-bottom: 8px; font-size: 14px;">测试输出 <span style="font-weight: normal; font-size: 12px;">(学生不可见)</span></div>
              <pre style="background: #fafafa; padding: 10px; border-radius: 6px; font-family: 'Monaco', 'Menlo', monospace; font-size: 13px; margin: 0; white-space: pre-wrap; word-break: break-all; max-height: 100px; overflow-y: auto;">{{ currentTestProblem.test_output || '-' }}</pre>
            </div>
          </div>
        </div>

        <!-- 代码输入区域 -->
        <div style="margin-bottom: 20px;">
          <label style="font-weight: bold; color: #606266; margin-bottom: 10px; display: block; font-size: 15px;">输入代码</label>
          <div style="position: relative;">
            <textarea
              v-model="testCode"
              :rows="18"
              style="width: 100%; padding: 15px; font-family: 'Monaco', 'Menlo', 'Consolas', monospace; font-size: 14px; border: 1px solid #dcdfe6; border-radius: 10px; resize: vertical; line-height: 1.6; min-height: 300px;"
              placeholder="请输入要测试的代码..."
            ></textarea>
          </div>
        </div>

        <!-- 测试结果 -->
        <div v-if="testResult || testOutput || testError" style="margin-top: 20px; padding: 20px; border-radius: 12px; background: #f8f9fa;">
          <h4 style="margin-bottom: 15px; color: #303133; font-size: 15px; border-bottom: 1px solid #e4e7ed; padding-bottom: 10px;">测试结果</h4>
          <div v-if="testResult === 'success'" style="color: #67c23a; font-weight: bold; margin-bottom: 15px; font-size: 15px;">
            ✓ 测试通过！代码运行结果与预期一致。
          </div>
          <div v-else-if="testResult === 'failed'" style="color: #f56c6c; font-weight: bold; margin-bottom: 15px; font-size: 15px;">
            ✗ 测试失败！代码运行结果与预期不符。
          </div>
          <div v-if="testOutput" style="margin-bottom: 15px;">
            <div style="font-weight: bold; color: #606266; margin-bottom: 8px;">程序输出</div>
            <pre style="background: #fff; padding: 15px; border-radius: 8px; font-family: 'Monaco', 'Menlo', monospace; font-size: 13px; border: 1px solid #e4e7ed; white-space: pre-wrap; word-break: break-all; max-height: 200px; overflow-y: auto; margin: 0;">{{ testOutput }}</pre>
          </div>
          <div v-if="testError" style="margin-bottom: 15px;">
            <div style="font-weight: bold; color: #f56c6c; margin-bottom: 8px;">错误信息</div>
            <pre style="background: #fff; padding: 15px; border-radius: 8px; font-family: 'Monaco', 'Menlo', monospace; font-size: 13px; border: 1px solid #fbc6c6; white-space: pre-wrap; word-break: break-all; max-height: 200px; overflow-y: auto; margin: 0; color: #f56c6c;">{{ testError }}</pre>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showTestDialog = false">关闭</el-button>
        <el-button type="primary" :loading="testing" @click="handleTestSubmit">提交测试</el-button>
      </template>
    </el-dialog>

    <!-- 教师测试提交记录对话框 -->
    <el-dialog v-model="showTeacherSubmissionsDialog" title="我的测试提交记录" width="95%" top="5vh">
      <div style="max-height: 75vh; overflow-y: auto;">
        <el-table :data="teacherSubmissions" v-loading="teacherSubmissionsLoading" style="width: 100%" stripe>
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="problem_title" label="题目" min-width="200" show-overflow-tooltip />
          <el-table-column prop="problem_category" label="分类" width="150" show-overflow-tooltip />
          <el-table-column label="测试结果" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.ai_feedback?.test_result === 'success' ? 'success' : 'danger'" size="small">
                {{ scope.row.ai_feedback?.test_result === 'success' ? '通过' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="submission_time" label="提交时间" width="180">
            <template #default="scope">
              {{ scope.row.submission_time ? new Date(scope.row.submission_time).toLocaleString() : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="scope">
              <el-button type="primary" size="small" @click="viewTeacherSubmissionCode(scope.row)">
                查看代码
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="showTeacherSubmissionsDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 查看教师提交代码详情对话框 -->
    <el-dialog v-model="showTeacherSubmissionCodeDialog" :title="`代码详情 - ${currentTeacherSubmission?.problem_title || ''}`" width="95%" top="5vh">
      <div v-if="currentTeacherSubmission" style="max-height: 70vh; overflow-y: auto; padding: 10px;">
        <!-- 提交信息 -->
        <div style="margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
          <div style="display: flex; gap: 30px; flex-wrap: wrap;">
            <div><strong>提交时间：</strong>{{ currentTeacherSubmission.submission_time ? new Date(currentTeacherSubmission.submission_time).toLocaleString() : '-' }}</div>
            <div><strong>题目分类：</strong>{{ currentTeacherSubmission.problem_category || '-' }}</div>
            <div>
              <strong>测试结果：</strong>
              <el-tag :type="currentTeacherSubmission.ai_feedback?.test_result === 'success' ? 'success' : 'danger'" size="small">
                {{ currentTeacherSubmission.ai_feedback?.test_result === 'success' ? '通过' : '失败' }}
              </el-tag>
            </div>
          </div>
        </div>

        <!-- 代码内容 -->
        <div style="margin-bottom: 20px;">
          <label style="font-weight: bold; color: #606266; margin-bottom: 10px; display: block;">提交的代码</label>
          <pre style="background: #1e1e1e; color: #d4d4d4; padding: 20px; border-radius: 10px; font-family: 'Monaco', 'Menlo', monospace; font-size: 14px; line-height: 1.6; overflow-x: auto; white-space: pre-wrap; word-break: break-all; min-height: 200px;">{{ currentTeacherSubmission.code_content }}</pre>
        </div>

        <!-- 运行结果 -->
        <div v-if="currentTeacherSubmission.ai_feedback?.execution_output" style="margin-bottom: 20px;">
          <label style="font-weight: bold; color: #606266; margin-bottom: 10px; display: block;">程序输出</label>
          <pre style="background: #f8f9fa; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 13px; border: 1px solid #e4e7ed; white-space: pre-wrap; word-break: break-all;">{{ currentTeacherSubmission.ai_feedback.execution_output }}</pre>
        </div>

        <!-- 错误信息 -->
        <div v-if="currentTeacherSubmission.ai_feedback?.error_message" style="margin-bottom: 20px;">
          <label style="font-weight: bold; color: #f56c6c; margin-bottom: 10px; display: block;">错误信息</label>
          <pre style="background: #fef0f0; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 13px; border: 1px solid #fbc6c6; color: #f56c6c; white-space: pre-wrap; word-break: break-all;">{{ currentTeacherSubmission.ai_feedback.error_message }}</pre>
        </div>
      </div>
      <template #footer>
        <el-button @click="showTeacherSubmissionCodeDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showGenerateDialog" title="AI生成编程题目" width="500px">
      <el-form :model="generateForm" label-width="100px">
        <el-form-item label="知识点">
          <el-input
            v-model="generateForm.topic"
            :placeholder="topicPlaceholder"
          />
        </el-form-item>
        <el-form-item label="生成数量">
          <el-input-number
            v-model="generateForm.count"
            :min="1"
            :max="10"
            placeholder="请输入生成数量"
          />
        </el-form-item>
        <el-form-item label="难度等级">
          <el-select v-model="generateForm.difficulty" placeholder="请选择难度等级" style="width: 100%">
            <el-option label="入门" value="入门" />
            <el-option label="基础" value="基础" />
            <el-option label="提高" value="提高" />
          </el-select>
        </el-form-item>
        <el-form-item label="自定义函数">
          <el-select v-model="generateForm.require_custom_function" placeholder="是否需要自定义函数" style="width: 100%">
            <el-option label="是" value="true" />
            <el-option label="否" value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="编程语言">
          <el-select v-model="generateForm.language" placeholder="请选择编程语言" style="width: 100%">
            <el-option label="Python" value="python" />
            <el-option label="C" value="c" />
            <el-option label="C++" value="cpp" />
            <el-option label="Java" value="java" />
            <el-option label="Go" value="go" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showGenerateDialog = false">取消</el-button>
        <el-button type="primary" :loading="generating" @click="handleGenerate">生成题目</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showAddHomeworkDialog" :title="editingHomework ? '编辑作业与测验' : '添加作业与测验'" width="600px">
      <el-form :model="homeworkForm" label-width="100px">
        <el-form-item label="标题">
          <el-input v-model="homeworkForm.title" placeholder="请输入作业标题" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="homeworkForm.type" placeholder="请选择类型" style="width: 100%">
            <el-option label="作业" value="homework" />
            <el-option label="测验" value="quiz" />
          </el-select>
        </el-form-item>
        <el-form-item label="编程语言">
          <el-select v-model="homeworkForm.language" placeholder="请选择编程语言" style="width: 100%">
            <el-option label="Python" value="python" />
            <el-option label="C" value="c" />
            <el-option label="C++" value="cpp" />
            <el-option label="Java" value="java" />
            <el-option label="Go" value="go" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级">
          <el-select v-model="homeworkForm.class_name" placeholder="请选择班级（多选），不选择则所有班级可见" style="width: 100%" multiple>
            <el-option v-for="cls in classList" :key="cls" :label="cls" :value="cls" />
          </el-select>
        </el-form-item>
        <el-form-item label="题目编号">
          <el-input v-model="homeworkForm.problem_numbers" placeholder="请用逗号分隔，如：1,2,3" @input="handleProblemNumbersChange" />
        </el-form-item>
        <el-form-item label="题目分数">
          <el-input v-model="homeworkForm.problem_scores" placeholder="请用逗号分隔，如：30,30,40，不填写则自动平均分配" />
        </el-form-item>
        <el-form-item>
          <el-button link @click="autoAssignScores">自动分配分数</el-button>
        </el-form-item>
        <el-form-item label="开始时间">
          <el-date-picker
            v-model="homeworkForm.start_time"
            type="datetime"
            placeholder="选择开始时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker
            v-model="homeworkForm.end_time"
            type="datetime"
            placeholder="选择结束时间"
            style="width: 100%"
          />
        </el-form-item>
        
        <!-- 题目详情显示区域 -->
        <el-form-item v-if="homeworkProblemDetails.length > 0" label="题目详情">
          <div class="problem-details">
            <div 
              v-for="(detail, index) in homeworkProblemDetails" 
              :key="index" 
              class="problem-detail-item"
            >
              <span class="problem-number">第{{ detail.problem_number }}题：</span>
              <span class="problem-title">{{ detail.title }}</span>
              <span v-if="detail.category" class="problem-category">【{{ detail.category }}】</span>
              <span :class="['problem-difficulty', detail.difficulty]">【{{ detail.difficulty }}】</span>
            </div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddHomeworkDialog = false">取消</el-button>
        <el-button type="primary" :loading="addingHomework" @click="editingHomework ? handleEditHomework() : handleAddHomework()">
          {{ editingHomework ? '更新作业' : '添加作业' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 修改学生密码对话框 -->
    <el-dialog v-model="showChangePasswordDialog" title="修改学生密码" width="500px">
      <el-form :model="changePasswordForm" :rules="changePasswordRules" ref="changePasswordFormRef" label-width="120px">
        <el-form-item label="登录用户名">
          <el-input v-model="changePasswordForm.username" disabled />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="changePasswordForm.newPassword" type="password" placeholder="请输入新密码" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="changePasswordForm.confirmPassword" type="password" placeholder="请确认新密码" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showChangePasswordDialog = false">取消</el-button>
        <el-button type="primary" :loading="changingPassword" @click="handleChangePassword">
          确认修改
        </el-button>
      </template>
    </el-dialog>

    <!-- 题目提交记录对话框 -->
    <el-dialog v-model="showSubmissionDialog" :title="`题目提交记录 - ${currentProblem?.title || ''}`" width="80%" top="5vh">
      <div class="submission-records-container">
        <el-table :data="submissionRecords" style="width: 100%">
          <el-table-column prop="student_id" label="学号" width="120">
            <template #default="scope">
              <span v-if="scope.row.student_id">{{ scope.row.student_id }}</span>
              <span v-else-if="scope.row.teacher_id" style="color: #E6A23C;">教师</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="student_name" label="姓名" width="120">
            <template #default="scope">
              <span v-if="scope.row.student_name">{{ scope.row.student_name }}</span>
              <span v-else-if="scope.row.teacher_name" style="color: #E6A23C;">{{ scope.row.teacher_name }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="submission_time" label="提交时间" width="180" />
          <el-table-column label="运行结果" width="100">
            <template #default="scope">
              <el-tag v-if="scope.row.is_correct === true" type="success">✓</el-tag>
              <el-tag v-else-if="scope.row.is_correct === false" type="danger">×</el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="code_content" label="代码内容">
            <template #default="scope">
              <el-popover
                placement="right"
                :width="400"
                trigger="click"
              >
                <template #reference>
                  <el-button link size="small">查看代码</el-button>
                </template>
                <pre>{{ scope.row.code_content }}</pre>
              </el-popover>
            </template>
          </el-table-column>
          <el-table-column prop="ai_feedback" label="AI反馈">
            <template #default="scope">
              <el-popover
                placement="right"
                :width="400"
                trigger="click"
              >
                <template #reference>
                  <el-button link size="small">查看反馈</el-button>
                </template>
                <div v-if="scope.row.ai_feedback">
                  <div v-for="(value, key) in JSON.parse(scope.row.ai_feedback)" :key="key">
                    <strong>{{ key }}:</strong> {{ value }}
                  </div>
                </div>
                <div v-else>无反馈</div>
              </el-popover>
            </template>
          </el-table-column>
        </el-table>
        
        <div v-if="submissionRecords.length === 0" style="text-align: center; padding: 40px;">
          <el-empty description="暂无提交记录" />
        </div>
      </div>
    </el-dialog>

    <!-- 学生知识掌握图谱对话框 -->
    <el-dialog v-model="showKnowledgeGraphDialog" :title="`学生知识掌握图谱 - ${currentStudent?.class_name || ''} - ${currentStudent?.student_id || ''} - ${currentStudent?.name || ''}`" width="95%" top="2vh" height="90vh">
      <div class="knowledge-graph-container" style="height: 85vh; overflow-y: auto; overflow-x: hidden; padding-right: 10px;">
        <div class="language-buttons" style="margin-bottom: 20px;">
          <el-button 
            v-for="lang in languages" 
            :key="lang.value"
            :type="selectedLanguage === lang.value ? 'primary' : 'default'"
            @click="selectLanguage(lang.value)"
          >
            {{ lang.label }}
          </el-button>
        </div>
        
        <div v-show="knowledgeData" class="chart-container" style="height: calc(100% - 100px);">
          <div class="chart-wrapper" style="height: 60%; display: flex; align-items: stretch; gap: 20px;">
            <div 
              id="knowledge-chart" 
              style="flex: 1; border: 1px solid #eee; min-height: 300px;"
            ></div>
            <div 
              id="mastery-pie" 
              style="flex: 1; border: 1px solid #eee; min-height: 300px;"
            ></div>
          </div>
          
          <!-- 知识点推荐按钮 -->
          <div class="knowledge-recommend-buttons" style="margin-top: 10px;">
            <h4 style="margin-bottom: 10px;">个性化推荐</h4>
            <div class="button-grid" style="display: flex; gap: 10px; flex-wrap: wrap;">
              <div 
                v-for="node in filteredNodes" 
                :key="node.id"
                class="knowledge-item"
                style="display: flex; flex-direction: column; align-items: center; margin-right: 20px; margin-bottom: 10px;"
              >
                <span style="margin-bottom: 5px;">{{ node.name.includes('-') ? node.name.split('-')[1] : node.name }}</span>
                <el-button 
                  type="primary" 
                  size="small" 
                  :loading="aiGenerating[node.id]"
                  @click="generateAIRecommendationsForTopic(node)"
                >
                  <el-icon><Star /></el-icon>
                  AI生成推荐
                </el-button>
              </div>
            </div>
          </div>
          
          <!-- 柱状图：知识点掌握率 -->
          <div class="bar-chart-container" style="margin-top: 30px; border: 1px solid #eee; min-height: 250px;">
            <div id="mastery-bar" style="width: 100%; height: 250px;"></div>
          </div>
        </div>
        
        <div v-if="!knowledgeData" class="empty-state">
          <el-empty description="暂无数据" />
        </div>
      </div>
    </el-dialog>

    <!-- 班级知识掌握图谱对话框 -->
    <el-dialog v-model="showClassKnowledgeGraphDialog" :title="`班级知识掌握图谱 - ${currentClassName}`" width="95%" top="2vh" height="90vh">
      <div class="knowledge-graph-container" style="height: 85vh; overflow-y: auto; overflow-x: hidden; padding-right: 10px;">
        <div class="language-buttons" style="margin-bottom: 20px;">
          <el-button 
            v-for="lang in languages" 
            :key="lang.value"
            :type="selectedLanguage === lang.value ? 'primary' : 'default'"
            @click="selectLanguage(lang.value)"
          >
            {{ lang.label }}
          </el-button>
        </div>
        
        <div v-show="classKnowledgeData && !classKnowledgeData.no_data" class="chart-container" style="height: calc(100% - 100px);">
          <!-- 关系图和饼图 -->
          <div class="chart-wrapper" style="height: 60%; display: flex; align-items: stretch; gap: 20px;">
            <div 
              id="class-knowledge-chart" 
              style="flex: 1; border: 1px solid #eee; min-height: 300px;"
            ></div>
            <div 
              id="class-mastery-pie" 
              style="flex: 1; border: 1px solid #eee; min-height: 300px;"
            ></div>
          </div>
          
          <!-- 柱状图：知识点掌握率 -->
          <div class="bar-chart-container" style="margin-top: 30px; border: 1px solid #eee; min-height: 250px;">
            <div id="class-mastery-bar" style="width: 100%; height: 250px;"></div>
          </div>
        </div>
        
        <div v-if="!classKnowledgeData || classKnowledgeData.no_data" class="empty-state" style="height: 400px; display: flex; align-items: center; justify-content: center;">
          <el-empty description="暂无数据" />
        </div>
      </div>
    </el-dialog>

    <!-- 作业成绩查看对话框 -->
    <el-dialog v-model="showHomeworkScoresDialog" :title="`作业成绩 - ${currentHomework?.title || ''}`" width="90%" top="5vh">
      <div class="homework-scores-container">
        <div class="scores-header" style="margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
          <div>
            <span style="margin-right: 20px;">题目编号：{{ currentHomework?.problem_numbers || '-' }}</span>
            <span>班级：{{ currentHomework?.class_name || '全部班级' }}</span>
          </div>
          <el-button type="primary" @click="exportHomeworkScores">
            <el-icon><Download /></el-icon>
            导出Excel
          </el-button>
        </div>
        
        <el-table :data="homeworkScores" style="width: 100%" border>
          <el-table-column prop="student_id" label="学号" width="120" fixed />
          <el-table-column prop="student_name" label="姓名" width="120" fixed />
          <el-table-column prop="class_name" label="班级" width="150" fixed />
          <el-table-column 
            v-for="(problem, index) in homeworkProblemColumns" 
            :key="index"
            :label="`第${index + 1}题`"
            width="100"
            align="center"
          >
            <template #default="scope">
              <span :style="{ color: getScoreColor(scope.row.scores[index]) }">
                {{ scope.row.scores[index] !== undefined ? scope.row.scores[index] : '-' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="total_score" label="总分" width="100" fixed="right" align="center">
            <template #default="scope">
              <span style="font-weight: bold; color: #409EFF;">{{ scope.row.total_score }}</span>
            </template>
          </el-table-column>
        </el-table>
        
        <div v-if="homeworkScores.length === 0" class="empty-state" style="margin-top: 20px;">
          <el-empty description="暂无学生成绩数据" />
        </div>
      </div>
    </el-dialog>

    <!-- 修改题目号对话框 -->
    <el-dialog v-model="editProblemNumberVisible" :title="`修改题目号 - ${currentEditingHomework?.title || ''}`" width="600px">
      <div style="margin-bottom: 20px;">
        <p style="color: #666; margin-bottom: 10px;">请输入新的题目号（多个题目号用逗号分隔）：</p>
        <el-input
          v-model="editProblemNumbers"
          placeholder="例如：1, 2, 3, 1001"
          @input="fetchProblemDetails"
        />
      </div>
      
      <!-- 修改生成时间 -->
      <div style="margin-bottom: 20px;">
        <p style="color: #666; margin-bottom: 10px;">修改生成时间：</p>
        <el-date-picker
          v-model="editGeneratedAt"
          type="datetime"
          placeholder="选择日期时间"
          format="YYYY-MM-DD HH:mm:ss"
          value-format="YYYY-MM-DD HH:mm:ss"
        />
      </div>
      
      <!-- 题目信息展示 -->
      <div v-if="editProblemDetails.length > 0" style="max-height: 300px; overflow-y: auto; border: 1px solid #eee; border-radius: 4px; padding: 10px;">
        <p style="font-weight: bold; margin-bottom: 10px; color: #333;">题目详情：</p>
        <div 
          v-for="(detail, index) in editProblemDetails" 
          :key="index"
          style="display: flex; justify-content: space-between; align-items: center; padding: 8px; border-bottom: 1px solid #f0f0f0;"
          :class="{ 'text-red-500': detail.notFound }"
        >
          <div>
            <span style="font-weight: bold; margin-right: 10px;">{{ detail.number }}</span>
            <span>{{ detail.title }}</span>
          </div>
          <el-tag :type="detail.notFound ? 'warning' : getDifficultyType(detail.difficulty)" size="small">
            {{ detail.difficulty }}
          </el-tag>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="editProblemNumberVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEditedProblemNumbers">确定</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { User, Menu, Star, TrendCharts, Picture, Document, Notebook, Download, Setting } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import api from '../../services/api'

const router = useRouter()

const students = ref([])
const filteredStudents = ref([])
const searchUsername = ref('')
const searchClass = ref('')
const classList = ref([])
const studentCount = ref(0)
const todaySubmissions = ref(0)
const showImportDialog = ref(false)
const importing = ref(false)
const selectedFile = ref(null)

// 导入题目相关
const showImportProblemDialog = ref(false)
const importingProblems = ref(false)
const importProblemFile = ref(null)

// 左侧菜单相关
const activeMenu = ref('students')

// AI推荐管理相关
const aiRecommendations = ref([])
const aiLoading = ref(false)
const aiHomeworkList = ref([])
const aiHomeworkLoading = ref(false)
const originalAiHomeworkList = ref([])
const searchStudentNumber = ref('')
const searchStudentName = ref('')
const searchRecommendClass = ref('')

// AI推荐管理分页相关
const aiHomeworkCurrentPage = ref(1)
const aiHomeworkPageSize = ref(15)
const aiHomeworkTotal = ref(0)
const aiHomeworkTotalPages = ref(0)

// 题目相关
const problems = ref([])
const showAddProblemDialog = ref(false)
const addingProblem = ref(false)
const editingProblem = ref(false)
const currentProblemId = ref(null)
const fileInput = ref(null)
const editorContainer = ref(null)
const problemForm = ref({
  title: '',
  description: '',
  input_description: '',
  output_description: '',
  sample_input: '',
  sample_output: '',
  test_input: '',
  test_output: '',
  category: '',
  required_functions: '',
  difficulty: '入门'
})

// 分类相关
const categories = ref([])

// 搜索条件
const searchProblemNumber = ref('')
const searchCategory = ref('')
const searchDifficulty = ref('')

// 监听搜索条件变化
watch([searchProblemNumber, searchCategory, searchDifficulty], () => {
  loadProblemsWithFilters(1)
})

// 难度等级列表
const difficultyLevels = ['入门', '基础', '提高']

// 测试提交相关
const showTestDialog = ref(false)
const currentTestProblem = ref(null)
const testCode = ref('')
const testResult = ref('')
const testOutput = ref('')
const testError = ref('')
const testing = ref(false)

// 教师提交记录相关
const showTeacherSubmissionsDialog = ref(false)
const teacherSubmissions = ref([])
const teacherSubmissionsLoading = ref(false)
const showTeacherSubmissionCodeDialog = ref(false)
const currentTeacherSubmission = ref(null)

// 分页相关
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const totalPages = ref(0)

// 计算属性：控制题目对话框的显示状态
const isProblemDialogVisible = computed({
  get() {
    return showAddProblemDialog.value || editingProblem.value
  },
  set(value) {
    if (!value) {
      showAddProblemDialog.value = false
      editingProblem.value = false
      currentProblemId.value = null
      resetProblemForm()
    }
  }
})

// 重置题目表单
const resetProblemForm = () => {
  problemForm.value = {
    title: '',
    description: '',
    input_description: '',
    output_description: '',
    sample_input: '',
    sample_output: '',
    test_input: '',
    test_output: '',
    category: '',
    required_functions: '',
    difficulty: '入门'
  }
}

// 打开添加题目对话框
const openAddProblemDialog = () => {
  resetProblemForm()
  editingProblem.value = false
  currentProblemId.value = null
  showAddProblemDialog.value = true
}

// AI生成题目相关
const showGenerateDialog = ref(false)
const generating = ref(false)
const aiGenerating = ref({}) // 改为对象，存储每个知识点的加载状态
const generateForm = ref({
  topic: '',
  count: 3,
  difficulty: '入门',
  require_custom_function: 'true',
  language: 'python'
})

// 知识点输入框的动态提示文字
const topicPlaceholder = computed(() => {
  const languageMap = {
    'python': 'Python',
    'c': 'C',
    'cpp': 'C++',
    'java': 'Java',
    'go': 'Go'
  }
  const languageName = languageMap[generateForm.value.language] || 'Python'
  return `请输入要生成的${languageName}知识点，如：循环、函数、列表等`
})

// 备份数据库相关
const backingUp = ref(false)
const backupHistory = ref([])

// 作业与测验相关
const homeworks = ref([])
const showAddHomeworkDialog = ref(false)
const addingHomework = ref(false)
const editingHomework = ref(false)
const currentHomeworkId = ref(null)
const homeworkForm = ref({
  title: '',
  type: 'homework',
  language: '',
  class_name: [],
  problem_numbers: '',
  problem_scores: '',
  start_time: '',
  end_time: ''
})
const homeworkProblemDetails = ref([])

// 修改学生密码相关
const showChangePasswordDialog = ref(false)
const changingPassword = ref(false)
const changePasswordFormRef = ref(null)
const teacherChangePasswordFormRef = ref(null)
const currentStudent = ref(null)
const changePasswordForm = ref({
  username: '',
  newPassword: '',
  confirmPassword: ''
})
const validateConfirmPassword = (rule, value, callback) => {
  if (value !== changePasswordForm.value.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}
const changePasswordRules = {
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 教师修改密码相关
const teacherChangePasswordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const teacherChangingPassword = ref(false)

const validateTeacherConfirmPassword = (rule, value, callback) => {
  if (value !== teacherChangePasswordForm.value.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const teacherChangePasswordRules = {
  oldPassword: [
    { required: true, message: '请输入原密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateTeacherConfirmPassword, trigger: 'blur' }
  ]
}

const handleTeacherChangePassword = async () => {
  const formRef = teacherChangePasswordFormRef.value
  if (!formRef) return
  
  try {
    const isValid = await formRef.validate()
    if (!isValid) return
    
    teacherChangingPassword.value = true
    
    const teacherId = localStorage.getItem('userId')
    if (!teacherId) {
      ElMessage.error('未找到教师ID')
      return
    }
    
    const response = await api.changeTeacherPassword(
      teacherId,
      teacherChangePasswordForm.value.oldPassword,
      teacherChangePasswordForm.value.newPassword
    )
    
    if (response.success) {
      ElMessage.success('密码修改成功，请重新登录')
      // 重置表单
      teacherChangePasswordForm.value = {
        oldPassword: '',
        newPassword: '',
        confirmPassword: ''
      }
      // 清除本地存储，强制重新登录
      localStorage.removeItem('token')
      localStorage.removeItem('userId')
      localStorage.removeItem('userRole')
      router.push('/login')
    } else {
      ElMessage.error(response.error || '密码修改失败')
    }
  } catch (error) {
    console.error('修改密码失败:', error)
    const errorMessage = error.response?.data?.error || error.message || '修改密码失败，请检查网络连接'
    ElMessage.error(errorMessage)
  } finally {
    teacherChangingPassword.value = false
  }
}

// 提交记录相关
const showSubmissionDialog = ref(false)
const currentProblem = ref(null)
const submissionRecords = ref([])

// 知识图谱相关
const showKnowledgeGraphDialog = ref(false)
const knowledgeData = ref(null)
const currentStudentId = ref(null)
let chartInstance = null
let pieChartInstance = null

// 班级知识图谱相关
const showClassKnowledgeGraphDialog = ref(false)
const classKnowledgeData = ref(null)
const currentClassName = ref('')
const classAiGenerating = ref({})
let classChartInstance = null
let classPieChartInstance = null
let classBarChartInstance = null

// 作业成绩查看相关
const showHomeworkScoresDialog = ref(false)
const currentHomework = ref(null)
const homeworkScores = ref([])
const homeworkProblemColumns = ref([])

// 班级知识图谱按语言过滤的节点
const filteredClassNodes = computed(() => {
  if (!classKnowledgeData.value?.nodes) return []
  return classKnowledgeData.value.nodes.filter(node => {
    if (node.name.includes('-')) {
      const nodeLanguage = node.name.split('-')[0]
      return nodeLanguage === selectedLanguage.value
    }
    return true
  })
})
let barChartInstance = null

// 语言选项
const languages = [
  { label: 'Python', value: 'Python' },
  { label: 'C', value: 'C' },
  { label: 'C++', value: 'C++' },
  { label: 'Java', value: 'Java' },
  { label: 'Go', value: 'Go' }
]

// 当前选中的语言
const selectedLanguage = ref('Python')

// 计算统计数据
const goodCount = computed(() => {
  if (!knowledgeData.value) return 0
  return filteredNodes.value.filter(node => node.value > 0.7).length
})

const mediumCount = computed(() => {
  if (!knowledgeData.value) return 0
  return filteredNodes.value.filter(node => node.value >= 0.4 && node.value <= 0.7).length
})

const poorCount = computed(() => {
  if (!knowledgeData.value) return 0
  return filteredNodes.value.filter(node => node.value < 0.4).length
})

// 根据选中的语言过滤节点
const filteredNodes = computed(() => {
  if (!knowledgeData.value) return []
  
  // 先过滤出符合条件的节点：只显示当前选中语言的知识点
  const candidates = knowledgeData.value.nodes.filter(node => {
    // 提取知识点的语言部分
    if (node.name.includes('-')) {
      const nodeLanguage = node.name.split('-')[0]
      return nodeLanguage === selectedLanguage.value
    }
    return false
  })
  
  // 去重：对于相同的知识点，只保留一个
  const uniqueNodes = []
  const seenKnowledge = new Set()
  
  for (const node of candidates) {
    // 提取知识点名称
    let knowledgeName = node.name
    
    // 如果这个知识点还没见过，就添加到结果中
    if (!seenKnowledge.has(knowledgeName)) {
      seenKnowledge.add(knowledgeName)
      uniqueNodes.push(node)
    }
  }
  
  return uniqueNodes
})

// 编辑器相关函数
const insertImage = () => {
  fileInput.value.click()
}

const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      const img = document.createElement('img')
      img.src = e.target.result
      img.style.maxWidth = '100%'
      img.style.maxHeight = '400px'

      if (editorContainer.value) {
        // 将图片插入到编辑器中
        const selection = window.getSelection()
        if (selection.rangeCount > 0) {
          const range = selection.getRangeAt(0)
          range.insertNode(img)
          range.collapse(false)
          selection.removeAllRanges()
          selection.addRange(range)
        } else {
          editorContainer.value.appendChild(img)
        }
        // 更新 description
        problemForm.value.description = editorContainer.value.innerHTML
      }
    }
    reader.readAsDataURL(file)
  }
}

const handleEditorInput = () => {
  if (editorContainer.value) {
    problemForm.value.description = editorContainer.value.innerHTML
  }
}

const loadStudents = async () => {
  try {
    const response = await api.getAllStudents()
    if (response.success) {
      students.value = response.students || []
      studentCount.value = students.value.length
      // 提取班级列表
      const classes = new Set()
      students.value.forEach(student => {
        if (student.class_name) {
          classes.add(student.class_name)
        }
      })
      classList.value = Array.from(classes).sort()
      updateFilteredStudents()
    }
  } catch (error) {
    console.error('获取学生列表失败:', error)
  }
}

const updateFilteredStudents = () => {
  filteredStudents.value = students.value.filter(student => {
    const matchUsername = !searchUsername.value || 
      student.username.toLowerCase().includes(searchUsername.value.toLowerCase())
    const matchClass = !searchClass.value || 
      student.class_name === searchClass.value
    return matchUsername && matchClass
  })
}

const handleSearch = () => {
  updateFilteredStudents()
}

// 题目搜索
const handleProblemSearch = () => {
  loadProblemsWithFilters(1)
}

const loadProblems = async (page = 1) => {
  try {
    const response = await api.getProblems(page, pageSize.value)
    if (response.success) {
      problems.value = response.problems || []
      total.value = response.total || 0
      totalPages.value = response.total_pages || 1
      currentPage.value = response.page || 1
    }
  } catch (error) {
    console.error('获取题目列表失败:', error)
  }
}

const loadProblemsWithFilters = async (page = 1) => {
  try {
    const searchParams = {
      problemNumber: searchProblemNumber.value || undefined,
      category: searchCategory.value || undefined,
      difficulty: searchDifficulty.value || undefined
    }
    const response = await api.getProblems(page, pageSize.value, searchParams)
    if (response.success) {
      problems.value = response.problems || []
      total.value = response.total || 0
      totalPages.value = response.total_pages || 1
      currentPage.value = response.page || 1
    }
  } catch (error) {
    console.error('获取题目列表失败:', error)
  }
}

// 将题目添加到作业
const addProblemToHomeworks = async (problem, homeworkIds) => {
  if (!homeworkIds || homeworkIds.length === 0) return
  
  try {
    for (const homeworkId of homeworkIds) {
      // 找到对应的作业
      const homework = homeworks.value.find(hw => hw.id === homeworkId)
      if (!homework) continue
      
      // 获取当前作业的题目编号列表
      const currentProblems = homework.problem_numbers 
        ? homework.problem_numbers.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n))
        : []
      
      // 检查题目是否已存在
      if (currentProblems.includes(problem.problem_number)) {
        continue
      }
      
      // 添加新题目编号
      currentProblems.push(problem.problem_number)
      
      // 更新作业
      const response = await api.updateHomework(homeworkId, {
        problem_numbers: currentProblems.join(','),
        problem_scores: homework.problem_scores
      })
      
      if (!response.success) {
        ElMessage.error(`添加到作业 "${homework.title}" 失败`)
      }
    }
    
    ElMessage.success('题目已成功添加到选中的作业')
    // 重新加载作业列表
    loadHomeworks()
  } catch (error) {
    console.error('添加题目到作业失败:', error)
    ElMessage.error('添加题目到作业失败')
  }
}

const loadCategories = async () => {
  try {
    const response = await api.getProblemCategories()
    if (response.success) {
      categories.value = response.categories || []
    }
  } catch (error) {
    console.error('获取分类列表失败:', error)
  }
}

// 处理左侧菜单选择
const handleMenuSelect = (key) => {
  activeMenu.value = key
  
  // 根据不同菜单加载相应数据
  if (key === 'ai-recommend') {
    loadAIHomeworkList()
  } else if (key === 'students') {
    loadTodaySubmissions()
  }
}



// 处理文件选择
const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

// 处理题目文件选择
const handleProblemFileChange = (file) => {
  importProblemFile.value = file.raw
}

const handleImport = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择要导入的Excel文件')
    return
  }

  try {
    importing.value = true
    const response = await api.importStudents(selectedFile.value)

    if (response.success) {
      ElMessage.success(response.message)
      showImportDialog.value = false
      selectedFile.value = null
      loadStudents()
    } else {
      ElMessage.error(response.error || '导入失败')
    }
  } catch (error) {
    console.error('导入失败:', error)
    const errorMessage = error.response?.data?.error || error.message || '导入失败，请检查文件格式和网络连接'
    ElMessage.error(errorMessage)
  } finally {
    importing.value = false
  }
}

const handleAddProblem = async () => {
  if (!problemForm.value.title || !problemForm.value.description) {
    ElMessage.warning('请填写题目标题和描述')
    return
  }

  try {
    addingProblem.value = true
    const response = await api.addProblem(problemForm.value)

    if (response.success) {
      ElMessage.success(response.message)
      isProblemDialogVisible.value = false
      // 重置表单
      problemForm.value = {
        title: '',
        description: '',
        input_description: '',
        output_description: '',
        sample_input: '',
        sample_output: '',
        test_input: '',
        test_output: '',
        category: '',
        required_functions: '',
        difficulty: '入门'
      }
      loadProblems(currentPage.value)
    } else {
      ElMessage.error(response.error || '添加题目失败')
    }
  } catch (error) {
    console.error('添加题目失败:', error)
    const errorMessage = error.response?.data?.error || error.message || '添加题目失败，请检查网络连接'
    ElMessage.error(errorMessage)
  } finally {
    addingProblem.value = false
  }
}

const handleGenerate = async () => {
  if (!generateForm.value.topic) {
    ElMessage.warning('请输入要生成的知识点')
    return
  }

  if (!generateForm.value.count || generateForm.value.count < 1) {
    ElMessage.warning('请输入有效的生成数量')
    return
  }

  try {
    generating.value = true
    const response = await api.generateProblems(
      generateForm.value.topic,
      generateForm.value.count,
      generateForm.value.difficulty,
      generateForm.value.require_custom_function === 'true',
      generateForm.value.language
    )

    if (response.success) {
      ElMessage.success(response.message)
      showGenerateDialog.value = false
      // 重置表单
      generateForm.value = {
        topic: '',
        count: 3,
        language: 'python'
      }
      loadProblems(currentPage.value)
    } else {
      ElMessage.error(response.error || '生成题目失败')
    }
  } catch (error) {
    console.error('生成题目失败:', error)
    const errorMessage = error.response?.data?.error || error.message || '生成题目失败，请检查网络连接'
    ElMessage.error(errorMessage)
  } finally {
    generating.value = false
  }
}

const deleteProblem = async (problem) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除题目 ${problem.problem_number}. ${problem.title} 吗？`,
      '删除题目',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await api.deleteProblem(problem.id)

    if (response.success) {
      ElMessage.success(response.message)
      loadProblems(currentPage.value)
    } else {
      ElMessage.error(response.error || '删除题目失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除题目失败:', error)
      const errorMessage = error.response?.data?.error || error.message || '删除题目失败，请检查网络连接'
      ElMessage.error(errorMessage)
    }
  }
}

const editProblem = async (problem) => {
  try {
    const response = await api.getProblemDetail(problem.id)
    if (response.success) {
      const problemData = response.problem
      problemForm.value = {
        title: problemData.title || '',
        description: problemData.description || '',
        input_description: problemData.input_description || '',
        output_description: problemData.output_description || '',
        sample_input: problemData.sample_input || '',
        sample_output: problemData.sample_output || '',
        test_input: problemData.test_input || '',
        test_output: problemData.test_output || '',
        category: problemData.category || '',
        required_functions: problemData.required_functions || '',
        difficulty: problemData.difficulty || '入门'
      }
      currentProblemId.value = problem.id
      editingProblem.value = true
      await nextTick()
      if (editorContainer.value) {
        editorContainer.value.innerHTML = problemForm.value.description || ''
      }
    } else {
      ElMessage.error(response.error || '获取题目详情失败')
    }
  } catch (error) {
    console.error('获取题目详情失败:', error)
    const errorMessage = error.response?.data?.error || error.message || '获取题目详情失败，请检查网络连接'
    ElMessage.error(errorMessage)
  }
}

// 通过题目号查看/编辑题目
const viewProblemDetail = async (problemNumber) => {
  try {
    const response = await api.getProblemByNumber(problemNumber)
    if (response.success && response.problem) {
      const problemData = response.problem
      problemForm.value = {
        title: problemData.title || '',
        description: problemData.description || '',
        input_description: problemData.input_description || '',
        output_description: problemData.output_description || '',
        sample_input: problemData.sample_input || '',
        sample_output: problemData.sample_output || '',
        test_input: problemData.test_input || '',
        test_output: problemData.test_output || '',
        category: problemData.category || '',
        required_functions: problemData.required_functions || '',
        difficulty: problemData.difficulty || '入门'
      }
      currentProblemId.value = problemData.id
      editingProblem.value = true
      await nextTick()
      if (editorContainer.value) {
        editorContainer.value.innerHTML = problemForm.value.description || ''
      }
    } else {
      ElMessage.error(response.error || '获取题目详情失败')
    }
  } catch (error) {
    console.error('获取题目详情失败:', error)
    const errorMessage = error.response?.data?.error || error.message || '获取题目详情失败，请检查网络连接'
    ElMessage.error(errorMessage)
  }
}

const testProblem = async (problem) => {
  try {
    const response = await api.getProblemDetail(problem.id)
    if (response.success) {
      currentTestProblem.value = response.problem
      testCode.value = ''
      testResult.value = ''
      testOutput.value = ''
      testError.value = ''
      showTestDialog.value = true
    } else {
      ElMessage.error(response.error || '获取题目详情失败')
    }
  } catch (error) {
    console.error('获取题目详情失败:', error)
    const errorMessage = error.response?.data?.error || error.message || '获取题目详情失败，请检查网络连接'
    ElMessage.error(errorMessage)
  }
}

const handleTestSubmit = async () => {
  if (!testCode.value.trim()) {
    ElMessage.warning('请输入要测试的代码')
    return
  }

  try {
    testing.value = true
    testResult.value = ''
    testOutput.value = ''
    testError.value = ''

    const teacherId = localStorage.getItem('userId')
    const response = await api.testProblem(currentTestProblem.value.id, {
      code: testCode.value,
      teacher_id: teacherId
    })

    if (response.success) {
      testResult.value = response.result
      testOutput.value = response.output
      if (response.result === 'success') {
        ElMessage.success('测试通过！')
      } else {
        ElMessage.warning('测试未通过，请检查代码')
      }
    } else {
      testError.value = response.error || '测试失败'
      ElMessage.error(response.error || '测试失败')
    }
  } catch (error) {
    console.error('测试提交失败:', error)
    testError.value = error.response?.data?.error || error.message || '测试提交失败，请检查网络连接'
    ElMessage.error(testError.value)
  } finally {
    testing.value = false
  }
}

const loadTeacherSubmissions = async () => {
  try {
    teacherSubmissionsLoading.value = true
    const teacherId = localStorage.getItem('userId')
    if (!teacherId) {
      ElMessage.warning('未找到教师ID')
      return
    }
    
    const response = await api.getTeacherSubmissions(teacherId)
    if (response.success) {
      teacherSubmissions.value = response.submissions || []
    } else {
      ElMessage.error(response.error || '获取提交记录失败')
    }
  } catch (error) {
    console.error('获取教师提交记录失败:', error)
    ElMessage.error('获取提交记录失败')
  } finally {
    teacherSubmissionsLoading.value = false
  }
}

const showTeacherSubmissions = async () => {
  await loadTeacherSubmissions()
  showTeacherSubmissionsDialog.value = true
}

const viewTeacherSubmissionCode = (row) => {
  currentTeacherSubmission.value = row
  showTeacherSubmissionCodeDialog.value = true
}

const handleEditProblem = async () => {
  if (!problemForm.value.title || !problemForm.value.description) {
    ElMessage.warning('请填写题目标题和描述')
    return
  }

  try {
    addingProblem.value = true
    const response = await api.updateProblem(currentProblemId.value, problemForm.value)

    if (response.success) {
      ElMessage.success(response.message)
      isProblemDialogVisible.value = false
      // 重置表单
      problemForm.value = {
        title: '',
        description: '',
        input_description: '',
        output_description: '',
        sample_input: '',
        sample_output: '',
        test_input: '',
        test_output: '',
        category: '',
        required_functions: '',
        difficulty: '入门'
      }
      loadProblems(currentPage.value)
    } else {
      ElMessage.error(response.error || '更新题目失败')
    }
  } catch (error) {
    console.error('更新题目失败:', error)
    const errorMessage = error.response?.data?.error || error.message || '更新题目失败，请检查网络连接'
    ElMessage.error(errorMessage)
  } finally {
    addingProblem.value = false
  }
}

const deleteStudent = async (student) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除学生 ${student.student_id} ${student.name} 吗？`,
      '删除学生',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await api.deleteStudent(student.id)

    if (response.success) {
      ElMessage.success(response.message)
      loadStudents()
    } else {
      ElMessage.error(response.error || '删除学生失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除学生失败:', error)
      const errorMessage = error.response?.data?.error || error.message || '删除学生失败，请检查网络连接'
      ElMessage.error(errorMessage)
    }
  }
}

const openChangePasswordDialog = (student) => {
  currentStudent.value = student
  changePasswordForm.value = {
    username: student.username,
    newPassword: '',
    confirmPassword: ''
  }
  showChangePasswordDialog.value = true
}

// 显示题目提交记录
const showSubmissionRecords = async (problem) => {
  currentProblem.value = problem
  showSubmissionDialog.value = true
  
  try {
    const token = localStorage.getItem('token')
    console.log('当前Token:', token)
    console.log('请求题目ID:', problem.id)
    
    const response = await api.getProblemSubmissions(problem.id)
    console.log('API响应:', response)
    
    if (response.success) {
      // 解析 ai_feedback 字段，提取 is_correct 值
      submissionRecords.value = response.submissions.map(item => {
        let isCorrect = null
        if (item.ai_feedback) {
          try {
            const feedback = JSON.parse(item.ai_feedback)
            isCorrect = feedback.is_correct
          } catch (e) {
            console.warn('解析 ai_feedback 失败:', e)
          }
        }
        return {
          ...item,
          is_correct: isCorrect
        }
      })
    } else {
      ElMessage.error(response.error || '加载提交记录失败')
    }
  } catch (error) {
    console.error('加载提交记录失败:', error)
    console.error('错误详情:', error.response || error.message)
    const errorMsg = error.response 
      ? `加载提交记录失败: ${error.response.status} - ${error.response.data?.error || '未知错误'}`
      : '加载提交记录失败: ' + error.message
    ElMessage.error(errorMsg)
  }
}

// 显示学生知识掌握图谱
const showStudentKnowledgeGraph = async (student) => {
  currentStudentId.value = student.id
  currentStudent.value = student
  selectedLanguage.value = 'Python'
  showKnowledgeGraphDialog.value = true
  await loadKnowledgeMap()
}

// 显示班级知识图谱
const showClassKnowledgeGraph = async () => {
  if (!searchClass.value) {
    ElMessage.warning('请先选择班级')
    return
  }
  currentClassName.value = searchClass.value
  selectedLanguage.value = 'Python'
  showClassKnowledgeGraphDialog.value = true
  await loadClassKnowledgeMap()
}

// 导出学生代码到Excel
const exportStudentCode = async (student) => {
  try {
    const response = await api.getStudentSubmissions(student.id)
    if (response.success && response.submissions) {
      const submissions = response.submissions
      
      // 构建CSV内容
      let csvContent = '题号,提交时间,代码内容,正确/错误\n'
      
      submissions.forEach(submission => {
        // 处理代码内容中的特殊字符
        let code = submission.code_content || ''
        // 替换换行符和逗号
        code = code.replace(/\n/g, '\\n').replace(/,/g, '\\,')
        // 如果包含引号，需要用双引号包裹
        if (code.includes('"')) {
          code = code.replace(/"/g, '""')
        }
        code = `"${code}"`
        
        // 格式化提交时间
        const submitTime = submission.submission_time ? 
          new Date(submission.submission_time).toLocaleString('zh-CN') : '未知'
        
        // 获取正确/错误状态
        const isCorrect = submission.is_correct || '未知'
        
        csvContent += `${submission.problem_number || '未知'},${submitTime},${code},${isCorrect}\n`
      })
      
      // 创建并下载文件
      const blob = new Blob([`\uFEFF${csvContent}`], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `${student.name}_${student.student_id}_代码提交记录.csv`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      ElMessage.success('导出成功')
    } else {
      ElMessage.error('获取提交记录失败')
    }
  } catch (error) {
    console.error('导出代码失败:', error)
    ElMessage.error('导出失败')
  }
}

// 加载知识图谱数据
const loadKnowledgeMap = async () => {
  if (!currentStudentId.value) return
  
  try {
    const response = await api.getKnowledgeMap(currentStudentId.value)
    if (response.success) {
      knowledgeData.value = response
      await nextTick()
      renderChart()
    } else {
      ElMessage.error(response.error || '加载知识图谱失败')
    }
  } catch (error) {
    console.error('加载知识图谱失败:', error)
    ElMessage.error('加载知识图谱失败')
  }
}

// 加载班级知识图谱数据
const loadClassKnowledgeMap = async () => {
  if (!currentClassName.value) return
  
  try {
    const response = await api.getClassKnowledgeMap(currentClassName.value)
    if (response.success) {
      classKnowledgeData.value = response
      await nextTick()
      renderClassChart()
    } else {
      ElMessage.error(response.error || '加载班级知识图谱失败')
    }
  } catch (error) {
    console.error('加载班级知识图谱失败:', error)
    ElMessage.error('加载班级知识图谱失败')
  }
}

// 选择语言
const selectLanguage = (language) => {
  selectedLanguage.value = language
  renderChart()
}

// 处理班级推荐前后的掌握率数据
const getClassMasteryData = () => {
  const allKnowledge = new Set()
  const preData = {}
  const postData = {}
  let hasRecommendation = false
  
  // 收集所有知识点
  if (classKnowledgeData.value?.pre_recommend_stats) {
    Object.keys(classKnowledgeData.value.pre_recommend_stats).forEach(key => {
      allKnowledge.add(key)
    })
  }
  if (classKnowledgeData.value?.post_recommend_stats) {
    const postKeys = Object.keys(classKnowledgeData.value.post_recommend_stats)
    if (postKeys.length > 0) {
      hasRecommendation = true
      postKeys.forEach(key => {
        allKnowledge.add(key)
      })
    }
  }
  
  // 如果推荐数据为空，尝试从nodes中获取数据
  if (allKnowledge.size === 0 && classKnowledgeData.value?.nodes) {
    classKnowledgeData.value.nodes.forEach(node => {
      allKnowledge.add(node.name)
      preData[node.name] = node.value
      postData[node.name] = node.value
    })
    hasRecommendation = true
  }
  
  // 计算推荐前掌握率
  if (classKnowledgeData.value?.pre_recommend_stats) {
    Object.entries(classKnowledgeData.value.pre_recommend_stats).forEach(([key, stats]) => {
      if (stats.total > 0) {
        preData[key] = stats.correct / stats.total
      } else {
        preData[key] = 0.5
      }
    })
  }
  
  // 计算推荐后掌握率
  if (classKnowledgeData.value?.post_recommend_stats) {
    Object.entries(classKnowledgeData.value.post_recommend_stats).forEach(([key, stats]) => {
      if (stats.total > 0) {
        postData[key] = stats.correct / stats.total
      } else {
        postData[key] = 0.5
      }
    })
  }
  
  // 检查是否有推荐后数据（只有当post_recommend_stats有数据时才显示推荐后柱子）
  if (Object.keys(classKnowledgeData.value?.post_recommend_stats || {}).length > 0) {
    hasRecommendation = true
  }
  
  // 生成统一的知识点列表
  const knowledgeList = Array.from(allKnowledge)
  
  // 按语言过滤（支持有语言前缀和没有语言前缀的情况）
  const filteredKnowledge = knowledgeList.filter(key => {
    if (key.includes('-')) {
      const nodeLanguage = key.split('-')[0]
      return nodeLanguage === selectedLanguage.value
    }
    // 如果没有语言前缀，默认认为是当前选中语言的数据
    return true
  })
  
  // 提取核心知识点名称
  const coreKnowledgeNames = new Set()
  const uniqueFilteredKnowledge = []
  
  filteredKnowledge.forEach(key => {
    let coreName = key
    if (key.includes('-')) {
      coreName = key.split('-')[1]
    }
    if (!coreKnowledgeNames.has(coreName)) {
      coreKnowledgeNames.add(coreName)
      uniqueFilteredKnowledge.push(key)
    }
  })
  
  // 生成数据
  const xAxisData = []
  const preMasteryData = []
  const postMasteryData = []
  
  // 获取所有有推荐后数据的知识点key
  const postKeys = classKnowledgeData.value?.post_recommend_stats ? Object.keys(classKnowledgeData.value.post_recommend_stats) : []
  
  uniqueFilteredKnowledge.forEach(key => {
    let coreName = key
    if (key.includes('-')) {
      coreName = key.split('-')[1]
    }
    xAxisData.push(coreName)
    
    // 从 preData 获取掌握率，如果没有则尝试从nodes中获取
    let preValue = preData[key]
    if (preValue === undefined) {
      const node = classKnowledgeData.value?.nodes?.find(n => n.name === key)
      preValue = node?.value ?? 0.5
    }
    preMasteryData.push(preValue)
    
    // 只有该知识点有推荐后数据才显示推荐后柱状图，否则显示null（不显示）
    const hasPostData = postKeys.includes(key)
    postMasteryData.push(hasPostData ? postData[key] || 0.5 : null)
  })
  
  // 检查是否有任何知识点有推荐后数据
  const hasAnyRecommendation = postKeys.length > 0
  
  return { xAxisData, preMasteryData, postMasteryData, hasRecommendation: hasAnyRecommendation }
}

// 处理推荐前后的掌握率数据
const getMasteryData = () => {
  const preData = {}
  const postData = {}
  let hasRecommendation = false
  
  // 收集所有知识点（用于显示诊断柱状图）
  const allKnowledge = new Set()
  
  // 计算推荐前掌握率
  if (knowledgeData.value?.pre_recommend_stats) {
    Object.entries(knowledgeData.value.pre_recommend_stats).forEach(([key, stats]) => {
      allKnowledge.add(key)
      if (stats.total > 0) {
        preData[key] = stats.correct / stats.total
      } else {
        preData[key] = 0.5
      }
    })
  }
  
  // 计算推荐后掌握率
  const postKeys = knowledgeData.value?.post_recommend_stats ? Object.keys(knowledgeData.value.post_recommend_stats) : []
  if (postKeys.length > 0) {
    hasRecommendation = true
    Object.entries(knowledgeData.value.post_recommend_stats).forEach(([key, stats]) => {
      if (stats.total > 0) {
        postData[key] = stats.correct / stats.total
      } else {
        postData[key] = 0.5
      }
    })
  }
  
  // 所有知识点都显示诊断柱状图
  const knowledgeList = Array.from(allKnowledge)
  
  // 按语言过滤
  const filteredKnowledge = knowledgeList.filter(key => {
    if (key.includes('-')) {
      const nodeLanguage = key.split('-')[0]
      return nodeLanguage === selectedLanguage.value
    }
    return false
  })
  
  // 提取核心知识点名称
  const coreKnowledgeNames = new Set()
  const uniqueFilteredKnowledge = []
  
  filteredKnowledge.forEach(key => {
    let coreName = key
    if (key.includes('-')) {
      coreName = key.split('-')[1]
    }
    if (!coreKnowledgeNames.has(coreName)) {
      coreKnowledgeNames.add(coreName)
      uniqueFilteredKnowledge.push(key)
    }
  })
  
  // 生成数据
  const xAxisData = []
  const preMasteryData = []
  const postMasteryData = []
  
  uniqueFilteredKnowledge.forEach(key => {
    let coreName = key
    if (key.includes('-')) {
      coreName = key.split('-')[1]
    }
    xAxisData.push(coreName)
    preMasteryData.push(preData[key] || 0.5)
    // 只有该知识点有推荐后数据才显示推荐后掌握率，否则显示null（不显示）
    const hasPostData = postKeys.includes(key)
    postMasteryData.push(hasPostData ? postData[key] || 0.5 : null)
  })
  
  // 检查是否有任何知识点有推荐后数据
  const hasAnyRecommendation = postKeys.length > 0
  
  return { xAxisData, preMasteryData, postMasteryData, hasRecommendation: hasAnyRecommendation }
}

// 渲染图表
const renderChart = () => {
  if (!knowledgeData.value) return
  
  // 初始化关系图
  const chartDom = document.getElementById('knowledge-chart')
  if (chartDom) {
    if (chartInstance) {
      chartInstance.dispose()
    }
    chartInstance = echarts.init(chartDom)
    // 调整图表大小以适应容器
    chartInstance.resize()
    
    // 处理节点颜色和名称
    const nodesWithColor = filteredNodes.value.map(node => {
      // 处理节点名称，只显示短横后面的部分
      let displayName = node.name
      if (displayName.includes('-')) {
        displayName = displayName.split('-')[1]
      }
      
      return {
        id: node.id,
        name: displayName,
        value: node.value,
        category: node.category,
        total: node.total,
        correct: node.correct,
        itemStyle: {
          color: getNodeColor(node.value)
        }
      }
    })
    
    // 生成类别列表
    const categories = [...new Set(filteredNodes.value.map(n => n.category))]
    
    const option = {
      title: {
        text: '知识点掌握图谱',
        subtext: `总提交次数：${knowledgeData.value.submission_count} | 绿色：掌握良好 黄色：需巩固 红色：薄弱`,
        top: 'top',
        left: 'center',
        textStyle: {
          fontSize: 18
        },
        subtextStyle: {
          fontSize: 14
        }
      },
      tooltip: {
        trigger: 'item',
        formatter: function(params) {
          if (params.dataType === 'node') {
            const node = params.data
            const masteryPercent = (node.value * 100).toFixed(1)
            let status = '薄弱'
            if (node.value >= 0.7) status = '掌握良好'
            else if (node.value >= 0.4) status = '需巩固'
            
            let tooltip = `<strong>${node.name}</strong><br/>`
            tooltip += `掌握率: ${masteryPercent}%<br/>`
            tooltip += `状态: ${status}<br/>`
            tooltip += `类别: ${node.category}<br/>`
            if (node.total) {
              tooltip += `提交次数: ${node.total} | 正确: ${node.correct}`
            }
            return tooltip
          }
          return ''
        }
      },
      legend: {
        data: categories,
        bottom: 10,
        textStyle: {
          fontSize: 12
        }
      },
      dataZoom: [{
        type: 'inside',
        start: 0,
        end: 12
      }],
      series: [{
        type: 'graph',
        layout: 'force',
        data: nodesWithColor,
        // 过滤链接，只显示与过滤后节点相关的链接
        links: knowledgeData.value.links.filter(link => {
          const sourceId = typeof link.source === 'object' ? link.source.id : link.source
          const targetId = typeof link.target === 'object' ? link.target.id : link.target
          return nodesWithColor.some(node => node.id === sourceId || node.id === targetId)
        }),
        categories: categories.map(name => ({ name })),
        roam: true,
        label: { show: true, position: 'right', formatter: '{b}', fontSize: 14 },
        lineStyle: { color: 'source', curveness: 0.3 },
        emphasis: { focus: 'adjacency' },
        force: { repulsion: 500, edgeLength: 30, gravity: 0.3 }
      }]
    }
    
    chartInstance.setOption(option)
  }
  
  // 初始化饼图
  const pieDom = document.getElementById('mastery-pie')
  if (pieDom) {
    if (pieChartInstance) {
      pieChartInstance.dispose()
    }
    pieChartInstance = echarts.init(pieDom)
    // 调整图表大小以适应容器
    pieChartInstance.resize()
    
    const pieOption = {
      title: {
        text: '掌握状态分布',
        subtext: `掌握良好：${goodCount.value} 个 | 需要巩固：${mediumCount.value} 个 | 薄弱：${poorCount.value} 个`,
        left: 'center',
        top: 10,
        textStyle: {
          fontSize: 16
        },
        subtextStyle: {
          fontSize: 12,
          color: '#666',
          padding: [5, 0, 15, 0]
        }
      },
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c}个 ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left',
        top: 'middle',
        textStyle: {
          fontSize: 14
        }
      },
      series: [
        {
          name: '掌握状态',
          type: 'pie',
          radius: '60%',
          center: ['60%', '60%'],
          data: [
            { value: goodCount.value, name: '掌握良好', itemStyle: { color: '#52c41a' } },
            { value: mediumCount.value, name: '需巩固', itemStyle: { color: '#faad14' } },
            { value: poorCount.value, name: '薄弱', itemStyle: { color: '#f5222d' } }
          ],
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          },
          label: {
            show: true,
            formatter: '{b}\n{c}个',
            fontSize: 12,
            overflow: 'break'
          },
          labelLine: {
            show: true,
            length: 10,
            length2: 20
          }
        }
      ]
    }
    
    pieChartInstance.setOption(pieOption)
  }
  
  // 初始化柱状图
  const barDom = document.getElementById('mastery-bar')
  if (barDom) {
    if (barChartInstance) {
      barChartInstance.dispose()
    }
    barChartInstance = echarts.init(barDom)
    // 调整图表大小以适应容器
    barChartInstance.resize()
    
    const masteryData = getMasteryData()
    const barOption = {
      title: {
        text: '知识点掌握率对比',
        subtext: '诊断 vs 推荐后',
        left: 'center',
        top: '2%',
        textStyle: {
          fontSize: 16,
          fontWeight: 'bold'
        },
        subtextStyle: {
          fontSize: 12,
          color: '#666'
        }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        },
        formatter: function(params) {
          let result = `<div style="font-weight:bold;margin-bottom:5px;">${params[0].axisValue}</div>`
          params.forEach(param => {
            const masteryPercent = (param.value * 100).toFixed(1)
            let status = '薄弱'
            if (param.value >= 0.7) status = '掌握良好'
            else if (param.value >= 0.4) status = '需巩固'
            result += `<div style="display:flex;align-items:center;margin:3px 0;">
              <span style="display:inline-block;width:10px;height:10px;background:${param.color};margin-right:8px;"></span>
              <span>${param.seriesName}: ${masteryPercent}% (${status})</span>
            </div>`
          })
          return result
        },
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#ddd',
        borderWidth: 1,
        padding: 10,
        boxShadow: '0 2px 12px 0 rgba(0, 0, 0, 0.1)'
      },
      legend: {
        data: ['诊断', '推荐后'],
        bottom: 10,
        textStyle: {
          fontSize: 14,
          fontWeight: '500'
        },
        itemWidth: 16,
        itemHeight: 10,
        itemGap: 20
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '20%',
        top: '25%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: masteryData.xAxisData,
        axisLabel: {
          interval: 0,
          rotate: 45,
          fontSize: 12,
          fontWeight: '500'
        },
        axisLine: {
          lineStyle: {
            color: '#ddd'
          }
        },
        axisTick: {
          alignWithLabel: true
        }
      },
      yAxis: {
        type: 'value',
        name: '掌握率',
        min: 0,
        max: 1,
        interval: 0.2,
        axisLabel: {
          formatter: function(value) {
            return (value * 100).toFixed(0) + '%'
          },
          fontSize: 12
        },
        axisLine: {
          lineStyle: {
            color: '#ddd'
          }
        },
        splitLine: {
          lineStyle: {
            color: '#f0f0f0',
            type: 'dashed'
          }
        }
      },
      series: [
        {
          name: '诊断',
          type: 'bar',
          data: masteryData.preMasteryData.map(value => ({
            value: value,
            itemStyle: {
              color: value >= 0.7 ? '#52c41a' : (value >= 0.4 ? '#faad14' : '#f5222d')
            }
          })),
          barWidth: masteryData.hasRecommendation ? '35%' : '60%',
          animationDuration: 1000,
          animationEasing: 'elasticOut'
        },
        ...(masteryData.hasRecommendation ? [{
          name: '推荐后',
          type: 'bar',
          data: masteryData.postMasteryData.map(value => ({
            value: value,
            itemStyle: {
              color: value >= 0.7 ? '#389e0d' : (value >= 0.4 ? '#fa8c16' : '#ff4d4f')
            }
          })),
          barWidth: '35%',
          animationDuration: 1000,
          animationEasing: 'elasticOut',
          animationDelay: 300
        }] : [])
      ]
    }
    
    barChartInstance.setOption(barOption)
  }
}

// 获取节点颜色
const getNodeColor = (masteryRate) => {
  if (masteryRate > 0.7) {
    return '#52c41a' // 绿色 - 掌握良好
  } else if (masteryRate >= 0.4) {
    return '#faad14' // 黄色 - 需巩固
  } else {
    return '#f5222d' // 红色 - 薄弱
  }
}

// 渲染班级知识图谱
const renderClassChart = () => {
  if (!classKnowledgeData.value) return
  
  // 初始化关系图
  const chartDom = document.getElementById('class-knowledge-chart')
  if (chartDom) {
    if (classChartInstance) {
      classChartInstance.dispose()
    }
    classChartInstance = echarts.init(chartDom)
    classChartInstance.resize()
    
    const filteredClassNodes = (classKnowledgeData.value.nodes || []).filter(node => {
      if (node.name.includes('-')) {
        const nodeLanguage = node.name.split('-')[0]
        return nodeLanguage === selectedLanguage.value
      }
      return true
    })
    
    const nodesWithColor = filteredClassNodes.map(node => {
      let displayName = node.name
      if (displayName.includes('-')) {
        displayName = displayName.split('-')[1]
      }
      
      return {
        id: node.id,
        name: displayName,
        value: node.value,
        category: node.category,
        total: node.total,
        correct: node.correct,
        itemStyle: {
          color: getNodeColor(node.value)
        }
      }
    })
    
    const categories = [...new Set(filteredClassNodes.map(n => n.category))]
    
    const option = {
      title: {
        text: '班级知识点掌握图谱',
        subtext: `总提交次数：${classKnowledgeData.value.submission_count} | 绿色：掌握良好 黄色：需巩固 红色：薄弱`,
        top: 'top',
        left: 'center',
        textStyle: {
          fontSize: 18
        },
        subtextStyle: {
          fontSize: 14
        }
      },
      tooltip: {
        trigger: 'item',
        formatter: function(params) {
          if (params.dataType === 'node') {
            const node = params.data
            const masteryPercent = (node.value * 100).toFixed(1)
            let status = '薄弱'
            if (node.value >= 0.7) status = '掌握良好'
            else if (node.value >= 0.4) status = '需巩固'
            return `<div style="font-weight:bold;margin-bottom:5px;">${node.name}</div>
              <div>掌握率：${masteryPercent}% (${status})</div>
              <div>总提交：${node.total || 0}</div>
              <div>正确：${node.correct || 0}</div>`
          } else if (params.dataType === 'edge') {
            return `<div>知识点关联</div>`
          }
        },
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#ddd',
        borderWidth: 1,
        padding: 10,
        boxShadow: '0 2px 12px 0 rgba(0, 0, 0, 0.1)'
      },
      legend: {
        data: categories,
        bottom: 10,
        textStyle: {
          fontSize: 12
        }
      },
      animationDuration: 1500,
      animationEasingUpdate: 'quinticInOut',
      series: [
        {
          name: '知识点',
          type: 'graph',
          layout: 'force',
          data: nodesWithColor,
          links: (classKnowledgeData.value.links || []).filter(link => {
            const sourceId = typeof link.source === 'object' ? link.source.id : link.source
            const targetId = typeof link.target === 'object' ? link.target.id : link.target
            return nodesWithColor.some(node => node.id === sourceId || node.id === targetId)
          }),
          categories: categories.map(cat => ({ name: cat })),
          roam: true,
          draggable: true,
          force: {
            repulsion: 400,
            gravity: 0.1,
            edgeLength: [50, 200]
          },
          label: {
            show: true,
            position: 'bottom',
            fontSize: 12,
            fontWeight: '500'
          },
          emphasis: {
            focus: 'adjacency',
            lineStyle: {
              width: 4
            }
          },
          lineStyle: {
            color: '#ccc',
            width: 1,
            curveness: 0.2
          }
        }
      ]
    }
    
    classChartInstance.setOption(option)
  }
  
  // 初始化饼图
  const pieDom = document.getElementById('class-mastery-pie')
  if (pieDom) {
    if (classPieChartInstance) {
      classPieChartInstance.dispose()
    }
    classPieChartInstance = echarts.init(pieDom)
    classPieChartInstance.resize()
    
    const stats = classKnowledgeData.value || {}
    const goodCount = (stats.good_count || 0)
    const mediumCount = (stats.medium_count || 0)
    const weakCount = (stats.weak_count || 0)
    
    const pieOption = {
      title: {
        text: '掌握状态分布',
        subtext: `掌握良好：${goodCount} 个 | 需要巩固：${mediumCount} 个 | 薄弱：${weakCount} 个`,
        left: 'center',
        top: 5,
        textStyle: {
          fontSize: 16
        },
        subtextStyle: {
          fontSize: 11,
          color: '#666',
          padding: [5, 0, 25, 0]
        }
      },
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#ddd',
        borderWidth: 1,
        padding: 10,
        boxShadow: '0 2px 12px 0 rgba(0, 0, 0, 0.1)'
      },
      legend: {
        orient: 'horizontal',
        bottom: 10,
        data: ['掌握良好', '需巩固', '薄弱'],
        textStyle: {
          fontSize: 12
        }
      },
      series: [
        {
          name: '掌握状态',
          type: 'pie',
          radius: ['40%', '65%'],
          center: ['50%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: true,
            formatter: '{b}\n{c}个 ({d}%)',
            fontSize: 12
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 14,
              fontWeight: 'bold'
            },
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          },
          labelLine: {
            show: true,
            length: 15,
            length2: 20
          },
          data: [
            { value: goodCount, name: '掌握良好', itemStyle: { color: '#52c41a' } },
            { value: mediumCount, name: '需巩固', itemStyle: { color: '#faad14' } },
            { value: weakCount, name: '薄弱', itemStyle: { color: '#f5222d' } }
          ]
        }
      ]
    }
    
    classPieChartInstance.setOption(pieOption)
  }
  
  // 初始化柱状图
  const barDom = document.getElementById('class-mastery-bar')
  if (barDom) {
    if (classBarChartInstance) {
      classBarChartInstance.dispose()
    }
    classBarChartInstance = echarts.init(barDom)
    classBarChartInstance.resize()
    
    const masteryData = getClassMasteryData()
    const barOption = {
      title: {
        text: '知识点掌握率对比',
        subtext: '诊断 vs 推荐后',
        left: 'center',
        top: '2%',
        textStyle: {
          fontSize: 16,
          fontWeight: 'bold'
        },
        subtextStyle: {
          fontSize: 12,
          color: '#666'
        }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        },
        formatter: function(params) {
          let result = `<div style="font-weight:bold;margin-bottom:5px;">${params[0].axisValue}</div>`
          params.forEach(param => {
            const masteryPercent = (param.value * 100).toFixed(1)
            let status = '薄弱'
            if (param.value >= 0.7) status = '掌握良好'
            else if (param.value >= 0.4) status = '需巩固'
            result += `<div style="display:flex;align-items:center;margin:3px 0;">
              <span style="display:inline-block;width:10px;height:10px;background:${param.color};margin-right:8px;"></span>
              <span>${param.seriesName}: ${masteryPercent}% (${status})</span>
            </div>`
          })
          return result
        },
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#ddd',
        borderWidth: 1,
        padding: 10,
        boxShadow: '0 2px 12px 0 rgba(0, 0, 0, 0.1)'
      },
      legend: {
        data: ['诊断', '推荐后'],
        bottom: 10,
        textStyle: {
          fontSize: 14,
          fontWeight: '500'
        },
        itemWidth: 16,
        itemHeight: 10,
        itemGap: 20
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '20%',
        top: '25%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: masteryData.xAxisData,
        axisLabel: {
          interval: 0,
          rotate: 45,
          fontSize: 12,
          fontWeight: '500'
        },
        axisLine: {
          lineStyle: {
            color: '#ddd'
          }
        },
        axisTick: {
          alignWithLabel: true
        }
      },
      yAxis: {
        type: 'value',
        name: '掌握率',
        min: 0,
        max: 1,
        interval: 0.2,
        axisLabel: {
          formatter: function(value) {
            return (value * 100).toFixed(0) + '%'
          },
          fontSize: 12
        },
        axisLine: {
          lineStyle: {
            color: '#ddd'
          }
        },
        splitLine: {
          lineStyle: {
            color: '#f0f0f0',
            type: 'dashed'
          }
        }
      },
      series: [
        {
          name: '诊断',
          type: 'bar',
          data: masteryData.preMasteryData.map(value => ({
            value: value,
            itemStyle: {
              color: value >= 0.7 ? '#52c41a' : (value >= 0.4 ? '#faad14' : '#f5222d')
            }
          })),
          barWidth: masteryData.hasRecommendation ? '35%' : '60%',
          animationDuration: 1000,
          animationEasing: 'elasticOut'
        },
        ...(masteryData.hasRecommendation ? [{
          name: '推荐后',
          type: 'bar',
          data: masteryData.postMasteryData.map(value => {
            if (value === null) {
              return null
            }
            return {
              value: value,
              itemStyle: {
                color: value >= 0.7 ? '#389e0d' : (value >= 0.4 ? '#fa8c16' : '#ff4d4f')
              }
            }
          }),
          barWidth: '35%',
          animationDuration: 1000,
          animationEasing: 'elasticOut',
          animationDelay: 300
        }] : [])
      ]
    }
    
    classBarChartInstance.setOption(barOption)
  }
}

// 生成AI推荐题目
const generateAIRecommendations = async () => {
  if (!knowledgeData.value || !filteredNodes.value.length) {
    ElMessage.warning('没有可用于推荐的知识点')
    return
  }
  
  // 优先选择掌握率较低的知识点
  const sortedNodes = [...filteredNodes.value].sort((a, b) => a.value - b.value)
  const targetNode = sortedNodes[0] // 选择最薄弱的知识点
  
  // 解析知识点名称（可能包含语言前缀）
  let knowledgeTopic = targetNode.name
  if (knowledgeTopic.includes('-')) {
    knowledgeTopic = knowledgeTopic.split('-')[1]
  }
  
  // 语言映射
  const languageMap = {
    'Python': 'python',
    'C': 'c',
    'C++': 'cpp',
    'Java': 'java',
    'Go': 'go'
  }
  
  try {
    aiGenerating.value = true
    
    const response = await fetch('http://localhost:5002/api/ai-recommend/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        student_id: currentStudentId.value,
        knowledge_topic: knowledgeTopic,
        language: languageMap[selectedLanguage.value] || 'python',
        count: 3
      })
    })
    
    const data = await response.json()
    
    if (data.success) {
      ElMessage.success(data.message)
    } else {
      ElMessage.error(data.error || '生成推荐题目失败')
    }
  } catch (error) {
    console.error('生成推荐失败:', error)
    ElMessage.error('生成推荐题目失败，请稍后重试')
  } finally {
    aiGenerating.value = false
  }
}

// 为指定知识点生成AI推荐题目
const generateAIRecommendationsForTopic = async (node) => {
  if (!currentStudentId.value) {
    ElMessage.warning('请先选择学生')
    return
  }
  
  // 立即设置loading状态，防止重复点击
  if (aiGenerating.value[node.id]) {
    return
  }
  aiGenerating.value[node.id] = true
  
  // 使用完整的知识点名称
  let knowledgeTopic = node.name
  
  // 语言映射
  const languageMap = {
    'Python': 'python',
    'C': 'c',
    'C++': 'cpp',
    'Java': 'java',
    'Go': 'go'
  }
  
  try {
    
    const response = await fetch('http://localhost:5002/api/ai-recommend/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        student_id: currentStudentId.value,
        knowledge_topic: knowledgeTopic,
        language: languageMap[selectedLanguage.value] || 'python',
        count: 3
      })
    })
    
    const data = await response.json()
    
    if (data.success) {
      ElMessage.success(data.message)
      // 刷新推荐作业列表（不显示错误提示，避免覆盖成功消息）
      try {
        await loadAIHomeworkList()
      } catch (e) {
        console.error('刷新推荐作业列表失败:', e)
      }
      // 刷新知识图谱（不显示错误提示，避免覆盖成功消息）
      if (currentStudentId.value) {
        try {
          await loadKnowledgeMap()
        } catch (e) {
          console.error('刷新知识图谱失败:', e)
        }
      }
    } else {
      ElMessage.error(data.error || '生成推荐题目失败')
    }
  } catch (error) {
    console.error('生成推荐失败:', error)
    ElMessage.error('生成推荐题目失败，请稍后重试')
  } finally {
    aiGenerating.value[node.id] = false
  }
}

// 为班级指定知识点生成AI推荐题目
const generateAIRecommendationsForClassTopic = async (node) => {
  if (!currentClassName.value) {
    ElMessage.warning('请先选择班级')
    return
  }
  
  let knowledgeTopic = node.name
  
  const languageMap = {
    'Python': 'python',
    'C': 'c',
    'C++': 'cpp',
    'Java': 'java',
    'Go': 'go'
  }
  
  try {
    classAiGenerating.value[node.id] = true
    
    const response = await fetch('http://localhost:5002/api/ai-recommend/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        class_name: currentClassName.value,
        knowledge_topic: knowledgeTopic,
        language: languageMap[selectedLanguage.value] || 'python',
        count: 3
      })
    })
    
    const data = await response.json()
    
    if (data.success) {
      ElMessage.success(data.message)
      // 重新加载班级知识图谱以显示推荐效果
      await loadClassKnowledgeMap()
    } else {
      ElMessage.error(data.error || '生成推荐题目失败')
    }
  } catch (error) {
    console.error('生成推荐失败:', error)
    ElMessage.error('生成推荐题目失败，请稍后重试')
  } finally {
    classAiGenerating.value[node.id] = false
  }
}

const handleChangePassword = async () => {
  if (!changePasswordFormRef.value) return

  try {
    await changePasswordFormRef.value.validate()
    changingPassword.value = true

    const response = await api.updateUserInfo(currentStudent.value.user_id, {
      password: changePasswordForm.value.newPassword
    })

    if (response.success) {
      ElMessage.success('密码修改成功')
      showChangePasswordDialog.value = false
      // 重置表单
      changePasswordForm.value = {
        username: '',
        newPassword: '',
        confirmPassword: ''
      }
    } else {
      ElMessage.error(response.error || '密码修改失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('修改密码失败:', error)
      const errorMessage = error.response?.data?.error || error.message || '修改密码失败，请检查网络连接'
      ElMessage.error(errorMessage)
    }
  } finally {
    changingPassword.value = false
  }
}

// 作业题目分数相关函数
const handleProblemNumbersChange = async () => {
  // 当题目编号改变时，可以自动清空分数，让用户重新设置
  homeworkForm.value.problem_scores = ''
  
  // 获取题目编号列表
  const problemNumbers = homeworkForm.value.problem_numbers
  if (!problemNumbers) {
    homeworkProblemDetails.value = []
    return
  }
  
  const numbers = problemNumbers.split(',').map(num => num.trim()).filter(num => num)
  
  if (numbers.length === 0) {
    homeworkProblemDetails.value = []
    return
  }
  
  try {
    // 获取所有题目列表
    const response = await api.getProblems(1, 1000)
    if (response.success && response.problems) {
      const allProblems = response.problems
      const details = []
      
      for (const num of numbers) {
        const problem = allProblems.find(p => p.problem_number === parseInt(num))
        if (problem) {
          details.push({
            problem_number: problem.problem_number,
            title: problem.title,
            difficulty: problem.difficulty || '入门',
            category: problem.category || ''
          })
        }
      }
      
      homeworkProblemDetails.value = details
    }
  } catch (error) {
    console.error('获取题目详情失败:', error)
    homeworkProblemDetails.value = []
  }
}

const autoAssignScores = () => {
  const problemNumbers = homeworkForm.value.problem_numbers
  if (!problemNumbers) {
    ElMessage.warning('请先输入题目编号')
    return
  }

  const numbers = problemNumbers.split(',').map(num => num.trim()).filter(num => num)
  const count = numbers.length

  if (count === 0) {
    ElMessage.warning('请输入有效的题目编号')
    return
  }

  // 计算平均分数，确保总和为100
  const avgScore = Math.floor(100 / count)
  const scores = Array(count).fill(avgScore)

  // 处理余数，将余数分配给第一个题目
  const remainder = 100 - (avgScore * count)
  if (remainder > 0 && scores.length > 0) {
    scores[0] += remainder
  }

  homeworkForm.value.problem_scores = scores.join(',')
  ElMessage.success('分数已自动分配')
}

// 备份数据库相关函数
const backupDatabase = async () => {
  try {
    backingUp.value = true
    const response = await api.backupDatabase()

    // 生成文件名：learning_analysis_{时间戳}.db
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    const filename = `learning_analysis_${timestamp}.db`

    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    ElMessage.success('数据库备份成功')
    loadBackupHistory()
  } catch (error) {
    console.error('备份数据库失败:', error)
    const errorMessage = error.response?.data?.error || error.message || '备份数据库失败，请检查网络连接'
    ElMessage.error(errorMessage)
  } finally {
    backingUp.value = false
  }
}

const loadBackupHistory = async () => {
  try {
    const response = await api.getBackupHistory()
    if (response.success) {
      backupHistory.value = response.backups || []
    }
  } catch (error) {
    console.error('获取备份历史失败:', error)
  }
}

const downloadBackup = (backup) => {
  // 这里可以实现下载历史备份的功能
  ElMessage.info('下载功能开发中')
}

// 导出题目
const exportProblems = async () => {
  try {
    const response = await api.exportProblems()
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `problems_${new Date().toISOString().slice(0, 10)}.xlsx`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success('题目导出成功')
  } catch (error) {
    console.error('导出题目失败:', error)
    ElMessage.error('导出题目失败')
  }
}

// 导入题目
const handleProblemImport = async () => {
  if (!importProblemFile.value) {
    ElMessage.warning('请先选择要导入的Excel文件')
    return
  }
  
  try {
    importingProblems.value = true
    
    const formData = new FormData()
    formData.append('file', importProblemFile.value)
    
    const response = await api.importProblems(formData)
    
    if (response.success) {
      ElMessage.success(`成功导入 ${response.imported} 道题目`)
      loadProblems() // 重新加载题目列表
      showImportProblemDialog.value = false
      importProblemFile.value = null
    } else {
      ElMessage.error(response.error || '导入题目失败')
    }
  } catch (error) {
    console.error('导入题目失败:', error)
    ElMessage.error('导入题目失败，请检查文件格式')
  } finally {
    importingProblems.value = false
  }
}

// 作业与测验相关函数
const loadHomeworks = async () => {
  try {
    // 从API获取作业列表
    const response = await api.getHomeworks()
    if (response.success) {
      // 格式化时间
      homeworks.value = response.homeworks.map(homework => {
        const formatTime = (dateString) => {
          if (!dateString) return ''
          const date = new Date(dateString)
          return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
          })
        }
        return {
          ...homework,
          start_time: formatTime(homework.start_time),
          end_time: formatTime(homework.end_time)
        }
      })
    } else {
      ElMessage.error('获取作业列表失败')
    }
  } catch (error) {
    console.error('获取作业列表失败:', error)
  }
}

const loadTodaySubmissions = async () => {
  try {
    const response = await api.getTodaySubmissions()
    if (response.success) {
      todaySubmissions.value = response.count
    } else {
      console.error('获取今日提交数失败:', response.error)
    }
  } catch (error) {
    console.error('获取今日提交数失败:', error)
  }
}

const handleAddHomework = async () => {
  if (!homeworkForm.value.title) {
    ElMessage.warning('请填写作业标题')
    return
  }

  try {
    addingHomework.value = true

    // 调用API添加作业
    const response = await api.addHomework(homeworkForm.value)

    if (response.success) {
      ElMessage.success('作业添加成功')
      showAddHomeworkDialog.value = false
      // 重置表单
      homeworkForm.value = {
        title: '',
        type: 'homework',
        language: '',
        class_name: [],
        problem_numbers: '',
        problem_scores: '',
        start_time: '',
        end_time: ''
      }
      // 重新加载作业列表
      loadHomeworks()
    } else {
      ElMessage.error(response.error || '添加作业失败')
    }
  } catch (error) {
    console.error('添加作业失败:', error)
    const errorMessage = error.response?.data?.error || error.message || '添加作业失败，请检查网络连接'
    ElMessage.error(errorMessage)
  } finally {
    addingHomework.value = false
  }
}

const editHomework = (homework) => {
  // 将逗号分隔的班级字符串转换为数组
  const classNames = homework.class_name ? homework.class_name.split(',').map(c => c.trim()) : []
  homeworkForm.value = {
    title: homework.title,
    type: homework.type,
    language: homework.language || '',
    class_name: classNames,
    problem_numbers: homework.problem_numbers,
    problem_scores: homework.problem_scores || '',
    start_time: homework.start_time,
    end_time: homework.end_time
  }
  currentHomeworkId.value = homework.id
  editingHomework.value = true
  showAddHomeworkDialog.value = true
}

// 查看作业成绩
const viewHomeworkScores = async (homework) => {
  currentHomework.value = homework
  showHomeworkScoresDialog.value = true
  
  // 解析题目编号
  const problemNumbers = homework.problem_numbers ? homework.problem_numbers.split(',').map(n => n.trim()) : []
  homeworkProblemColumns.value = problemNumbers
  
  try {
    // 调用API获取成绩数据
    const response = await api.getHomeworkScores(homework.id)
    if (response.success) {
      homeworkScores.value = response.scores || []
    } else {
      ElMessage.error(response.error || '获取成绩数据失败')
      homeworkScores.value = []
    }
  } catch (error) {
    console.error('获取作业成绩失败:', error)
    ElMessage.error('获取作业成绩失败')
    homeworkScores.value = []
  }
}

// 获取分数颜色
const getScoreColor = (score) => {
  if (score === undefined || score === null) return '#909399'
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
}

// 导出作业成绩到Excel
const exportHomeworkScores = () => {
  if (homeworkScores.value.length === 0) {
    ElMessage.warning('没有可导出的成绩数据')
    return
  }
  
  // 构建CSV数据
  const problemNumbers = currentHomework.value?.problem_numbers ? currentHomework.value.problem_numbers.split(',').map(n => n.trim()) : []
  
  // CSV表头
  let csvContent = '\uFEFF' // BOM for UTF-8
  csvContent += '学号,姓名,班级,'
  problemNumbers.forEach((num, index) => {
    csvContent += `第${index + 1}题(题号${num}),`
  })
  csvContent += '总分\n'
  
  // CSV数据行
  homeworkScores.value.forEach(student => {
    csvContent += `${student.student_id},${student.student_name},${student.class_name},`
    student.scores.forEach(score => {
      csvContent += `${score !== undefined ? score : ''},`
    })
    csvContent += `${student.total_score}\n`
  })
  
  // 创建下载链接
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `作业成绩_${currentHomework.value?.title || '导出'}_${new Date().toLocaleDateString()}.csv`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  ElMessage.success('成绩导出成功')
}

const handleEditHomework = async () => {
  if (!homeworkForm.value.title) {
    ElMessage.warning('请填写作业标题')
    return
  }

  try {
    addingHomework.value = true

    // 调用API更新作业
    const response = await api.updateHomework(currentHomeworkId.value, homeworkForm.value)

    if (response.success) {
      ElMessage.success('作业更新成功')
      showAddHomeworkDialog.value = false
      editingHomework.value = false
      // 重置表单
      homeworkForm.value = {
        title: '',
        type: 'homework',
        language: '',
        class_name: [],
        problem_numbers: '',
        problem_scores: '',
        start_time: '',
        end_time: ''
      }
      // 重新加载作业列表
      loadHomeworks()
    } else {
      ElMessage.error(response.error || '更新作业失败')
    }
  } catch (error) {
    console.error('更新作业失败:', error)
    const errorMessage = error.response?.data?.error || error.message || '更新作业失败，请检查网络连接'
    ElMessage.error(errorMessage)
  } finally {
    addingHomework.value = false
  }
}

const deleteHomework = async (homework) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除作业 ${homework.id}. ${homework.title} 吗？`,
      '删除作业',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // 调用API删除作业
    const response = await api.deleteHomework(homework.id)

    if (response.success) {
      ElMessage.success('作业删除成功')
      // 重新加载作业列表
      loadHomeworks()
    } else {
      ElMessage.error(response.error || '删除作业失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除作业失败:', error)
      const errorMessage = error.response?.data?.error || error.message || '删除作业失败，请检查网络连接'
      ElMessage.error(errorMessage)
    }
  }
}

// 复制作业
const copyHomework = async (homework) => {
  try {
    // 转换日期格式
    const formatTime = (timeStr) => {
      if (!timeStr) return ''
      // 处理 "2026/04/20 16:00" 格式
      if (timeStr.includes('/')) {
        const parts = timeStr.split(' ')
        const dateParts = parts[0].split('/')
        const timeParts = parts[1] ? parts[1].split(':') : ['00', '00']
        return `${dateParts[0]}-${dateParts[1].padStart(2, '0')}-${dateParts[2].padStart(2, '0')}T${timeParts[0].padStart(2, '0')}:${timeParts[1].padStart(2, '0')}:00`
      }
      return timeStr
    }

    // 创建副本数据，标题添加"副本"后缀
    const copyData = {
      title: homework.title + ' (副本)',
      type: homework.type,
      language: homework.language,
      class_name: homework.class_name ? homework.class_name.split(',').map(c => c.trim()) : [],
      problem_numbers: homework.problem_numbers,
      problem_scores: homework.problem_scores,
      start_time: formatTime(homework.start_time),
      end_time: formatTime(homework.end_time)
    }

    // 调用API添加作业副本
    const response = await api.addHomework(copyData)

    if (response.success) {
      ElMessage.success('作业复制成功')
      // 重新加载作业列表
      loadHomeworks()
    } else {
      ElMessage.error(response.error || '复制作业失败')
    }
  } catch (error) {
    console.error('复制作业失败:', error)
    const errorMessage = error.response?.data?.error || error.message || '复制作业失败，请检查网络连接'
    ElMessage.error(errorMessage)
  }
}

// AI推荐管理相关函数
const loadAIRecommendations = async () => {
  try {
    aiLoading.value = true
    const response = await fetch('http://localhost:5002/api/ai-recommend/list')
    const data = await response.json()
    
    if (data.success) {
      aiRecommendations.value = data.recommendations
    } else {
      ElMessage.error(data.error || '加载推荐题目失败')
    }
  } catch (error) {
    console.error('加载推荐题目失败:', error)
    ElMessage.error('加载推荐题目失败，请稍后重试')
  } finally {
    aiLoading.value = false
  }
}

const loadAIHomeworkList = async (page = 1, perPage = 15) => {
  try {
    aiHomeworkLoading.value = true
    const response = await fetch(`http://localhost:5002/api/ai-recommend/homework/list?page=${page}&per_page=${perPage}`)
    const data = await response.json()
    
    if (data.success) {
      // 直接使用后端返回的数据，已包含 is_completed 字段
      aiHomeworkList.value = data.homeworks
      originalAiHomeworkList.value = data.homeworks
      // 更新分页信息
      aiHomeworkTotal.value = data.total || 0
      aiHomeworkTotalPages.value = data.total_pages || 1
      aiHomeworkCurrentPage.value = data.page || 1
      aiHomeworkPageSize.value = data.per_page || 15
    } else {
      ElMessage.error(data.error || '加载推荐作业失败')
    }
  } catch (error) {
    console.error('加载推荐作业失败:', error)
    ElMessage.error('加载推荐作业失败，请稍后重试')
  } finally {
    aiHomeworkLoading.value = false
  }
}

// AI推荐作业分页处理
const handleAIHomeworkSizeChange = (val) => {
  aiHomeworkPageSize.value = val
  aiHomeworkCurrentPage.value = 1
  loadAIHomeworkList(1, val)
}

const handleAIHomeworkCurrentChange = (val) => {
  aiHomeworkCurrentPage.value = val
  loadAIHomeworkList(val, aiHomeworkPageSize.value)
}

const handleAIHomeworkSearch = async () => {
  try {
    aiHomeworkLoading.value = true
    
    // 构建查询参数
    const params = new URLSearchParams({
      page: 1,
      per_page: aiHomeworkPageSize.value,
      search_student_number: searchStudentNumber.value,
      search_student_name: searchStudentName.value,
      search_class_name: searchRecommendClass.value
    })
    
    const response = await fetch(`http://localhost:5002/api/ai-recommend/homework/list?${params}`)
    const data = await response.json()
    
    if (data.success) {
      aiHomeworkList.value = data.homeworks
      aiHomeworkTotal.value = data.total || 0
      aiHomeworkTotalPages.value = data.total_pages || 1
      aiHomeworkCurrentPage.value = 1
    } else {
      ElMessage.error(data.error || '搜索推荐作业失败')
    }
  } catch (error) {
    console.error('搜索推荐作业失败:', error)
    ElMessage.error('搜索推荐作业失败，请稍后重试')
  } finally {
    aiHomeworkLoading.value = false
  }
}

const viewAIHomework = async (homework) => {
  try {
    // 调用优化后的API，一次性获取所有数据
    const response = await fetch(`http://localhost:5002/api/ai-recommend/homework/${homework.id}/detail`)
    const data = await response.json()
    
    if (data.success) {
      const hw = data.homework
      
      // 生成题目列表HTML
      let problemsHtml = ''
      if (hw.problems && hw.problems.length > 0) {
        hw.problems.forEach((problem) => {
          let status = '<span style="color: #999;">未提交</span>'
          if (problem.is_correct === true) {
            status = '<span style="color: #52c41a;">✅ 正确</span>'
          } else if (problem.is_correct === false) {
            status = '<span style="color: #f5222d;">❌ 错误</span>'
          } else if (problem.submission_time) {
            status = '<span style="color: #1890ff;">⚠️ 待分析</span>'
          }
          
          problemsHtml += `
            <div style="margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #eee;">
              <h5 style="margin-bottom: 8px;">${problem.problem_number}. ${problem.title}</h5>
              <div style="margin-bottom: 5px;"><strong>状态:</strong> ${status}</div>
              ${problem.submission_time ? `<div style="margin-bottom: 5px;"><strong>提交时间:</strong> ${problem.submission_time}</div>` : ''}
            </div>
          `
        })
      }
      
      ElMessageBox.alert(
        `<div style="text-align: left;">
          <h4>作业信息</h4>
          <p><strong>学生:</strong> ${hw.student_name} (${hw.student_number})</p>
          <p><strong>班级:</strong> ${hw.class_name}</p>
          <p><strong>生成时间:</strong> ${hw.generated_at}</p>
          <p><strong>作业描述:</strong> ${hw.description || '无'}</p>
          <p><strong>题目数量:</strong> ${hw.problem_count || 0} 道</p>
          
          <h4 style="margin-top: 20px;">题目提交情况</h4>
          ${problemsHtml || '<p>暂无题目信息</p>'}
        </div>`,
        hw.title,
        {
          dangerouslyUseHTMLString: true,
          customClass: 'problem-detail-dialog',
          width: '800px'
        }
      )
    } else {
      ElMessage.error(data.error || '获取推荐作业详情失败')
    }
  } catch (error) {
    console.error('查看作业详情失败:', error)
    ElMessage.error('查看作业详情失败')
  }
}

const editAIHomework = (homework) => {
  // 这里可以实现编辑推荐作业的功能
  ElMessage.info('编辑功能开发中')
}

// 修改题目号相关的响应式变量
const editProblemNumberVisible = ref(false)
const currentEditingHomework = ref(null)
const editProblemNumbers = ref('')
const editProblemDetails = ref([])
const editGeneratedAt = ref('')

const editAIHomeworkProblemNumber = (homework) => {
  currentEditingHomework.value = homework
  editProblemNumbers.value = homework.problem_number || ''
  editGeneratedAt.value = homework.generated_at || ''
  editProblemDetails.value = []
  editProblemNumberVisible.value = true
  // 初始化时获取已有题目的信息
  fetchProblemDetails()
}

const deleteAIHomework = async (homework) => {
  try {
    await ElMessageBox.confirm(
      '此操作将删除该推荐记录（已生成的题目不会删除），学生端的推荐列表也会同步删除，是否继续?',
      '提示',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 使用POST方法调用删除API，避免CORS问题
    const response = await fetch(`http://localhost:5002/api/ai-recommend/homework/${homework.id}/delete`, {
      method: 'POST'
    })
    
    const data = await response.json()
    
    if (data.success) {
      ElMessage.success('删除成功')
      // 重新加载推荐列表
      await loadAIHomeworkList()
    } else {
      ElMessage.error(data.error || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const fetchProblemDetails = async () => {
  if (!editProblemNumbers.value.trim()) {
    editProblemDetails.value = []
    return
  }
  
  const numbers = editProblemNumbers.value.split(',').map(num => num.trim()).filter(Boolean)
  editProblemDetails.value = []
  
  for (const num of numbers) {
    if (!isNaN(num)) {
      try {
        const response = await fetch(`http://localhost:5002/api/problems/detail?number=${num}`)
        const data = await response.json()
        if (data.success && data.problem) {
          editProblemDetails.value.push({
            number: num,
            title: data.problem.title,
            difficulty: data.problem.difficulty || '入门'
          })
        } else {
          editProblemDetails.value.push({
            number: num,
            title: '题目不存在',
            difficulty: '-',
            notFound: true
          })
        }
      } catch (error) {
        editProblemDetails.value.push({
          number: num,
          title: '查询失败',
          difficulty: '-',
          notFound: true
        })
      }
    }
  }
}

const saveEditedProblemNumbers = async () => {
  if (!currentEditingHomework.value) return
  
  try {
    const postData = {
      problem_number: editProblemNumbers.value.trim(),
      generated_at: editGeneratedAt.value.trim()
    }
    console.log('发送的数据:', postData)
    
    const response = await fetch(`http://localhost:5002/api/ai-recommend/homework/${currentEditingHomework.value.id}/update-problem-number`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(postData)
    })
    
    const data = await response.json()
    if (data.success) {
      ElMessage.success('修改成功')
      editProblemNumberVisible.value = false
      loadAIHomeworkList()
    } else {
      ElMessage.error(data.error || '修改失败')
    }
  } catch (error) {
    console.error('修改题目号失败:', error)
    ElMessage.error('修改题目号失败')
  }
}

// 发送推荐作业到学生端
const sendToStudent = async (homework) => {
  try {
    const loading = ElMessage({ loading: '正在发送到学生端...', duration: 0 })
    
    // 调用API发送推荐作业到学生端
    const response = await fetch(`http://localhost:5002/api/ai-recommend/homework/${homework.id}/send`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        student_id: homework.student_id
      })
    })
    
    const data = await response.json()
    
    loading.close()
    
    if (data.success) {
      ElMessage.success('已成功发送到学生端')
    } else {
      ElMessage.error(data.error || '发送失败')
    }
  } catch (error) {
    console.error('发送推荐作业失败:', error)
    ElMessage.error('发送失败，请稍后重试')
  }
}

const viewAIProblem = (problem) => {
  ElMessageBox.alert(
    `<div style="text-align: left;">
        <h4>题目描述</h4>
        <p>${problem.description || '无'}</p>
        <h4>输入描述</h4>
        <p>${problem.input_description || '无'}</p>
        <h4>输出描述</h4>
        <p>${problem.output_description || '无'}</p>
        <h4>样例输入</h4>
        <pre style="background: #f5f7fa; padding: 10px; border-radius: 4px;">${problem.sample_input || '无'}</pre>
        <h4>样例输出</h4>
        <pre style="background: #f5f7fa; padding: 10px; border-radius: 4px;">${problem.sample_output || '无'}</pre>
    </div>`,
    problem.title,
    {
      dangerouslyUseHTMLString: true,
      customClass: 'problem-detail-dialog',
      width: '600px'
    }
  )
}

const deleteAIProblem = async (problem) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除推荐题目《${problem.title}》吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await fetch(`/api/ai-recommend/${problem.id}/delete`, {
      method: 'POST'
    })
    
    const data = await response.json()
    
    if (data.success) {
      ElMessage.success('删除成功')
      loadAIRecommendations()
    } else {
      ElMessage.error(data.error || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除推荐题目失败:', error)
      ElMessage.error('删除推荐题目失败，请稍后重试')
    }
  }
}

const editAIProblem = (problem) => {
  // 这里可以打开编辑对话框
  ElMessage.info('编辑功能开发中')
  // 后续可以添加编辑逻辑
}

// 分页处理函数
const handleSizeChange = (size) => {
  pageSize.value = size
  loadProblemsWithFilters(1)
}

const handleCurrentChange = (current) => {
  loadProblemsWithFilters(current)
}

// 监听对话框打开，清空编辑器
watch([showAddProblemDialog, editingProblem], ([newAddVal, newEditVal]) => {
  if (newAddVal || newEditVal) {
    nextTick(() => {
      if (editorContainer.value) {
        if (newEditVal) {
          // 编辑模式，保持现有内容
          editorContainer.value.innerHTML = problemForm.value.description || ''
        } else {
          // 添加模式，清空编辑器
          editorContainer.value.innerHTML = ''
        }
      }
    })
  }
})

onMounted(() => {
  // 检查是否已登录
  const isAuthenticated = localStorage.getItem('isAuthenticated')
  const userRole = localStorage.getItem('userRole')

  if (!isAuthenticated || isAuthenticated !== 'true') {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }

  if (userRole !== 'teacher') {
    ElMessage.warning('您没有权限访问教师端')
    router.push('/dashboard')
    return
  }

  loadStudents()
  loadProblems(currentPage.value)
  loadCategories()
  loadHomeworks()
  loadTodaySubmissions()
})

const getDifficultyType = (difficulty) => {
  if (!difficulty) return 'success'
  switch (difficulty) {
    case '入门': return 'success'
    case '基础': return 'warning'
    case '提高': return 'danger'
    default: return 'info'
  }
}
</script>

<style scoped>
.teacher-dashboard {
  width: 100%;
  height: 100vh;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.aside {
  background: linear-gradient(180deg, #303133, #1f1f23);
  color: #fff;
  overflow: hidden;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
}

.aside:hover {
  box-shadow: 2px 0 16px rgba(0, 0, 0, 0.2);
}

.logo {
  padding: 24px;
  text-align: center;
  border-bottom: 1px solid #404040;
  background: rgba(255, 255, 255, 0.05);
}

.logo h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #67c23a;
  letter-spacing: 1px;
}

.menu {
  height: calc(100vh - 96px);
  border-right: none;
  background: transparent;
}

.menu .el-menu-item {
  color: #c0c4cc;
  height: 60px;
  line-height: 60px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  border-radius: 0 20px 20px 0;
  margin: 8px 0;
  padding: 0 24px;
}

.menu .el-menu-item:hover {
  background: linear-gradient(90deg, rgba(64, 158, 255, 0.2), rgba(64, 158, 255, 0.1));
  color: #409eff;
}

.menu .el-menu-item.is-active {
  background: linear-gradient(90deg, rgba(64, 158, 255, 0.3), rgba(64, 158, 255, 0.15));
  color: #409eff;
  font-weight: 600;
}

.menu .el-menu-item .el-icon {
  margin-right: 12px;
  font-size: 18px;
}

.main {
  background-color: #f5f7fa;
  padding: 24px;
  overflow-y: auto;
}

.stat-card {
  height: 120px;
  position: relative;
  overflow: hidden;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.stat-content {
  position: relative;
  z-index: 2;
  padding: 16px;
}

.stat-number {
  font-size: 32px;
  font-weight: 600;
  color: #409eff;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #606266;
  margin-top: 8px;
  font-weight: 500;
}

.stat-icon {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 60px;
  color: rgba(64, 158, 255, 0.1);
  z-index: 1;
}

.table-card {
  margin-top: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.problem-numbers-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.problem-number-link {
  color: #409eff;
  text-decoration: underline;
  cursor: pointer;
  font-size: 14px;
}

.problem-number-link:hover {
  color: #667eea;
  text-decoration: none;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 16px;
  padding: 16px 20px;
}

.header-actions {
  display: flex;
  align-items: center;
}

.card-header .el-button {
  font-weight: 500;
  transition: all 0.3s ease;
}

.rich-editor-container {
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.rich-editor-toolbar {
  padding: 12px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
}

.rich-editor-content {
  min-height: 180px;
  max-height: 350px;
  padding: 16px;
  overflow-y: auto;
  background-color: #fff;
  font-size: 14px;
  line-height: 1.6;
}

.rich-editor-content:focus {
  outline: none;
}

.rich-editor-content[contenteditable]:empty:before {
  content: attr(placeholder);
  color: #9ca3af;
  pointer-events: none;
}

.rich-editor-content img {
  max-width: 100%;
  margin: 12px 0;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 表格样式 */
.el-table {
  border-radius: 8px;
  overflow: hidden;
}

.el-table th {
  background-color: #fafafa;
  font-weight: 600;
  color: #606266;
  padding: 12px 0;
}

.el-table td {
  padding: 12px 0;
  font-size: 14px;
}

/* 按钮样式 */
.el-button {
  border-radius: 4px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.el-button:hover {
  transform: translateY(-1px);
}

/* 对话框样式 */
.el-dialog {
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.el-dialog__header {
  background-color: #fafafa;
  border-bottom: 1px solid #ebeef5;
  padding: 16px 20px;
}

.el-dialog__title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.el-dialog__body {
  padding: 24px;
}

.el-dialog__footer {
  padding: 16px 20px;
  border-top: 1px solid #ebeef5;
  background-color: #fafafa;
}

/* 表单样式 */
.el-form-item {
  margin-bottom: 16px;
}

.el-form-item__label {
  font-weight: 500;
  color: #606266;
}

.el-input,
.el-select,
.el-date-picker {
  border-radius: 4px;
  transition: all 0.3s ease;
}

.el-input:focus,
.el-select:focus,
.el-date-picker:focus {
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

/* 题目详情样式 */
.problem-details {
  max-height: 200px;
  overflow-y: auto;
  padding: 10px;
  background-color: #fafafa;
  border-radius: 4px;
}

.problem-detail-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px dashed #ebeef5;
}

.problem-detail-item:last-child {
  border-bottom: none;
}

.problem-number {
  font-weight: 600;
  color: #409eff;
  margin-right: 8px;
}

.problem-title {
  flex: 1;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.problem-category {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  background-color: #e8f4fd;
  color: #409eff;
  margin-right: 8px;
}

.problem-difficulty {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.problem-difficulty.入门 {
  background-color: #f0f9eb;
  color: #67c23a;
}

.problem-difficulty.基础 {
  background-color: #fef9e7;
  color: #e6a23c;
}

.problem-difficulty.提高 {
  background-color: #fef0f0;
  color: #f56c6c;
}
</style>