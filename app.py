"""
AI学情分析系统 - Flask后端应用
用于高职Python编程学情诊断系统
"""

import os
import datetime
import io
import re
import json
from flask import Flask, request, jsonify, session, send_file, send_from_directory, send_from_directory
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import sqlalchemy as sa

# 导入处理Excel的库
import pandas as pd

# 去除HTML标签的函数
def remove_html_tags(text):
    if not text:
        return text
    # 移除HTML标签
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 调试：打印环境变量加载情况
print("DEBUG: Loaded environment variables:")
print(f"DEBUG: DEEPSEEK_API_KEY length: {len(os.environ.get('DEEPSEEK_API_KEY', ''))}")
print(f"DEBUG: DEEPSEEK_API_KEY starts with: {os.environ.get('DEEPSEEK_API_KEY', '')[:5]}...")

app = Flask(__name__, static_folder=None)
app.secret_key = 'your-secret-key-change-in-production'
CORS(app, supports_credentials=True)

# 生产环境配置
app.config['ENV'] = 'production'
app.config['DEBUG'] = False

# 数据库配置
DATABASE_URL = 'sqlite:///learning_analysis.db'
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# ==================== 数据模型 ====================

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    role = Column(String(20), default='student')  # student
    email = Column(String(100))
    created_at = Column(DateTime, default=datetime.datetime.now)

    student = relationship("Student", back_populates="user", uselist=False)

class Teacher(Base):
    __tablename__ = 'teachers'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    email = Column(String(100))
    created_at = Column(DateTime, default=datetime.datetime.now)

class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    student_id = Column(String(50), unique=True)  # 学号
    name = Column(String(100))  # 姓名
    class_name = Column(String(100))  # 班级

    user = relationship("User", back_populates="student")
    submissions = relationship("HomeworkSubmission", back_populates="student")

class HomeworkSubmission(Base):
    __tablename__ = 'homework_submissions'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'))
    teacher_id = Column(Integer, ForeignKey('teachers.id'), nullable=True)
    problem_id = Column(Integer, ForeignKey('problems.id'), nullable=True)
    code_content = Column(Text)
    ai_feedback = Column(Text)
    submission_time = Column(DateTime, default=datetime.datetime.now)
    is_homework_submission = Column(Boolean, default=False)

    student = relationship("Student", back_populates="submissions")
    problem = relationship("Problem")
    teacher = relationship("Teacher")

class Problem(Base):
    __tablename__ = 'problems'
    id = Column(Integer, primary_key=True)
    problem_number = Column(Integer)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    input_description = Column(Text)
    output_description = Column(Text)
    sample_input = Column(Text)
    sample_output = Column(Text)
    test_input = Column(Text)  # 测试输入（不显示给学生）
    test_output = Column(Text)  # 测试输出（不显示给学生）
    category = Column(String(100))
    language = Column(String(50))  # programming language
    required_functions = Column(Text, default='[]')  # JSON格式存储必需函数列表
    difficulty = Column(String(20), default='入门')  # 难度等级：入门、基础、提高

# ==================== 代码验证工具函数 ====================

def analyze_python_ast(code, required_funcs):
    """
    AST分析：检查Python代码是否定义了必需的函数
    :param code: Python源代码
    :param required_funcs: 必需函数名列表
    :return: (成功标志, 消息)
    """
    import ast
    
    if not required_funcs or not required_funcs.strip():
        return True, "无必需函数检查"
    
    try:
        # 解析JSON格式的必需函数列表
        try:
            funcs_to_check = json.loads(required_funcs)
        except:
            # 如果不是JSON格式，尝试按逗号分隔
            funcs_to_check = [f.strip() for f in required_funcs.split(',') if f.strip()]
        
        # 解析代码为AST
        tree = ast.parse(code)
        
        # 获取所有定义的函数名
        defined_funcs = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                defined_funcs.append(node.name)
        
        # 检查所有必需函数是否存在
        missing_funcs = []
        for func_name in funcs_to_check:
            if func_name not in defined_funcs:
                missing_funcs.append(func_name)
        
        if missing_funcs:
            return False, f"缺少必需函数: {', '.join(missing_funcs)}"
        
        return True, "AST检查通过"
    except SyntaxError as e:
        return False, f"语法错误: {e}"
    except Exception as e:
        return False, f"AST分析失败: {str(e)}"

def trace_python_function_calls(code, input_data, required_funcs):
    """
    函数调用追踪：检查Python代码运行时是否调用了必需的函数
    :param code: Python源代码
    :param input_data: 输入数据
    :param required_funcs: 必需函数名列表
    :return: (成功标志, 消息, 执行结果)
    """
    if not required_funcs or not required_funcs.strip():
        return True, "无必需函数检查", ""
    
    import sys
    import io
    import ast
    
    try:
        # 解析必需函数列表
        try:
            funcs_to_check = json.loads(required_funcs)
        except:
            funcs_to_check = [f.strip() for f in required_funcs.split(',') if f.strip()]
        
        # 第一步：使用AST分析代码中是否有调用必需函数
        try:
            tree = ast.parse(code)
            called_funcs = set()
            
            for node in ast.walk(tree):
                # 检测函数调用
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        called_funcs.add(node.func.id)
                    # 处理方法调用，如 obj.func()
                    elif isinstance(node.func, ast.Attribute):
                        called_funcs.add(node.func.attr)
            
            # 检查所有必需函数是否被调用
            not_called_funcs = []
            for func_name in funcs_to_check:
                if func_name not in called_funcs:
                    not_called_funcs.append(func_name)
            
            if not_called_funcs:
                return False, f"必需函数未被调用: {', '.join(not_called_funcs)}", ""
        except SyntaxError as e:
            return False, f"语法错误: {e}", ""
        
        # 第二步：执行代码获取输出（同时确保代码能正常运行）
        output = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = output
        
        try:
            if input_data:
                input_lines = input_data.strip().split('\n')
                input_index = [0]
                
                def mock_input(prompt=''):
                    if input_index[0] < len(input_lines):
                        value = input_lines[input_index[0]]
                        input_index[0] += 1
                        return value
                    return ''
                
                exec_globals = {'input': mock_input}
                exec(code, exec_globals)
            else:
                exec(code, {})
            
            execution_result = output.getvalue()
            return True, "函数调用检查通过", execution_result
        except Exception as e:
            return False, f"运行错误: {str(e)}", output.getvalue()
        finally:
            sys.stdout = old_stdout
    except Exception as e:
        return False, f"函数追踪失败: {str(e)}", ""

def execute_python_code_with_input(code, input_data):
    """
    使用指定输入运行Python代码
    :param code: Python源代码
    :param input_data: 输入数据
    :return: 执行结果输出
    """
    import sys
    import io
    
    output = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = output
    
    try:
        if input_data:
            input_lines = input_data.strip().split('\n')
            input_index = [0]
            
            def mock_input(prompt=''):
                if input_index[0] < len(input_lines):
                    line = input_lines[input_index[0]]
                    input_index[0] += 1
                    return line
                return ''
            
            exec(code, {'input': mock_input})
        else:
            exec(code)
        
        return output.getvalue()
    except Exception as e:
        return f"执行错误: {str(e)}"
    finally:
        sys.stdout = old_stdout

class Homework(Base):
    __tablename__ = 'homeworks'
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False)  # homework or quiz
    language = Column(String(50))  # programming language
    class_name = Column(String(500))  # comma-separated class names, empty means all classes
    problem_numbers = Column(String(200))  # comma-separated problem numbers
    problem_scores = Column(String(200))  # comma-separated problem scores
    start_time = Column(DateTime)
    end_time = Column(DateTime)

class KnowledgeNode(Base):
    __tablename__ = 'knowledge_nodes'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    category = Column(String(100))
    description = Column(Text)

class AIRecommendedProblem(Base):
    __tablename__ = 'ai_recommended_problems'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    knowledge_topic = Column(String(100), nullable=False)
    language = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    input_description = Column(Text)
    output_description = Column(Text)
    sample_input = Column(Text)
    sample_output = Column(Text)
    test_input = Column(Text)  # 测试输入（不显示给学生）
    test_output = Column(Text)  # 测试输出（不显示给学生）
    generated_at = Column(DateTime, default=datetime.datetime.now)
    is_active = Column(Integer, default=1)  # 1: active, 0: deleted

    student = relationship("Student")

class AIRecommendedHomework(Base):
    __tablename__ = 'ai_recommended_homeworks'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    knowledge_topics = Column(Text)  # JSON格式存储多个知识点
    problem_count = Column(Integer, default=0)
    generated_at = Column(DateTime, default=datetime.datetime.now)
    is_active = Column(Integer, default=1)  # 1: active, 0: deleted

    student = relationship("Student")

# 创建表
Base.metadata.create_all(engine)

# ==================== DeepSeek 分析器 ====================

from deepseek_service_simple import DeepSeekAnalyzer

# 初始化DeepSeek分析器
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
if not DEEPSEEK_API_KEY:
    print("警告: DeepSeek API密钥未设置，请设置环境变量 DEEPSEEK_API_KEY")
analyzer = DeepSeekAnalyzer(DEEPSEEK_API_KEY)

def get_deepseek_analyzer():
    """获取DeepSeek分析器实例"""
    return analyzer

def execute_c_cpp_code(code, language, input_data, timeout=10):
    """
    执行C/C++代码并返回执行结果
    :param code: C/C++源代码
    :param language: 语言类型 ('c' 或 'cpp')
    :param input_data: 输入数据
    :param timeout: 执行超时时间（秒）
    :return: (成功标志, 执行结果或错误信息)
    """
    import subprocess
    import tempfile
    import os
    import shutil

    temp_dir = tempfile.mkdtemp()
    try:
        if language == 'c':
            source_file = os.path.join(temp_dir, 'main.c')
            compiler = 'gcc'
        else:
            source_file = os.path.join(temp_dir, 'main.cpp')
            compiler = 'g++'

        with open(source_file, 'w', encoding='utf-8') as f:
            f.write(code)

        exe_file = os.path.join(temp_dir, 'program.exe')
        compile_cmd = [compiler, source_file, '-o', exe_file, '-Wall']

        try:
            compile_result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='replace'
            )

            if compile_result.returncode != 0:
                return False, f"编译错误:\n{compile_result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "编译超时"
        except Exception as e:
            return False, f"编译失败: {str(e)}"

        if not os.path.exists(exe_file):
            return False, f"编译失败: exe文件未生成\n{compile_result.stderr}"

        try:
            exec_cmd = [exe_file]

            if input_data:
                input_file = os.path.join(temp_dir, 'input.txt')
                with open(input_file, 'w', encoding='utf-8') as f:
                    f.write(input_data)
                with open(input_file, 'r', encoding='utf-8') as stdin:
                    exec_result = subprocess.run(
                        exec_cmd,
                        stdin=stdin,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        encoding='utf-8',
                        errors='replace'
                    )
            else:
                exec_result = subprocess.run(
                    exec_cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    encoding='utf-8',
                    errors='replace'
                )

            if exec_result.returncode != 0:
                return False, f"运行错误:\n{exec_result.stderr}"

            return True, exec_result.stdout

        except subprocess.TimeoutExpired:
            return False, "运行超时: 代码执行时间超过限制"
        except Exception as e:
            return False, f"运行失败: {str(e)}"

    finally:
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

def execute_java_code(code, input_data, timeout=10):
    """
    执行Java代码并返回执行结果
    :param code: Java源代码
    :param input_data: 输入数据
    :param timeout: 执行超时时间（秒）
    :return: (成功标志, 执行结果或错误信息)
    """
    import subprocess
    import tempfile
    import os
    import shutil

    temp_dir = tempfile.mkdtemp()
    try:
        # 假设代码包含main方法的类
        # 尝试提取类名
        class_name = None
        class_match = re.search(r'\bclass\s+(\w+)\s*\{', code)
        if class_match:
            class_name = class_match.group(1)
        else:
            # 如果没有找到类名，使用默认类名
            class_name = 'Main'

        # 写入Java源代码文件
        source_file = os.path.join(temp_dir, f'{class_name}.java')
        with open(source_file, 'w', encoding='utf-8') as f:
            f.write(code)

        # 编译命令
        compile_cmd = ['javac', source_file]

        # 编译代码
        try:
            compile_result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='replace'
            )

            if compile_result.returncode != 0:
                return False, f"编译错误:\n{compile_result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "编译超时"
        except Exception as e:
            return False, f"编译失败: {str(e)}"

        # 检查class文件是否生成
        class_file = os.path.join(temp_dir, f'{class_name}.class')
        if not os.path.exists(class_file):
            return False, f"编译失败: class文件未生成\n{compile_result.stderr}"

        # 执行编译后的程序
        try:
            # 准备执行命令
            exec_cmd = ['java', '-cp', temp_dir, class_name]

            # 如果有输入数据，写入临时输入文件
            if input_data:
                input_file = os.path.join(temp_dir, 'input.txt')
                with open(input_file, 'w', encoding='utf-8') as f:
                    f.write(input_data)
                # 使用输入重定向
                with open(input_file, 'r', encoding='utf-8') as stdin:
                    exec_result = subprocess.run(
                        exec_cmd,
                        stdin=stdin,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        encoding='utf-8',
                        errors='replace'
                    )
            else:
                exec_result = subprocess.run(
                    exec_cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    encoding='utf-8',
                    errors='replace'
                )

            if exec_result.returncode != 0:
                return False, f"运行错误:\n{exec_result.stderr}"

            return True, exec_result.stdout

        except subprocess.TimeoutExpired:
            return False, "运行超时: 代码执行时间超过限制"
        except Exception as e:
            return False, f"运行失败: {str(e)}"

    finally:
        # 清理临时目录
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

def execute_go_code(code, input_data, timeout=10):
    """
    执行Go代码并返回执行结果
    :param code: Go源代码
    :param input_data: 输入数据
    :param timeout: 执行超时时间（秒）
    :return: (成功标志, 执行结果或错误信息)
    """
    import subprocess
    import tempfile
    import os
    import shutil

    temp_dir = tempfile.mkdtemp()
    try:
        # 写入Go源代码文件
        source_file = os.path.join(temp_dir, 'main.go')
        with open(source_file, 'w', encoding='utf-8') as f:
            f.write(code)

        # 编译命令
        compile_cmd = ['go', 'build', '-o', 'program.exe', source_file]

        # 编译代码
        try:
            # 切换到临时目录执行go build
            compile_result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='replace',
                cwd=temp_dir
            )

            if compile_result.returncode != 0:
                return False, f"编译错误:\n{compile_result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "编译超时"
        except Exception as e:
            return False, f"编译失败: {str(e)}"

        # 检查exe文件是否生成
        exe_file = os.path.join(temp_dir, 'program.exe')
        if not os.path.exists(exe_file):
            return False, f"编译失败: exe文件未生成\n{compile_result.stderr}"

        # 执行编译后的程序
        try:
            # 准备执行命令
            exec_cmd = [exe_file]

            # 如果有输入数据，写入临时输入文件
            if input_data:
                input_file = os.path.join(temp_dir, 'input.txt')
                with open(input_file, 'w', encoding='utf-8') as f:
                    f.write(input_data)
                # 使用输入重定向
                with open(input_file, 'r', encoding='utf-8') as stdin:
                    exec_result = subprocess.run(
                        exec_cmd,
                        stdin=stdin,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        encoding='utf-8',
                        errors='replace'
                    )
            else:
                exec_result = subprocess.run(
                    exec_cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    encoding='utf-8',
                    errors='replace'
                )

            if exec_result.returncode != 0:
                return False, f"运行错误:\n{exec_result.stderr}"

            return True, exec_result.stdout

        except subprocess.TimeoutExpired:
            return False, "运行超时: 代码执行时间超过限制"
        except Exception as e:
            return False, f"运行失败: {str(e)}"

    finally:
        # 清理临时目录
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

# ==================== API 路由 ====================

@app.route('/api/test', methods=['GET'])
def test():
    """测试接口"""
    return jsonify({
        "success": True,
        "message": "API 工作正常",
        "timestamp": datetime.datetime.now().isoformat(),
        "sqlalchemy_version": sa.__version__
    })

@app.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return jsonify({
                "success": False,
                "error": "用户名和密码不能为空"
            }), 400

        session_db = Session()
        try:
            # 先尝试查找学生（使用学号作为用户名）
            student = session_db.query(Student).filter_by(student_id=username).first()
            if student:
                # 学生密码统一为123456
                if password == '123456':
                    # 生成简单token
                    token = f"token_student_{student.id}_{datetime.datetime.now().timestamp()}"
                    return jsonify({
                        "success": True,
                        "message": "登录成功",
                        "token": token,
                        "user": {
                            "id": student.id,
                            "username": student.student_id,
                            "name": student.name,
                            "role": "student",
                            "email": ""
                        }
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": "用户名或密码错误"
                    }), 401

            # 尝试查找用户（学生账号）
            user = session_db.query(User).filter_by(username=username).first()
            if user:
                # 验证用户是否存在以及密码是否正确
                from werkzeug.security import check_password_hash
                if not check_password_hash(user.password, password):
                    return jsonify({
                        "success": False,
                        "error": "用户名或密码错误"
                    }), 401
                
                # 对于学生用户，还需要检查是否在 Student 表中存在
                if user.role == 'student':
                    student = session_db.query(Student).filter_by(user_id=user.id).first()
                    if not student:
                        return jsonify({
                            "success": False,
                            "error": "学生不存在"
                        }), 401

                # 生成简单token（实际应使用JWT）
                token = f"token_student_{user.id}_{datetime.datetime.now().timestamp()}"

                # 构建用户信息
                user_info = {
                    "id": user.id,
                    "username": user.username,
                    "role": user.role,
                    "email": user.email
                }

                # 如果是学生用户，添加姓名信息
                if user.role == 'student' and 'student' in locals() and student:
                    user_info["name"] = student.name

                return jsonify({
                    "success": True,
                    "message": "登录成功",
                    "token": token,
                    "user": user_info
                })

            # 尝试查找教师
            teacher = session_db.query(Teacher).filter_by(username=username).first()
            if teacher:
                # 验证教师密码
                from werkzeug.security import check_password_hash
                if not check_password_hash(teacher.password, password):
                    return jsonify({
                        "success": False,
                        "error": "用户名或密码错误"
                    }), 401

                # 生成简单token（实际应使用JWT）
                token = f"token_teacher_{teacher.id}_{datetime.datetime.now().timestamp()}"

                return jsonify({
                    "success": True,
                    "message": "登录成功",
                    "token": token,
                    "user": {
                        "id": teacher.id,
                        "username": teacher.username,
                        "role": "teacher",
                        "email": teacher.email
                    }
                })

            # 所有都找不到
            return jsonify({
                "success": False,
                "error": "用户不存在"
            }), 401
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"登录失败: {str(e)}"
        }), 500

@app.route('/api/teacher/change-password', methods=['POST'])
def change_teacher_password():
    """教师修改密码"""
    try:
        data = request.json
        teacher_id = data.get('teacher_id')
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')

        if not teacher_id or not old_password or not new_password:
            return jsonify({
                "success": False,
                "error": "请填写完整信息"
            }), 400

        if len(new_password) < 6:
            return jsonify({
                "success": False,
                "error": "新密码长度不能少于6个字符"
            }), 400

        session_db = Session()
        try:
            teacher = session_db.query(Teacher).filter_by(id=teacher_id).first()
            if not teacher:
                return jsonify({
                    "success": False,
                    "error": "教师不存在"
                }), 404

            from werkzeug.security import check_password_hash, generate_password_hash
            if not check_password_hash(teacher.password, old_password):
                return jsonify({
                    "success": False,
                    "error": "原密码错误"
                }), 401

            teacher.password = generate_password_hash(new_password)
            session_db.commit()

            return jsonify({
                "success": True,
                "message": "密码修改成功"
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"修改密码失败: {str(e)}"
        }), 500

@app.route('/api/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        role = data.get('role', 'student')
        email = data.get('email', '')

        student_id = data.get('student_id', '')
        name = data.get('name', '')
        class_name = data.get('class_name', '')

        if not username or not password:
            return jsonify({
                "success": False,
                "error": "用户名和密码不能为空"
            }), 400

        session_db = Session()
        try:
            # 检查用户是否已存在
            existing_user = session_db.query(User).filter_by(username=username).first()
            if existing_user:
                return jsonify({
                    "success": False,
                    "error": "用户名已存在"
                }), 400

            # 密码加密
            from werkzeug.security import generate_password_hash
            hashed_password = generate_password_hash(password)
            
            # 只允许注册学生用户
            if role != 'student':
                return jsonify({
                    "success": False,
                    "error": "只允许注册学生用户"
                }), 400

            # 创建用户
            user = User(
                username=username,
                password=hashed_password,
                role=role,
                email=email
            )
            session_db.add(user)
            session_db.commit()

            # 创建学生记录
            student = Student(
                user_id=user.id,
                student_id=student_id or username,
                name=name or username,
                class_name=class_name,
                email=email
            )
            session_db.add(student)
            session_db.commit()

            return jsonify({
                "success": True,
                "message": "注册成功"
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"注册失败: {str(e)}"
        }), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user_info(user_id):
    """获取用户信息"""
    try:
        session_db = Session()
        try:
            user = session_db.query(User).filter_by(id=user_id).first()
            if not user:
                return jsonify({
                    "success": False,
                    "error": "用户不存在"
                }), 404

            # 构建用户信息
            user_info = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }

            # 如果是学生用户，添加姓名信息
            if user.role == 'student':
                student = session_db.query(Student).filter_by(user_id=user.id).first()
                if student and student.name:
                    user_info["name"] = student.name

            return jsonify({
                "success": True,
                "user": user_info
            })
        finally:
            session_db.close()
    except Exception as e:
        print(f"获取用户信息失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"获取用户信息失败: {str(e)}"
        }), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user_info(user_id):
    """更新用户信息"""
    try:
        data = request.json
        if not data:
            return jsonify({
                "success": False,
                "error": "请求数据不能为空"
            }), 400

        session_db = Session()
        try:
            user = session_db.query(User).filter_by(id=user_id).first()
            if not user:
                return jsonify({
                    "success": False,
                    "error": "用户不存在"
                }), 404

            # 只允许更新邮箱和密码
            if 'email' in data:
                user.email = data['email']

            if 'password' in data and data['password']:
                # 密码加密
                from werkzeug.security import generate_password_hash
                hashed_password = generate_password_hash(data['password'])
                user.password = hashed_password

            session_db.commit()

            return jsonify({
                "success": True,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role
                }
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"更新用户信息失败: {str(e)}"
        }), 500

@app.route('/api/students', methods=['GET'])
def get_all_students():
    """获取所有学生"""
    try:
        session_db = Session()
        try:
            students = session_db.query(Student).all()
            student_list = []
            for s in students:
                student_list.append({
                    "id": s.id,
                    "user_id": s.user_id,
                    "student_id": s.student_id,
                    "name": s.name,
                    "class_name": s.class_name,
                    "username": s.user.username if s.user else "",
                    "email": s.user.email if s.user else ""
                })
            return jsonify({
                "success": True,
                "students": student_list
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取学生列表失败: {str(e)}"
        }), 500

@app.route('/api/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    """删除学生记录"""
    try:
        session_db = Session()
        try:
            # 查找学生记录
            student = session_db.query(Student).filter_by(id=student_id).first()
            if not student:
                return jsonify({
                    "success": False,
                    "error": "学生记录不存在"
                }), 404
            
            # 保存用户ID用于后续删除
            user_id = student.user_id
            
            # 删除学生记录
            session_db.delete(student)
            
            # 删除关联的用户记录
            user = session_db.query(User).filter_by(id=user_id).first()
            if user:
                session_db.delete(user)
            
            session_db.commit()
            return jsonify({
                "success": True,
                "message": "删除成功"
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"删除失败: {str(e)}"
        }), 500

@app.route('/api/students/import', methods=['POST'])
def import_students():
    """导入学生花名册"""
    try:
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "没有上传文件"
            }), 400

        file = request.files['file']
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({
                "success": False,
                "error": "请上传Excel文件"
            }), 400

        import pandas as pd
        from io import BytesIO

        df = pd.read_excel(BytesIO(file.read()))
        session_db = Session()
        try:
            imported_count = 0
            for _, row in df.iterrows():
                student_id = str(row.get('学号', '')).strip()
                name = str(row.get('姓名', '')).strip()
                class_name = str(row.get('班级', '')).strip() if pd.notna(row.get('班级')) else ''
                email = str(row.get('邮箱', '')).strip() if pd.notna(row.get('邮箱')) else ''

                if not student_id:
                    continue

                # 检查学生是否已存在
                existing_student = session_db.query(Student).filter_by(student_id=student_id).first()
                if existing_student:
                    continue

                # 检查用户是否已存在
                existing_user = session_db.query(User).filter_by(username=student_id).first()
                if existing_user:
                    # 用户已存在，只创建学生记录
                    student = Student(
                        user_id=existing_user.id,
                        student_id=student_id,
                        name=name,
                        class_name=class_name
                    )
                    session_db.add(student)
                else:
                    # 创建用户
                    user = User(
                        username=student_id,
                        password='123456',
                        role='student',
                        email=email
                    )
                    session_db.add(user)
                    # 刷新session以获取user.id
                    session_db.flush()

                    # 创建学生记录
                    student = Student(
                        user_id=user.id,
                        student_id=student_id,
                        name=name,
                        class_name=class_name
                    )
                    session_db.add(student)
                imported_count += 1

            session_db.commit()
            return jsonify({
                "success": True,
                "message": f"成功导入 {imported_count} 名学生"
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"导入失败: {str(e)}"
        }), 500

@app.route('/api/problems', methods=['GET'])
def get_problems():
    """获取题目列表（支持分页和搜索）"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 获取搜索参数
        problem_number = request.args.get('problem_number', type=int)
        title = request.args.get('title', '')
        category = request.args.get('category', '')
        difficulty = request.args.get('difficulty', '')
        
        session_db = Session()
        try:
            # 构建查询
            query = session_db.query(Problem)
            
            # 添加搜索条件
            if problem_number:
                query = query.filter(Problem.problem_number == problem_number)
            if title:
                query = query.filter(Problem.title.like(f'%{title}%'))
            if category:
                query = query.filter(Problem.category.like(f'%{category}%'))
            if difficulty:
                query = query.filter(Problem.difficulty == difficulty)
            
            # 计算总数
            total = query.count()
            
            # 计算偏移量
            offset = (page - 1) * per_page
            
            # 查询分页数据
            problems = query.order_by(Problem.problem_number).offset(offset).limit(per_page).all()
            
            problem_list = []
            for p in problems:
                problem_list.append({
                    "id": p.id,
                    "problem_number": p.problem_number,
                    "title": p.title,
                    "category": p.category,
                    "difficulty": p.difficulty,
                    "description": p.description,
                    "input_description": p.input_description,
                    "output_description": p.output_description,
                    "sample_input": p.sample_input,
                    "sample_output": p.sample_output,
                    "test_input": p.test_input,
                    "test_output": p.test_output,
                    "language": p.language
                })
            
            # 计算总页数
            total_pages = (total + per_page - 1) // per_page
            
            return jsonify({
                "success": True,
                "problems": problem_list,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取题目列表失败: {str(e)}"
        }), 500

@app.route('/api/problems/<int:problem_id>', methods=['GET'])
def get_problem_detail(problem_id):
    """获取题目详情"""
    try:
        session_db = Session()
        try:
            problem = session_db.query(Problem).filter_by(id=problem_id).first()
            if not problem:
                return jsonify({
                    "success": False,
                    "error": "题目不存在"
                }), 404

            return jsonify({
                "success": True,
                "problem": {
                    "id": problem.id,
                    "problem_number": problem.problem_number,
                    "title": problem.title,
                    "description": problem.description,
                    "input_description": problem.input_description,
                    "output_description": problem.output_description,
                    "sample_input": problem.sample_input,
                    "sample_output": problem.sample_output,
                    "test_input": problem.test_input,
                    "test_output": problem.test_output,
                    "category": problem.category,
                    "difficulty": problem.difficulty,
                    "required_functions": problem.required_functions
                }
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取题目详情失败: {str(e)}"
        }), 500

@app.route('/api/problems/detail', methods=['GET'])
def get_problem_by_number():
    """根据题目编号获取题目详情"""
    try:
        number = request.args.get('number', type=int)
        if not number:
            return jsonify({
                "success": False,
                "error": "题目编号不能为空"
            }), 400
        
        session_db = Session()
        try:
            problem = session_db.query(Problem).filter_by(problem_number=number).first()
            if not problem:
                return jsonify({
                    "success": False,
                    "error": "题目不存在"
                })
            
            return jsonify({
                "success": True,
                "problem": {
                    "id": problem.id,
                    "problem_number": problem.problem_number,
                    "title": problem.title,
                    "description": problem.description,
                    "input_description": problem.input_description,
                    "output_description": problem.output_description,
                    "sample_input": problem.sample_input,
                    "sample_output": problem.sample_output,
                    "test_input": problem.test_input,
                    "test_output": problem.test_output,
                    "category": problem.category,
                    "difficulty": problem.difficulty,
                    "required_functions": problem.required_functions
                }
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取题目详情失败: {str(e)}"
        }), 500

@app.route('/api/problems', methods=['POST'])
def add_problem():
    """添加题目"""
    try:
        data = request.json
        if not data or not data.get('title'):
            return jsonify({
                "success": False,
                "error": "题目标题不能为空"
            }), 400

        session_db = Session()
        try:
            # 查找手动添加题目的最大编号（小于10000）
            max_problem = session_db.query(Problem).filter(Problem.problem_number < 10000).order_by(Problem.problem_number.desc()).first()
            problem_number = (max_problem.problem_number + 1) if max_problem else 1

            # 处理必需函数列表
            required_functions = data.get('required_functions', '')
            if required_functions:
                # 如果是数组，转换为JSON字符串
                if isinstance(required_functions, list):
                    required_functions = json.dumps(required_functions)
                elif not required_functions.startswith('['):
                    # 如果是逗号分隔的字符串，转换为JSON格式
                    func_list = [f.strip() for f in required_functions.split(',') if f.strip()]
                    required_functions = json.dumps(func_list)

            problem = Problem(
                problem_number=problem_number,
                title=data['title'],
                description=data.get('description', ''),
                input_description=data.get('input_description', ''),
                output_description=data.get('output_description', ''),
                sample_input=data.get('sample_input', ''),
                sample_output=data.get('sample_output', ''),
                test_input=data.get('test_input', ''),
                test_output=data.get('test_output', ''),
                category=data.get('category', ''),
                required_functions=required_functions,
                difficulty=data.get('difficulty', '入门')
            )
            session_db.add(problem)
            session_db.commit()

            return jsonify({
                "success": True,
                "message": "题目添加成功",
                "problem": {
                    "id": problem.id,
                    "problem_number": problem.problem_number,
                    "title": problem.title
                }
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"添加题目失败: {str(e)}"
        }), 500

@app.route('/api/problems/generate', methods=['POST'])
def generate_problems_by_ai():
    """通过DeepSeek AI生成编程题目"""
    try:
        data = request.json
        if not data:
            return jsonify({
                "success": False,
                "error": "请求数据不能为空"
            }), 400

        topic = data.get('topic', '')
        count = data.get('count', 1)
        difficulty = data.get('difficulty', '入门')
        require_custom_function = data.get('require_custom_function', True)
        language = data.get('language', 'python')

        if not topic:
            return jsonify({
                "success": False,
                "error": "请输入要生成的题目知识点"
            }), 400

        if count < 1 or count > 10:
            return jsonify({
                "success": False,
                "error": "生成题目数量必须在1-10之间"
            }), 400

        # 获取DeepSeek分析器实例
        analyzer = get_deepseek_analyzer()
        print("DEBUG: analyzer=", analyzer)
        print("DEBUG: analyzer.api_key=", getattr(analyzer, 'api_key', 'N/A'))
        print("DEBUG: api_key length=", len(getattr(analyzer, 'api_key', '')))
        if not analyzer or not getattr(analyzer, 'api_key', ''):
            return jsonify({
                "success": False,
                "error": "DeepSeek API密钥未配置，请设置环境变量 DEEPSEEK_API_KEY"
            }), 500

        # 调用DeepSeek生成题目
        print("DEBUG: Calling generate_problems with topic=", topic, "count=", count, "difficulty=", difficulty, "require_custom_function=", require_custom_function, "language=", language)
        problems_data = analyzer.generate_problems(topic, count, difficulty, require_custom_function, language)
        print("DEBUG: generate_problems returned:", problems_data)

        if problems_data is None:
            return jsonify({
                "success": False,
                "error": "DeepSeek API调用失败，请检查网络连接或API密钥"
            }), 500

        if not problems_data:
            return jsonify({
                "success": False,
                "error": "题目生成失败，API返回格式不正确，请稍后重试"
            }), 500

        # 将生成的题目保存到数据库
        session_db = Session()
        try:
            # 查找AI生成题目的最大编号（从10000开始）
            max_ai_problem = session_db.query(Problem).filter(Problem.problem_number >= 10000).order_by(Problem.problem_number.desc()).first()
            problem_number = (max_ai_problem.problem_number + 1) if max_ai_problem else 10000

            saved_problems = []
            for p in problems_data:
                description = p.get('description', '')
                # 从题目描述中提取函数名称
                # 匹配模式：名为xxx的函数、定义一个名为xxx的函数、函数名为xxx
                func_name_match = re.search(r'(?:名为|函数名\s*[为:]\s*["\']?)([a-zA-Z_][a-zA-Z0-9_]*)(?:["\'])?', description)
                extracted_func_name = func_name_match.group(1) if func_name_match else None
                
                # 获取AI返回的required_functions
                ai_required_funcs = p.get('required_functions', '')
                
                # 确定最终的必需函数列表
                if extracted_func_name:
                    # 如果从描述中提取到函数名，使用提取的函数名
                    required_funcs_list = [extracted_func_name]
                elif ai_required_funcs and ai_required_funcs.strip():
                    # 否则使用AI返回的函数名
                    required_funcs_list = [f.strip() for f in ai_required_funcs.split(',') if f.strip()]
                else:
                    required_funcs_list = []
                
                # 转换为JSON字符串格式
                required_functions_json = json.dumps(required_funcs_list)
                
                problem = Problem(
                        problem_number=problem_number,
                        title=p.get('title', ''),
                        description=description,
                        input_description=p.get('input_description', ''),
                        output_description=p.get('output_description', ''),
                        sample_input=p.get('sample_input', ''),
                        sample_output=p.get('sample_output', ''),
                        test_input=p.get('test_input', ''),
                        test_output=p.get('test_output', ''),
                        category=topic,
                        language=p.get('language', language),
                        difficulty=difficulty,
                        required_functions=required_functions_json
                    )
                session_db.add(problem)
                problem_number += 1
                saved_problems.append({
                    "id": problem.id,
                    "problem_number": problem.problem_number,
                    "title": problem.title
                })

            session_db.commit()

            return jsonify({
                "success": True,
                "message": f"成功生成 {len(saved_problems)} 道题目",
                "problems": saved_problems
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"生成题目失败: {str(e)}"
        }), 500

@app.route('/api/problems/<int:problem_id>', methods=['PUT'])
def update_problem(problem_id):
    """更新题目"""
    try:
        data = request.json
        if not data:
            return jsonify({
                "success": False,
                "error": "请求数据不能为空"
            }), 400

        session_db = Session()
        try:
            problem = session_db.query(Problem).filter_by(id=problem_id).first()
            if not problem:
                return jsonify({
                    "success": False,
                    "error": "题目不存在"
                }), 404

            # 更新题目信息
            if 'title' in data:
                problem.title = data['title']
            if 'description' in data:
                problem.description = data['description']
            if 'input_description' in data:
                problem.input_description = data['input_description']
            if 'output_description' in data:
                problem.output_description = data['output_description']
            if 'sample_input' in data:
                problem.sample_input = data['sample_input']
            if 'sample_output' in data:
                problem.sample_output = data['sample_output']
            if 'test_input' in data:
                problem.test_input = data['test_input']
            if 'test_output' in data:
                problem.test_output = data['test_output']
            if 'category' in data:
                problem.category = data['category']
            if 'required_functions' in data:
                # 处理必需函数列表
                required_functions = data['required_functions']
                if required_functions:
                    # 如果是数组，转换为JSON字符串
                    if isinstance(required_functions, list):
                        required_functions = json.dumps(required_functions)
                    elif not required_functions.startswith('['):
                        # 如果是逗号分隔的字符串，转换为JSON格式
                        func_list = [f.strip() for f in required_functions.split(',') if f.strip()]
                        required_functions = json.dumps(func_list)
                problem.required_functions = required_functions
            if 'difficulty' in data:
                problem.difficulty = data['difficulty']

            session_db.commit()

            return jsonify({
                "success": True,
                "message": "题目更新成功"
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"更新题目失败: {str(e)}"
        }), 500

@app.route('/api/problems/<int:problem_id>', methods=['DELETE'])
def delete_problem(problem_id):
    """删除题目"""
    try:
        session_db = Session()
        try:
            problem = session_db.query(Problem).filter_by(id=problem_id).first()
            if not problem:
                return jsonify({
                    "success": False,
                    "error": "题目不存在"
                }), 404

            session_db.delete(problem)
            session_db.commit()

            return jsonify({
                "success": True,
                "message": "题目删除成功"
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"删除题目失败: {str(e)}"
        }), 500

@app.route('/api/submit', methods=['POST'])
def submit_code():
    """学生提交代码接口"""
    try:
        # 确保请求方法是POST
        if request.method != 'POST':
            return jsonify({
                "success": False,
                "error": "请求方法错误，需要POST方法"
            }), 405

        # 获取请求数据
        try:
            data = request.json
        except Exception as e:
            print(f"解析请求数据失败: {e}")
            return jsonify({
                "success": False,
                "error": "请求数据格式错误"
            }), 400

        if not data or 'student_id' not in data or 'code' not in data:
            return jsonify({
                "success": False,
                "error": "请求参数不完整，需要student_id和code"
            }), 400

        student_id = data['student_id']
        code = data['code'].strip()
        input_data = data.get('input_data', '').strip()
        problem_id = data.get('problem_id')
        language = data.get('language', 'python')
        is_homework_submission = data.get('is_homework_submission', False)

        if not code:
            return jsonify({
                "success": False,
                "error": "代码内容不能为空"
            }), 400

        # 简化分析逻辑，确保始终返回score字段
        analysis_result = {
            'is_correct': True,
            'score': 100,
            'error_type': '无错误',
            'hint': '代码分析完成',
            'hint_en': 'Code analysis completed'
        }

        # 获取题目信息（如果有problem_id）
        required_functions = ''
        if problem_id:
            session_db_check = Session()
            try:
                problem = session_db_check.query(Problem).filter_by(id=problem_id).first()
                if problem and problem.required_functions:
                    required_functions = problem.required_functions
            finally:
                session_db_check.close()

        # 尝试执行代码
        try:
            import io
            import sys

            # 根据语言执行代码
            if language == 'python':
                # 先尝试执行代码，获取真实的错误信息
                execution_result = None
                actual_error = None
                try:
                    execution_result = execute_python_code_with_input(code, input_data)
                except Exception as exec_e:
                    actual_error = str(exec_e)
                
                # 检查是否有错误
                has_error = False
                if actual_error:
                    has_error = True
                elif execution_result and ('执行错误' in execution_result or 'Error' in execution_result or 'Traceback' in execution_result):
                    has_error = True
                
                if has_error:
                    # 使用本地编译器的错误信息作为主要提示
                    error_msg = actual_error if actual_error else execution_result
                    analysis_result['is_correct'] = False
                    analysis_result['score'] = 0
                    analysis_result['hint'] = error_msg
                    analysis_result['hint_en'] = error_msg
                    
                    # 确定错误类型
                    if 'SyntaxError' in error_msg or 'IndentationError' in error_msg:
                        analysis_result['error_type'] = '语法错误'
                    elif 'NameError' in error_msg:
                        analysis_result['error_type'] = '名称错误'
                    elif 'TypeError' in error_msg:
                        analysis_result['error_type'] = '类型错误'
                    elif 'IndexError' in error_msg:
                        analysis_result['error_type'] = '索引错误'
                    else:
                        analysis_result['error_type'] = '运行错误'
                    
                    analysis_result['execution_result'] = error_msg
                    
                    # 调用DeepSeek API分析错误原因（不覆盖原始错误信息）
                    try:
                        analyzer = get_deepseek_analyzer()
                        if analyzer and analyzer.api_key:
                            error_prompt = f"""你是一位Python编程教师，请分析以下代码的错误原因并提供修复建议：

代码：
```python
{code}
```

错误信息：{error_msg}

请按照以下JSON格式返回分析结果：
{{
  "error_reason": "错误原因的详细分析，解释为什么会出现这个错误",
  "fix_suggestion": "具体的修改建议，包括正确的代码示例",
  "knowledge_tags": ["涉及的知识点标签"]
}}

请只返回JSON格式，不要包含其他无关内容。"""
                            
                            deepseek_analysis = analyzer.analyze_with_deepseek(error_prompt)
                            if isinstance(deepseek_analysis, dict):
                                if 'error_reason' in deepseek_analysis:
                                    analysis_result['error_reason'] = deepseek_analysis['error_reason']
                                if 'fix_suggestion' in deepseek_analysis:
                                    analysis_result['fix_suggestion'] = deepseek_analysis['fix_suggestion']
                                if 'knowledge_tags' in deepseek_analysis:
                                    analysis_result['knowledge_tags'] = deepseek_analysis['knowledge_tags']
                    except Exception as api_e:
                        print(f"DeepSeek API分析失败: {api_e}")
                else:
                    # 代码执行成功，继续进行必需函数检查
                    analysis_result['execution_result'] = execution_result
                    # AST分析：检查必需函数是否定义
                    ast_ok, ast_msg = analyze_python_ast(code, required_functions)
                    if not ast_ok:
                        analysis_result['is_correct'] = False
                        analysis_result['score'] = 0
                        analysis_result['error_type'] = '缺少必需函数定义'
                        analysis_result['hint'] = ast_msg
                        analysis_result['hint_en'] = 'Missing required function definition'
                    else:
                        # 如果有必需函数要求，检查函数调用
                        if required_functions and required_functions.strip():
                            call_ok, call_msg, exec_result = trace_python_function_calls(code, input_data, required_functions)
                            if not call_ok:
                                analysis_result['is_correct'] = False
                                analysis_result['score'] = 0
                                analysis_result['error_type'] = '必需函数未被调用'
                                analysis_result['hint'] = call_msg
                                analysis_result['hint_en'] = 'Required function not called'
                                analysis_result['execution_result'] = exec_result
                                
                                # 调用DeepSeek API分析错误原因和修复建议
                                try:
                                    analyzer = get_deepseek_analyzer()
                                    if analyzer and analyzer.api_key:
                                        error_prompt = f"""你是一位Python编程教师，请分析以下代码的错误原因并提供修复建议：

代码：
```python
{code}
```

错误信息：{call_msg}

请按照以下JSON格式返回分析结果：
{{
  "error_reason": "错误原因的详细分析",
  "fix_suggestion": "具体的修改建议"
}}

请只返回JSON格式，不要包含其他无关内容。"""
                                        
                                        deepseek_analysis = analyzer.analyze_with_deepseek(error_prompt)
                                        if isinstance(deepseek_analysis, dict):
                                            if 'error_reason' in deepseek_analysis:
                                                analysis_result['error_reason'] = deepseek_analysis['error_reason']
                                            if 'fix_suggestion' in deepseek_analysis:
                                                analysis_result['fix_suggestion'] = deepseek_analysis['fix_suggestion']
                                except Exception as api_e:
                                    print(f"DeepSeek API分析失败: {api_e}")
                            else:
                                analysis_result['execution_result'] = exec_result
                        # 没有必需函数要求，execution_result已经在前面获取了
            elif language in ['c', 'cpp']:
                # C/C++代码执行
                success, result = execute_c_cpp_code(code, language, input_data)
                if success:
                    analysis_result['execution_result'] = result
                    analysis_result['is_correct'] = True
                    analysis_result['score'] = 100
                    analysis_result['error_type'] = '无错误'
                    analysis_result['hint'] = '代码编译执行成功'
                    analysis_result['hint_en'] = 'Code compiled and executed successfully'
                else:
                    analysis_result['execution_result'] = result
                    analysis_result['is_correct'] = False
                    analysis_result['score'] = 0
                    analysis_result['error_type'] = '编译或执行错误'
                    analysis_result['hint'] = result
                    analysis_result['hint_en'] = 'Compilation or execution error'
                    
                    # 调用DeepSeek API分析错误原因和修改建议
                    try:
                        analyzer = get_deepseek_analyzer()
                        if analyzer and analyzer.api_key:
                            error_prompt = f"""你是一位C/C++编程教师，请分析以下{language}代码的错误原因并提供修改建议：

代码：
```cpp
{code}
```

错误信息：{result}

请按照以下JSON格式返回分析结果：
{{
  "error_reason": "错误原因的详细分析",
  "fix_suggestion": "具体的修改建议"
}}

请只返回JSON格式，不要包含其他无关内容。"""
                            
                            deepseek_analysis = analyzer.analyze_with_deepseek(error_prompt)
                            if isinstance(deepseek_analysis, dict):
                                if 'error_reason' in deepseek_analysis:
                                    analysis_result['error_reason'] = deepseek_analysis['error_reason']
                                if 'fix_suggestion' in deepseek_analysis:
                                    analysis_result['fix_suggestion'] = deepseek_analysis['fix_suggestion']
                    except Exception as api_e:
                        print(f"DeepSeek API分析失败: {api_e}")
            elif language == 'java':
                # Java代码执行
                success, result = execute_java_code(code, input_data)
                if success:
                    analysis_result['execution_result'] = result
                    analysis_result['is_correct'] = True
                    analysis_result['score'] = 100
                    analysis_result['error_type'] = '无错误'
                    analysis_result['hint'] = '代码编译执行成功'
                    analysis_result['hint_en'] = 'Code compiled and executed successfully'
                else:
                    analysis_result['execution_result'] = result
                    analysis_result['is_correct'] = False
                    analysis_result['score'] = 0
                    analysis_result['error_type'] = '编译或执行错误'
                    analysis_result['hint'] = result
                    analysis_result['hint_en'] = 'Compilation or execution error'
            elif language == 'go':
                # Go代码执行
                success, result = execute_go_code(code, input_data)
                if success:
                    analysis_result['execution_result'] = result
                    analysis_result['is_correct'] = True
                    analysis_result['score'] = 100
                    analysis_result['error_type'] = '无错误'
                    analysis_result['hint'] = '代码编译执行成功'
                    analysis_result['hint_en'] = 'Code compiled and executed successfully'
                else:
                    analysis_result['execution_result'] = result
                    analysis_result['is_correct'] = False
                    analysis_result['score'] = 0
                    analysis_result['error_type'] = '编译或执行错误'
                    analysis_result['hint'] = result
                    analysis_result['hint_en'] = 'Compilation or execution error'
            else:
                # 其他语言调用DeepSeek分析器进行分析
                analyzer = get_deepseek_analyzer()
                if analyzer and analyzer.api_key:
                    prompt = f"""你是一位编程教师，请分析以下{language}代码：

```
{code}
```

请按照以下格式返回分析结果：
1. is_correct: 布尔值，表示代码是否正确
2. error_type: 字符串，错误类型
3. hint: 字符串，详细的错误提示或改进建议
4. knowledge_tags: 数组，涉及的知识点标签

请严格按照JSON格式返回，不要包含其他无关内容。"""
                    
                    deepseek_result = analyzer.analyze_with_deepseek(prompt)
                    
                    if isinstance(deepseek_result, dict):
                        if 'is_correct' in deepseek_result:
                            analysis_result['is_correct'] = deepseek_result['is_correct']
                        if 'error_type' in deepseek_result:
                            analysis_result['error_type'] = deepseek_result['error_type']
                        if 'hint' in deepseek_result:
                            analysis_result['hint'] = deepseek_result['hint']
                        if 'hint_en' in deepseek_result:
                            analysis_result['hint_en'] = deepseek_result['hint_en']
                        if 'knowledge_tags' in deepseek_result:
                            analysis_result['knowledge_tags'] = deepseek_result['knowledge_tags']
                    
                    analysis_result['execution_result'] = f'已通过AI进行{language}代码分析'
                else:
                    analysis_result['execution_result'] = f'暂不支持{language}代码分析'
                    analysis_result['is_correct'] = True
                    analysis_result['score'] = 100
                    analysis_result['error_type'] = '无错误'
                    analysis_result['hint'] = '代码分析完成'
                    analysis_result['hint_en'] = 'Code analysis completed'
        except Exception as e:
            analysis_result['is_correct'] = False
            analysis_result['score'] = 0
            analysis_result['error_type'] = '执行错误'
            analysis_result['hint'] = f'代码执行出错: {str(e)}'
            analysis_result['hint_en'] = f'Code execution failed: {str(e)}'
            
            # 调用DeepSeek API分析错误原因和修改建议
            try:
                analyzer = get_deepseek_analyzer()
                if analyzer and analyzer.api_key:
                    error_prompt = f"""你是一位编程教师，请分析以下{language}代码的错误原因并提供修改建议：

代码：
```
{code}
```

错误信息：{str(e)}

请按照以下JSON格式返回分析结果：
{{
  "error_reason": "错误原因的详细分析",
  "fix_suggestion": "具体的修改建议"
}}

请只返回JSON格式，不要包含其他无关内容。"""
                    
                    deepseek_analysis = analyzer.analyze_with_deepseek(error_prompt)
                    if isinstance(deepseek_analysis, dict):
                        if 'error_reason' in deepseek_analysis:
                            analysis_result['error_reason'] = deepseek_analysis['error_reason']
                        if 'fix_suggestion' in deepseek_analysis:
                            analysis_result['fix_suggestion'] = deepseek_analysis['fix_suggestion']
            except Exception as api_e:
                print(f"DeepSeek API分析失败: {api_e}")

        # 保存到数据库
        session_db = None
        try:
            session_db = Session()
            # 前端传递的可能是students表的id或users表的id
            # 先尝试根据students表的id查找
            student = session_db.query(Student).filter_by(id=student_id).first()
            # 如果找不到，再尝试根据users表的id查找
            if not student:
                student = session_db.query(Student).filter_by(user_id=student_id).first()
            # 如果都找不到，创建新的学生记录
            if not student:
                student = Student(
                    user_id=student_id,
                    name="Unknown",
                    student_id=str(student_id),
                    class_name="Unknown"
                )
                session_db.add(student)
                session_db.commit()

            if problem_id:
                problem = session_db.query(Problem).filter_by(id=problem_id).first()
                if problem and problem.category:
                    analysis_result['knowledge_tags'] = [problem.category]
                elif problem:
                    analysis_result['knowledge_tags'] = ["基础语法"]

                if problem and problem.sample_output and 'execution_result' in analysis_result:
                    # 只有Python、C、C++、Java代码才比较执行结果，其他语言依赖AI分析
                    if language in ['python', 'c', 'cpp', 'java']:
                        # 如果已经有错误（如必需函数错误），不再覆盖
                        if analysis_result.get('is_correct', True):
                            def normalize_output(output):
                                return output.strip().replace('\r\n', '\n').replace('\r', '\n')

                            normalized_execution = normalize_output(analysis_result['execution_result'])
                            normalized_sample = normalize_output(problem.sample_output)

                            # 检查样例输出是否匹配
                            if normalized_execution != normalized_sample:
                                analysis_result['is_correct'] = False
                                analysis_result['score'] = 0
                                analysis_result['error_type'] = '运行结果不准确'
                                analysis_result['hint'] = '您的代码运行结果与样例输出不一致'
                                analysis_result['hint_en'] = 'Your code execution result does not match the sample output'
                            else:
                                # 如果题目有样例输入，检查代码是否读取了输入
                                if problem.sample_input and problem.sample_input.strip():
                                    # 检查Python代码是否使用了input()函数
                                    if language == 'python' and 'input(' not in code and 'sys.stdin' not in code:
                                        analysis_result['is_correct'] = False
                                        analysis_result['score'] = 50
                                        analysis_result['error_type'] = '未读取输入'
                                        analysis_result['hint'] = '题目要求从输入读取数据，但您的代码没有读取输入，请使用input()函数读取输入数据'
                                        analysis_result['hint_en'] = 'The problem requires reading input, but your code does not read from input. Please use input() function.'
                                    else:
                                        # 样例测试通过，检查是否有测试输入需要验证
                                        if problem.test_input and problem.test_output and problem.test_input.strip() and problem.test_output.strip():
                                            # 使用测试输入运行代码
                                            test_execution_result = execute_python_code_with_input(code, problem.test_input) if language == 'python' else ''
                                            if test_execution_result:
                                                normalized_test = normalize_output(problem.test_output)
                                                normalized_test_execution = normalize_output(test_execution_result)
                                                if normalized_test_execution != normalized_test:
                                                    analysis_result['is_correct'] = False
                                                    analysis_result['score'] = 50
                                                    analysis_result['error_type'] = '测试用例未通过'
                                                    analysis_result['hint'] = '代码通过了样例测试，但未通过隐藏的测试用例'
                                                    analysis_result['hint_en'] = 'Your code passed the sample test but failed the hidden test case'
                                                    
                                                    # 调用DeepSeek API分析错误原因和修改建议
                                                    try:
                                                        analyzer = get_deepseek_analyzer()
                                                        if analyzer and analyzer.api_key:
                                                            error_prompt = f"""你是一位编程教师，请分析以下{language}代码的错误原因并提供修改建议：

代码：
```
{code}
```

题目测试用例：
输入：{problem.test_input}
期望输出：{problem.test_output}
实际输出：{test_execution_result}

请按照以下JSON格式返回分析结果：
{{
  "error_reason": "错误原因的详细分析",
  "fix_suggestion": "具体的修改建议"
}}

请只返回JSON格式，不要包含其他无关内容。"""
                                                            
                                                            deepseek_analysis = analyzer.analyze_with_deepseek(error_prompt)
                                                            if isinstance(deepseek_analysis, dict):
                                                                if 'error_reason' in deepseek_analysis:
                                                                    analysis_result['error_reason'] = deepseek_analysis['error_reason']
                                                                if 'fix_suggestion' in deepseek_analysis:
                                                                    analysis_result['fix_suggestion'] = deepseek_analysis['fix_suggestion']
                                                    except Exception as api_e:
                                                        print(f"DeepSeek API分析失败: {api_e}")
                                                else:
                                                    analysis_result['is_correct'] = True
                                                    analysis_result['score'] = 100
                                                    analysis_result['error_type'] = '无错误'
                                                    analysis_result['hint'] = '代码运行结果与样例输出和测试用例都一致'
                                                    analysis_result['hint_en'] = 'Your code execution result matches both sample output and test case'
                                            else:
                                                analysis_result['is_correct'] = True
                                                analysis_result['score'] = 100
                                                analysis_result['error_type'] = '无错误'
                                                analysis_result['hint'] = '代码运行结果与样例输出一致'
                                                analysis_result['hint_en'] = 'Your code execution result matches the sample output'
                                        else:
                                            analysis_result['is_correct'] = True
                                            analysis_result['score'] = 100
                                            analysis_result['error_type'] = '无错误'
                                            analysis_result['hint'] = '代码运行结果与样例输出一致'
                                            analysis_result['hint_en'] = 'Your code execution result matches the sample output'
                                else:
                                    # 样例测试通过，检查是否有测试输入需要验证
                                    if problem.test_input and problem.test_output and problem.test_input.strip() and problem.test_output.strip():
                                        # 使用测试输入运行代码
                                        test_execution_result = execute_python_code_with_input(code, problem.test_input) if language == 'python' else ''
                                        if test_execution_result:
                                            def normalize_output(output):
                                                return output.strip().replace('\r\n', '\n').replace('\r', '\n')
                                            normalized_test = normalize_output(problem.test_output)
                                            normalized_test_execution = normalize_output(test_execution_result)
                                            if normalized_test_execution != normalized_test:
                                                analysis_result['is_correct'] = False
                                                analysis_result['score'] = 50
                                                analysis_result['error_type'] = '测试用例未通过'
                                                analysis_result['hint'] = '代码通过了样例测试，但未通过隐藏的测试用例'
                                                analysis_result['hint_en'] = 'Your code passed the sample test but failed the hidden test case'
                                                
                                                # 调用DeepSeek API分析错误原因和修改建议
                                                try:
                                                    analyzer = get_deepseek_analyzer()
                                                    if analyzer and analyzer.api_key:
                                                        error_prompt = f"""你是一位编程教师，请分析以下{language}代码的错误原因并提供修改建议：

代码：
```
{code}
```

题目测试用例：
输入：{problem.test_input}
期望输出：{problem.test_output}
实际输出：{test_execution_result}

请按照以下JSON格式返回分析结果：
{{
  "error_reason": "错误原因的详细分析",
  "fix_suggestion": "具体的修改建议"
}}

请只返回JSON格式，不要包含其他无关内容。"""
                                                        
                                                        deepseek_analysis = analyzer.analyze_with_deepseek(error_prompt)
                                                        if isinstance(deepseek_analysis, dict):
                                                            if 'error_reason' in deepseek_analysis:
                                                                analysis_result['error_reason'] = deepseek_analysis['error_reason']
                                                            if 'fix_suggestion' in deepseek_analysis:
                                                                analysis_result['fix_suggestion'] = deepseek_analysis['fix_suggestion']
                                                except Exception as api_e:
                                                    print(f"DeepSeek API分析失败: {api_e}")
                                            else:
                                                analysis_result['is_correct'] = True
                                                analysis_result['score'] = 100
                                                analysis_result['error_type'] = '无错误'
                                                analysis_result['hint'] = '代码运行结果与样例输出和测试用例都一致'
                                                analysis_result['hint_en'] = 'Your code execution result matches both sample output and test case'
                                        else:
                                            analysis_result['is_correct'] = True
                                            analysis_result['score'] = 100
                                            analysis_result['error_type'] = '无错误'
                                            analysis_result['hint'] = '代码运行结果与样例输出一致'
                                            analysis_result['hint_en'] = 'Your code execution result matches the sample output'
                                    else:
                                        analysis_result['is_correct'] = True
                                        analysis_result['score'] = 100
                                        analysis_result['error_type'] = '无错误'
                                        analysis_result['hint'] = '代码运行结果与样例输出一致'
                                        analysis_result['hint_en'] = 'Your code execution result matches the sample output'
                    # 对于非Python、C、C++代码，不比较执行结果，依赖AI分析

            feedback_json = json.dumps(analysis_result)

            # 创建HomeworkSubmission对象
            submission = HomeworkSubmission(
                student_id=student.id,
                problem_id=problem_id,
                code_content=code,
                ai_feedback=feedback_json,
                submission_time=datetime.datetime.now(),
                is_homework_submission=is_homework_submission
            )
            session_db.add(submission)
            session_db.commit()

            # 获取插入的记录ID
            submission_id = submission.id

            return jsonify({
                "success": True,
                "message": "代码分析完成",
                "analysis": analysis_result,
                "submission_id": submission_id
            })
        except Exception as e:
            print(f"数据库操作失败: {e}")
            # 即使数据库操作失败，也返回分析结果
            return jsonify({
                "success": True,
                "message": "代码分析完成，但保存失败",
                "analysis": analysis_result,
                "submission_id": None
            })
        finally:
            if session_db:
                session_db.close()

    except Exception as e:
        print(f"服务器内部错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"服务器内部错误: {str(e)}"
        }), 500

@app.route('/api/test-problem/<int:problem_id>', methods=['POST'])
def test_problem(problem_id):
    """教师测试题目接口"""
    
    try:
        # 获取请求数据
        try:
            data = request.json
        except Exception as e:
            print(f"解析请求数据失败: {e}")
            return jsonify({
                "success": False,
                "error": "请求数据格式错误"
            }), 400

        if not data or 'code' not in data:
            return jsonify({
                "success": False,
                "error": "请求参数不完整，需要code"
            }), 400

        code = data['code'].strip()
        teacher_id = data.get('teacher_id')

        if not code:
            return jsonify({
                "success": False,
                "error": "代码内容不能为空"
            }), 400

        # 获取题目信息
        session_db = Session()
        try:
            problem = session_db.query(Problem).filter_by(id=problem_id).first()
            if not problem:
                return jsonify({
                    "success": False,
                    "error": "题目不存在"
                }), 404

            # 获取语言（从题目分类中提取）
            category = problem.category or ''
            language = 'python'
            if category.startswith('C-'):
                language = 'c'
            elif category.startswith('C++-'):
                language = 'cpp'
            elif category.startswith('Java-'):
                language = 'java'
            elif category.startswith('Go-'):
                language = 'go'

            # 执行代码
            execution_output = ''
            has_error = False
            error_message = ''

            if language == 'python':
                if problem.sample_input and problem.sample_input.strip():
                    execution_output = execute_python_code_with_input(code, problem.sample_input)
                else:
                    execution_output = execute_python_code_with_input(code, '')
            elif language in ['c', 'cpp']:
                success, result = execute_c_cpp_code(code, language, problem.sample_input or '')
                if success:
                    execution_output = result
                else:
                    has_error = True
                    error_message = result
            elif language == 'java':
                success, result = execute_java_code(code, problem.sample_input or '')
                if success:
                    execution_output = result
                else:
                    has_error = True
                    error_message = result
            elif language == 'go':
                success, result = execute_go_code(code, problem.sample_input or '')
                if success:
                    execution_output = result
                else:
                    has_error = True
                    error_message = result

            # 验证结果
            test_result = "failed"
            
            if problem.sample_output and problem.sample_output.strip():
                normalized_output = execution_output.strip().replace('\r\n', '\n').replace('\r', '\n')
                normalized_sample = problem.sample_output.strip().replace('\r\n', '\n').replace('\r', '\n')
                
                if normalized_output == normalized_sample:
                    if problem.test_input and problem.test_output and problem.test_input.strip() and problem.test_output.strip():
                        test_output = ''
                        if language == 'python':
                            test_output = execute_python_code_with_input(code, problem.test_input)
                        elif language in ['c', 'cpp']:
                            success, test_output = execute_c_cpp_code(code, language, problem.test_input)
                        elif language == 'java':
                            success, test_output = execute_java_code(code, problem.test_input)
                        elif language == 'go':
                            success, test_output = execute_go_code(code, problem.test_input)
                        
                        if test_output:
                            normalized_test = problem.test_output.strip().replace('\r\n', '\n').replace('\r', '\n')
                            normalized_test_output = test_output.strip().replace('\r\n', '\n').replace('\r', '\n')
                            
                            if normalized_test_output == normalized_test:
                                test_result = "success"
                            else:
                                test_result = "failed"
                    else:
                        test_result = "success"

            # 保存提交记录
            analysis_result = {
                'is_correct': test_result == 'success',
                'score': 100 if test_result == 'success' else 0,
                'error_type': '无错误' if test_result == 'success' else '运行结果不准确',
                'hint': '教师测试提交',
                'hint_en': 'Teacher test submission',
                'test_result': test_result,
                'execution_output': execution_output,
                'error_message': error_message if has_error else ''
            }
            
            submission = HomeworkSubmission(
                student_id=None,
                teacher_id=teacher_id,
                problem_id=problem_id,
                code_content=code,
                ai_feedback=json.dumps(analysis_result),
                submission_time=datetime.datetime.now(),
                is_homework_submission=False
            )
            session_db.add(submission)
            session_db.commit()
            submission_id = submission.id

            return jsonify({
                "success": True,
                "result": test_result,
                "output": execution_output,
                "error": error_message if has_error else None,
                "submission_id": submission_id
            })

        finally:
            session_db.close()

    except Exception as e:
        print(f"测试题目失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"测试题目失败: {str(e)}"
        }), 500

@app.route('/api/submissions/<int:student_id>', methods=['GET'])
def get_student_submissions(student_id):
    """获取学生的提交历史记录，支持按题目ID筛选"""
    session_db = None
    try:
        # 暂时取消认证要求，方便测试
        # token = request.headers.get('Authorization')
        # if not token:
        #     return jsonify({"success": False, "error": "未提供认证令牌"}), 401

        # token_parts = token.split(' ')
        # if len(token_parts) != 2 or token_parts[0] != 'Bearer':
        #     return jsonify({"success": False, "error": "认证令牌格式错误"}), 401

        session_db = Session()

        # 前端传递的可能是students表的id或users表的id
        # 先尝试根据students表的id查找
        student = session_db.query(Student).filter_by(id=student_id).first()
        # 如果找不到，再尝试根据users表的id查找
        if not student:
            student = session_db.query(Student).filter_by(user_id=student_id).first()
        if not student:
            return jsonify({
                "success": False,
                "error": "学生不存在",
                "submissions": [],
                "total": 0
            }), 404
        query_student_id = student.id
        
        # 获取可选的problem_id查询参数
        problem_id = request.args.get('problem_id', type=int)

        from sqlalchemy import text
        
        # 构建查询语句，关联problems表获取题目编号
        if problem_id:
            result = session_db.execute(
                text("SELECT hs.id, hs.student_id, hs.problem_id, p.problem_number, hs.code_content, hs.ai_feedback, hs.submission_time, hs.is_homework_submission FROM homework_submissions hs LEFT JOIN problems p ON hs.problem_id = p.id WHERE hs.student_id = :student_id AND hs.problem_id = :problem_id ORDER BY hs.submission_time DESC"),
                {"student_id": query_student_id, "problem_id": problem_id}
            )
        else:
            result = session_db.execute(
                text("SELECT hs.id, hs.student_id, hs.problem_id, p.problem_number, hs.code_content, hs.ai_feedback, hs.submission_time, hs.is_homework_submission FROM homework_submissions hs LEFT JOIN problems p ON hs.problem_id = p.id WHERE hs.student_id = :student_id ORDER BY hs.submission_time DESC"),
                {"student_id": query_student_id}
            )

        submissions = []
        for row in result:
            # 解析 ai_feedback 获取正确性信息
            is_correct = '未知'
            try:
                if row[5]:
                    feedback = json.loads(row[5])
                    if isinstance(feedback, dict) and 'is_correct' in feedback:
                        is_correct = '正确' if feedback['is_correct'] else '错误'
            except:
                is_correct = '未知'
            
            submission = {
                'id': row[0],
                'student_id': row[1],
                'problem_id': row[2],
                'problem_number': row[3] if row[3] is not None else '未知',
                'code_content': row[4],
                'ai_feedback': row[5],
                'submission_time': row[6],
                'is_homework_submission': bool(row[7]) if len(row) > 7 and row[7] is not None else False,
                'is_correct': is_correct
            }
            submissions.append(submission)

        return jsonify({
            "success": True,
            "submissions": submissions,
            "total": len(submissions)
        })
    except Exception as e:
        print(f"获取提交记录失败: {e}")
        return jsonify({
            "success": False,
            "error": f"获取提交记录失败: {str(e)}"
        }), 500
    finally:
        if session_db:
            session_db.close()

@app.route('/api/teacher/submissions', methods=['GET'])
def get_teacher_submissions():
    """获取教师的所有测试提交记录"""
    session_db = None
    try:
        teacher_id = request.args.get('teacher_id')
        if not teacher_id:
            return jsonify({"success": False, "error": "缺少teacher_id参数"}), 400

        session_db = Session()

        from sqlalchemy import text
        result = session_db.execute(
            text("""
                SELECT 
                    hs.id, 
                    hs.teacher_id,
                    t.username as teacher_name,
                    hs.problem_id, 
                    p.title as problem_title,
                    p.category as problem_category,
                    hs.code_content, 
                    hs.ai_feedback, 
                    hs.submission_time 
                FROM 
                    homework_submissions hs
                LEFT JOIN 
                    teachers t ON hs.teacher_id = t.id
                LEFT JOIN 
                    problems p ON hs.problem_id = p.id
                WHERE 
                    hs.teacher_id = :teacher_id 
                ORDER BY 
                    hs.submission_time DESC
                LIMIT 100
            """),
            {"teacher_id": teacher_id}
        )

        submissions = []
        for row in result:
            ai_feedback = row[7]
            feedback_data = {}
            if ai_feedback:
                try:
                    feedback_data = json.loads(ai_feedback)
                except:
                    pass
            
            submissions.append({
                'id': row[0],
                'teacher_id': row[1],
                'teacher_name': row[2] or '未知教师',
                'problem_id': row[3],
                'problem_title': row[4] or '未知题目',
                'problem_category': row[5] or '',
                'code_content': row[6],
                'ai_feedback': feedback_data,
                'submission_time': row[8].isoformat() if row[8] else None
            })

        return jsonify({
            "success": True,
            "submissions": submissions,
            "total": len(submissions)
        })
    except Exception as e:
        print(f"获取教师提交记录失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"获取教师提交记录失败: {str(e)}"
        }), 500
    finally:
        if session_db:
            session_db.close()

@app.route('/api/problem_submissions/<int:problem_id>', methods=['GET'])
def get_problem_submissions(problem_id):
    """获取某个题目的所有提交记录（包括学生和教师）"""
    session_db = None
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"success": False, "error": "未提供认证令牌"}), 401

        token_parts = token.split(' ')
        if len(token_parts) != 2 or token_parts[0] != 'Bearer':
            return jsonify({"success": False, "error": "认证令牌格式错误"}), 401

        session_db = Session()

        # 先查询所有提交记录
        submissions = session_db.query(HomeworkSubmission)\
            .filter(HomeworkSubmission.problem_id == problem_id)\
            .order_by(HomeworkSubmission.submission_time.desc())\
            .all()

        result_list = []
        for sub in submissions:
            # 获取学生信息
            student_info = session_db.query(Student)\
                .filter(Student.id == sub.student_id)\
                .first() if sub.student_id else None
            
            # 获取教师信息
            teacher_info = session_db.query(Teacher)\
                .filter(Teacher.id == sub.teacher_id)\
                .first() if sub.teacher_id else None
            
            # 获取题目信息
            problem_info = session_db.query(Problem)\
                .filter(Problem.id == sub.problem_id)\
                .first()

            result_list.append({
                'id': sub.id,
                'student_id': student_info.student_id if student_info else None,
                'student_name': student_info.name if student_info else None,
                'teacher_id': sub.teacher_id,
                'teacher_name': teacher_info.username if teacher_info else None,
                'problem_id': sub.problem_id,
                'code_content': sub.code_content,
                'ai_feedback': sub.ai_feedback,
                'submission_time': sub.submission_time,
                'problem_title': problem_info.title if problem_info else None
            })

        return jsonify({
            "success": True,
            "submissions": result_list,
            "total": len(result_list)
        })
    except Exception as e:
        print(f"获取题目提交记录失败: {e}")
        return jsonify({
            "success": False,
            "error": f"获取题目提交记录失败: {str(e)}"
        }), 500
    finally:
        if session_db:
            session_db.close()

@app.route('/api/submissions/today', methods=['GET'])
def get_today_submissions():
    """获取今日提交数"""
    session_db = None
    try:
        session_db = Session()
        
        from sqlalchemy import func
        # 获取今天的日期
        today = datetime.datetime.now().date()
        
        # 查询今日提交数
        count = session_db.query(func.count(HomeworkSubmission.id)).filter(
            func.date(HomeworkSubmission.submission_time) == today
        ).scalar()

        return jsonify({
            "success": True,
            "count": count
        })
    except Exception as e:
        print(f"获取今日提交数失败: {e}")
        return jsonify({
            "success": False,
            "error": f"获取今日提交数失败: {str(e)}"
        }), 500
    finally:
        if session_db:
            session_db.close()



def get_student_knowledge_stats(student_id, session_db):
    """获取单个学生的知识图谱统计数据（内部函数）"""
    try:
        from sqlalchemy import text
        
        # 获取学生的提交记录（使用原始SQL，与学生端API完全一致）
        result = session_db.execute(
            text("""
            SELECT hs.id, hs.student_id, hs.problem_id, hs.code_content, hs.ai_feedback, hs.submission_time 
            FROM homework_submissions hs
            WHERE hs.student_id = :student_id 
            ORDER BY hs.submission_time DESC
            """),
            {"student_id": student_id}
        )

        submissions = []
        for row in result:
            class Submission:
                def __init__(self, id, student_id, problem_id, code_content, ai_feedback, submission_time):
                    self.id = id
                    self.student_id = student_id
                    self.problem_id = problem_id
                    self.code_content = code_content
                    self.ai_feedback = ai_feedback
                    if isinstance(submission_time, str):
                        from datetime import datetime
                        try:
                            self.submission_time = datetime.strptime(submission_time, '%Y-%m-%d %H:%M:%S')
                        except:
                            self.submission_time = datetime.now()
                    else:
                        self.submission_time = submission_time
                    problem = session_db.query(Problem).filter_by(id=problem_id).first()
                    self.category = problem.category if problem else None
            submissions.append(Submission(*row))

        # 获取学生的推荐记录（与学生端API保持一致）
        recommended_knowledge = set()
        try:
            recommends = session_db.query(AIRecommendedHomework).filter(
                AIRecommendedHomework.student_id == student_id
            ).all()
            
            for recommend in recommends:
                if recommend.knowledge_topics:
                    try:
                        knowledge_topics = json.loads(recommend.knowledge_topics)
                        if isinstance(knowledge_topics, list):
                            for problem_number in knowledge_topics:
                                problem = session_db.query(Problem).filter(
                                    Problem.problem_number == problem_number
                                ).first()
                                if problem and problem.category:
                                    topic = problem.category
                                    if '-' in topic:
                                        core_topic = '-'.join(topic.split('-')[1:])
                                    else:
                                        core_topic = topic
                                    recommended_knowledge.add(core_topic)
                    except Exception as e:
                        print(f"解析推荐知识点失败: {str(e)}")
                        pass
        except Exception as e:
            print(f"获取推荐知识点失败: {str(e)}")
            pass

        # 获取学生的第一次推荐时间（与学生端API保持一致）
        first_recommend_time = None
        try:
            first_recommend = session_db.query(AIRecommendedHomework).filter(
                AIRecommendedHomework.student_id == student_id
            ).order_by(AIRecommendedHomework.generated_at).first()
            if first_recommend:
                first_recommend_time = first_recommend.generated_at
        except Exception as e:
            print(f"获取推荐时间失败: {str(e)}")
            first_recommend_time = None

        category_map = {
            "基础语法": "基础", "变量": "基础", "数据类型": "基础", "字符串": "基础",
            "数字": "基础", "布尔值": "基础", "输入输出": "基础", "变量与运算符": "基础", "控制流": "控制流", "循环": "控制流", "循环语句": "控制流",
            "条件语句": "控制流", "函数": "函数", "函数定义": "函数", "函数调用": "函数",
            "列表": "数据结构", "元组": "数据结构", "字典": "数据结构", "集合": "数据结构",
            "索引": "数据结构", "切片": "数据结构", "算术运算": "运算", "逻辑运算": "运算",
            "比较运算": "运算", "调试": "调试", "异常处理": "调试", "文件操作": "文件",
            "模块": "模块", "面向对象": "高级", "类": "高级", "继承": "高级",
        }

        knowledge_stats = {}
        pre_recommend_stats = {}
        post_recommend_stats = {}

        for submission in submissions:
            if submission.ai_feedback:
                try:
                    feedback_dict = json.loads(submission.ai_feedback)
                    is_correct = feedback_dict.get('is_correct', False)

                    # 优先使用题目当前的分类作为知识点标签（与学生端API保持一致）
                    if submission.category:
                        tag = submission.category
                        full_tag = tag
                        
                        if '-' in tag:
                            core_tag = '-'.join(tag.split('-')[1:])
                        else:
                            core_tag = tag
                        
                        language = tag.split('-')[0] if '-' in tag else 'Python'
                        
                        # 统计整体数据
                        if full_tag not in knowledge_stats:
                            knowledge_stats[full_tag] = {'total': 0, 'correct': 0, 'category': category_map.get(core_tag, '其他'), 'language': language}
                        knowledge_stats[full_tag]['total'] += 1
                        if is_correct:
                            knowledge_stats[full_tag]['correct'] += 1
                        
                        # 统计推荐前数据 - 包含所有提交记录（不考虑推荐时间）
                        if full_tag not in pre_recommend_stats:
                            pre_recommend_stats[full_tag] = {'total': 0, 'correct': 0, 'category': category_map.get(core_tag, '其他'), 'language': language}
                        pre_recommend_stats[full_tag]['total'] += 1
                        if is_correct:
                            pre_recommend_stats[full_tag]['correct'] += 1
                        
                        # 统计推荐后数据 - 只有被推荐过的知识点且在推荐后提交的才统计
                        if first_recommend_time and submission.submission_time >= first_recommend_time:
                            # 检查该知识点是否被推荐过
                            if core_tag in recommended_knowledge:
                                if full_tag not in post_recommend_stats:
                                    post_recommend_stats[full_tag] = {'total': 0, 'correct': 0, 'category': category_map.get(core_tag, '其他'), 'language': language}
                                post_recommend_stats[full_tag]['total'] += 1
                                if is_correct:
                                    post_recommend_stats[full_tag]['correct'] += 1
                    # 如果题目分类为空，从ai_feedback中的knowledge_tags获取（与学生端API保持一致）
                    elif 'knowledge_tags' in feedback_dict:
                        for tag in feedback_dict['knowledge_tags']:
                            full_tag = tag
                            
                            if '-' in tag:
                                core_tag = '-'.join(tag.split('-')[1:])
                            else:
                                core_tag = tag
                            
                            language = tag.split('-')[0] if '-' in tag else 'Python'
                            
                            # 统计整体数据
                            if full_tag not in knowledge_stats:
                                knowledge_stats[full_tag] = {'total': 0, 'correct': 0, 'category': category_map.get(core_tag, '其他'), 'language': language}
                            knowledge_stats[full_tag]['total'] += 1
                            if is_correct:
                                knowledge_stats[full_tag]['correct'] += 1
                            
                            # 统计推荐前数据
                            if full_tag not in pre_recommend_stats:
                                pre_recommend_stats[full_tag] = {'total': 0, 'correct': 0, 'category': category_map.get(core_tag, '其他'), 'language': language}
                            pre_recommend_stats[full_tag]['total'] += 1
                            if is_correct:
                                pre_recommend_stats[full_tag]['correct'] += 1
                            
                            # 统计推荐后数据
                            if first_recommend_time and submission.submission_time >= first_recommend_time:
                                if core_tag in recommended_knowledge:
                                    if full_tag not in post_recommend_stats:
                                        post_recommend_stats[full_tag] = {'total': 0, 'correct': 0, 'category': category_map.get(core_tag, '其他'), 'language': language}
                                    post_recommend_stats[full_tag]['total'] += 1
                                    if is_correct:
                                        post_recommend_stats[full_tag]['correct'] += 1
                except Exception as e:
                    print(f"处理提交数据失败: {str(e)}")
                    pass

        # 从新表中读取推荐前的掌握率（与学生端API保持一致）
        if knowledge_stats:
            for name, stats in knowledge_stats.items():
                # 提取核心知识点名称
                if '-' in name:
                    core_topic = '-'.join(name.split('-')[1:])
                else:
                    core_topic = name
                
                # 从新表中查询推荐前的掌握率
                from sqlalchemy import text
                pre_recommend_record = session_db.execute(
                    text('''
                        SELECT pre_recommend_mastery FROM knowledge_recommendation_status 
                        WHERE student_id = :student_id AND knowledge_name = :knowledge_name
                    '''), 
                    {'student_id': student_id, 'knowledge_name': core_topic}
                ).fetchone()
                
                if pre_recommend_record:
                    # 使用新表中的推荐前掌握率
                    mastery_rate = pre_recommend_record[0]
                    # 计算总提交数和正确数（保持与掌握率一致）
                    total = 10  # 假设总提交数为10
                    correct = int(total * mastery_rate)
                    pre_recommend_stats[name] = {
                        'total': total, 
                        'correct': correct, 
                        'category': stats['category'], 
                        'language': stats['language']
                    }
                else:
                    # 如果没有推荐前数据，使用所有提交记录
                    if name not in pre_recommend_stats:
                        pre_recommend_stats[name] = {
                            'total': 0, 
                            'correct': 0, 
                            'category': stats['category'], 
                            'language': stats['language']
                        }

        return {
            'knowledge_stats': knowledge_stats,
            'pre_recommend_stats': pre_recommend_stats,
            'post_recommend_stats': post_recommend_stats
        }
    except Exception as e:
        print(f"获取学生知识图谱数据失败: {e}")
        return None


@app.route('/api/class_knowledge_map/<class_name>', methods=['GET'])
def get_class_knowledge_map(class_name):
    """获取班级知识图谱数据（统计该班级所有学生的诊断和推荐后掌握率的平均值）"""
    session_db = None
    try:
        session_db = Session()

        # 获取该班级的所有学生
        students = session_db.query(Student).filter_by(class_name=class_name).all()
        if not students:
            default_knowledge = ["基础语法", "变量", "数据类型", "控制流", "循环", "条件语句", "函数", "列表", "调试"]
            knowledge_stats = {}
            category_map = {
                "基础语法": "基础", "变量": "基础", "数据类型": "基础", "字符串": "基础",
                "数字": "基础", "布尔值": "基础", "变量与运算符": "基础", "控制流": "控制流", "循环": "控制流", "循环语句": "控制流",
                "条件语句": "控制流", "函数": "函数", "函数定义": "函数", "函数调用": "函数",
                "列表": "数据结构", "元组": "数据结构", "字典": "数据结构", "集合": "数据结构",
                "索引": "数据结构", "切片": "数据结构", "算术运算": "运算", "逻辑运算": "运算",
                "比较运算": "运算", "调试": "调试", "异常处理": "调试", "文件操作": "文件",
                "模块": "模块", "面向对象": "高级", "类": "高级", "继承": "高级",
            }
            for tag in default_knowledge:
                knowledge_stats[tag] = {'total': 0, 'correct': 0, 'category': category_map.get(tag, '其他')}

            nodes = []
            node_id = 1
            for name, stats in knowledge_stats.items():
                nodes.append({
                    "id": node_id,
                    "name": name,
                    "value": 0.5,
                    "color": "#FFC107",
                    "category": stats['category'],
                    "total": 0,
                    "correct": 0
                })
                node_id += 1

            links = []
            categories = list(set([n['category'] for n in nodes]))
            for i, cat1 in enumerate(categories):
                for cat2 in categories[i+1:]:
                    if cat1 == "基础" or cat2 == "基础":
                        cat1_nodes = [n for n in nodes if n['category'] == cat1]
                        cat2_nodes = [n for n in nodes if n['category'] == cat2]
                        if cat1_nodes and cat2_nodes:
                            links.append({
                                "source": cat1_nodes[0]['id'],
                                "target": cat2_nodes[0]['id'],
                                "value": 1
                            })

            return jsonify({
                "success": True,
                "nodes": nodes,
                "links": links,
                "class_name": class_name,
                "submission_count": 0,
                "knowledge_stats": knowledge_stats,
                "good_count": 0,
                "medium_count": 0,
                "weak_count": len(nodes),
                "pre_recommend_stats": {},
                "post_recommend_stats": {}
            })

        # 获取班级所有学生的提交记录
        student_ids = [s.id for s in students]
        
        # 使用 SQLAlchemy ORM 查询
        submissions_query = session_db.query(
            HomeworkSubmission.id,
            HomeworkSubmission.student_id,
            HomeworkSubmission.problem_id,
            HomeworkSubmission.code_content,
            HomeworkSubmission.ai_feedback,
            HomeworkSubmission.submission_time
        ).filter(HomeworkSubmission.student_id.in_(student_ids)).order_by(HomeworkSubmission.submission_time.desc())
        
        result = submissions_query.all()

        # 如果没有提交记录，返回空数据
        if not result:
            return jsonify({
                "success": True,
                "nodes": [],
                "links": [],
                "class_name": class_name,
                "submission_count": 0,
                "knowledge_stats": {},
                "good_count": 0,
                "medium_count": 0,
                "weak_count": 0,
                "pre_recommend_stats": {},
                "post_recommend_stats": {},
                "no_data": True  # 标记没有数据
            })

        # 知识点分类映射
        category_map = {
            "基础语法": "基础", "变量": "基础", "数据类型": "基础", "字符串": "基础",
            "数字": "基础", "布尔值": "基础", "变量与运算符": "基础", "控制流": "控制流", "循环": "控制流", "循环语句": "控制流",
            "条件语句": "控制流", "函数": "函数", "函数定义": "函数", "函数调用": "函数",
            "列表": "数据结构", "元组": "数据结构", "字典": "数据结构", "集合": "数据结构",
            "索引": "数据结构", "切片": "数据结构", "算术运算": "运算", "逻辑运算": "运算",
            "比较运算": "运算", "调试": "调试", "异常处理": "调试", "文件操作": "文件",
            "模块": "模块", "面向对象": "高级", "类": "高级", "继承": "高级",
        }
        
        # 为每个学生获取知识图谱数据，直接使用学生知识图谱API的结果
        all_pre_stats = {}  # 存储每个学生的pre_recommend_stats（直接使用）
        all_post_stats = {}  # 存储每个学生的post_recommend_stats（直接使用）
        all_knowledge_stats = {}  # 累加所有学生的knowledge_stats
        student_count = 0  # 有数据的学生数量
        
        for student in students:
            # 使用内部函数获取学生的知识图谱数据，确保逻辑与学生端API一致
            student_data = get_student_knowledge_stats(student.id, session_db)
            
            if student_data:
                has_data = False
                
                # 直接使用学生的pre_recommend_stats
                if student_data.get('pre_recommend_stats') and len(student_data['pre_recommend_stats']) > 0:
                    for tag, stats in student_data['pre_recommend_stats'].items():
                        if tag not in all_pre_stats:
                            all_pre_stats[tag] = {'total': 0, 'correct': 0}
                        all_pre_stats[tag]['total'] += stats['total']
                        all_pre_stats[tag]['correct'] += stats['correct']
                    has_data = True
                
                # 直接使用学生的post_recommend_stats
                if student_data.get('post_recommend_stats') and len(student_data['post_recommend_stats']) > 0:
                    for tag, stats in student_data['post_recommend_stats'].items():
                        if tag not in all_post_stats:
                            all_post_stats[tag] = {'total': 0, 'correct': 0}
                        all_post_stats[tag]['total'] += stats['total']
                        all_post_stats[tag]['correct'] += stats['correct']
                    has_data = True
                
                # 累加每个学生的knowledge_stats
                if student_data.get('knowledge_stats'):
                    for tag, stats in student_data['knowledge_stats'].items():
                        if tag not in all_knowledge_stats:
                            all_knowledge_stats[tag] = {'total': 0, 'correct': 0}
                        all_knowledge_stats[tag]['total'] += stats['total']
                        all_knowledge_stats[tag]['correct'] += stats['correct']
                    has_data = True
                
                if has_data:
                    student_count += 1

        # 直接使用累加后的pre_recommend_stats
        pre_recommend_stats = {}
        for tag, stats in all_pre_stats.items():
            language = tag.split('-')[0] if '-' in tag else 'Python'
            core_tag = '-'.join(tag.split('-')[1:]) if '-' in tag else tag
            pre_recommend_stats[tag] = {
                'total': stats['total'],
                'correct': stats['correct'],
                'category': category_map.get(core_tag, '其他'),
                'language': language
            }
        
        # 直接使用累加后的post_recommend_stats
        post_recommend_stats = {}
        for tag, stats in all_post_stats.items():
            language = tag.split('-')[0] if '-' in tag else 'Python'
            core_tag = '-'.join(tag.split('-')[1:]) if '-' in tag else tag
            post_recommend_stats[tag] = {
                'total': stats['total'],
                'correct': stats['correct'],
                'category': category_map.get(core_tag, '其他'),
                'language': language
            }
        
        # 计算整体knowledge_stats（累加所有学生的数据）
        knowledge_stats = {}
        for tag, stats in all_knowledge_stats.items():
            core_tag = '-'.join(tag.split('-')[1:]) if '-' in tag else tag
            knowledge_stats[tag] = {
                'total': stats['total'],
                'correct': stats['correct'],
                'category': category_map.get(core_tag, '其他')
            }

        # 生成节点数据（使用pre_recommend_stats，与学生端保持一致）
        nodes = []
        node_id = 1
        for name, stats in pre_recommend_stats.items():
            # 计算掌握率（使用推荐前的统计数据）
            mastery_rate = stats['correct'] / stats['total'] if stats['total'] > 0 else 0.5
            
            # 根据掌握率设置颜色
            if mastery_rate > 0.7:
                color = "#67C23A"  # 绿色 - 掌握良好
            elif mastery_rate >= 0.4:
                color = "#E6A23C"  # 黄色 - 需巩固
            else:
                color = "#F56C6C"  # 红色 - 薄弱
            
            nodes.append({
                "id": node_id,
                "name": name,
                "value": mastery_rate,
                "color": color,
                "category": stats['category'],
                "total": stats['total'],
                "correct": stats['correct']
            })
            node_id += 1

        # 生成节点之间的连接关系
        links = []
        categories = list(set([n['category'] for n in nodes]))
        for i, cat1 in enumerate(categories):
            for cat2 in categories[i+1:]:
                cat1_nodes = [n for n in nodes if n['category'] == cat1]
                cat2_nodes = [n for n in nodes if n['category'] == cat2]
                if cat1_nodes and cat2_nodes:
                    links.append({
                        "source": cat1_nodes[0]['id'],
                        "target": cat2_nodes[0]['id'],
                        "value": 1
                    })

        # 统计掌握状态分布
        good_count = sum(1 for n in nodes if n['value'] > 0.7)
        medium_count = sum(1 for n in nodes if 0.4 <= n['value'] <= 0.7)
        weak_count = sum(1 for n in nodes if n['value'] < 0.4)

        return jsonify({
            "success": True,
            "nodes": nodes,
            "links": links,
            "class_name": class_name,
            "submission_count": len(result),
            "knowledge_stats": knowledge_stats,
            "good_count": good_count,
            "medium_count": medium_count,
            "weak_count": weak_count,
            "pre_recommend_stats": pre_recommend_stats,
            "post_recommend_stats": post_recommend_stats
        })
    except Exception as e:
        print(f"获取班级知识图谱失败: {e}")
        return jsonify({
            "success": False,
            "error": f"获取班级知识图谱失败: {str(e)}"
        }), 500
    finally:
        if session_db:
            session_db.close()

@app.route('/api/knowledge_map/<int:student_id>', methods=['GET'])
def get_knowledge_map(student_id):
    """获取学生知识图谱数据"""
    session_db = None
    try:
        session_db = Session()

        # 尝试根据 id 查找学生（教师端传递的是 id）
        student_by_id = session_db.query(Student).filter_by(id=student_id).first()
        # 尝试根据 user_id 查找学生（学生端传递的是 user_id）
        student_by_user_id = session_db.query(Student).filter_by(user_id=student_id).first()
        
        # 逻辑：
        # 1. 如果根据 id 找到了学生，选择该学生（教师端传递的是 id）
        # 2. 如果根据 user_id 找到了学生，选择该学生（学生端传递的是 user_id）
        # 3. 如果都找不到，返回 None
        if student_by_id:
            student = student_by_id
        elif student_by_user_id:
            student = student_by_user_id
        else:
            student = None
        if not student:
            default_knowledge = ["基础语法", "变量", "数据类型", "控制流", "循环", "条件语句", "函数", "列表", "调试"]
            knowledge_stats = {}
            category_map = {
            "基础语法": "基础", "变量": "基础", "数据类型": "基础", "字符串": "基础",
            "数字": "基础", "布尔值": "基础", "变量与运算符": "基础", "控制流": "控制流", "循环": "控制流", "循环语句": "控制流",
            "条件语句": "控制流", "函数": "函数", "函数定义": "函数", "函数调用": "函数",
            "列表": "数据结构", "元组": "数据结构", "字典": "数据结构", "集合": "数据结构",
            "索引": "数据结构", "切片": "数据结构", "算术运算": "运算", "逻辑运算": "运算",
            "比较运算": "运算", "调试": "调试", "异常处理": "调试", "文件操作": "文件",
            "模块": "模块", "面向对象": "高级", "类": "高级", "继承": "高级",
        }
            for tag in default_knowledge:
                knowledge_stats[tag] = {'total': 0, 'correct': 0, 'category': category_map.get(tag, '其他')}

            nodes = []
            node_id = 1
            for name, stats in knowledge_stats.items():
                nodes.append({
                    "id": node_id,
                    "name": name,
                    "value": 0.5,
                    "color": "#FFC107",
                    "category": stats['category'],
                    "total": 0,
                    "correct": 0
                })
                node_id += 1

            links = []
            categories = list(set([n['category'] for n in nodes]))
            for i, cat1 in enumerate(categories):
                for cat2 in categories[i+1:]:
                    if cat1 == "基础" or cat2 == "基础":
                        cat1_nodes = [n for n in nodes if n['category'] == cat1]
                        cat2_nodes = [n for n in nodes if n['category'] == cat2]
                        if cat1_nodes and cat2_nodes:
                            links.append({
                                "source": cat1_nodes[0]['id'],
                                "target": cat2_nodes[0]['id'],
                                "value": 1
                            })

            return jsonify({
                "success": True,
                "nodes": nodes,
                "links": links,
                "student_id": student_id,
                "submission_count": 0,
                "knowledge_stats": knowledge_stats,
                "pre_recommend_stats": {},
                "post_recommend_stats": {}
            })

        from sqlalchemy import text
        # 同时获取提交记录
        result = session_db.execute(
            text("""
            SELECT hs.id, hs.student_id, hs.problem_id, hs.code_content, hs.ai_feedback, hs.submission_time 
            FROM homework_submissions hs
            WHERE hs.student_id = :student_id 
            ORDER BY hs.submission_time DESC
            """),
            {"student_id": student.id}
        )

        submissions = []
        for row in result:
            class Submission:
                def __init__(self, id, student_id, problem_id, code_content, ai_feedback, submission_time):
                    self.id = id
                    self.student_id = student_id
                    self.problem_id = problem_id
                    self.code_content = code_content
                    self.ai_feedback = ai_feedback
                    # 确保submission_time是datetime类型
                    if isinstance(submission_time, str):
                        from datetime import datetime
                        try:
                            self.submission_time = datetime.strptime(submission_time, '%Y-%m-%d %H:%M:%S')
                        except:
                            self.submission_time = datetime.now()
                    else:
                        self.submission_time = submission_time
                    # 实时查询当前题目的分类，确保使用最新的分类
                    problem = session_db.query(Problem).filter_by(id=problem_id).first()
                    self.category = problem.category if problem else None
            submissions.append(Submission(*row))

        # 获取学生的推荐记录，提取推荐的知识点
        recommended_knowledge = set()
        try:
            # 获取学生的所有推荐记录
            recommends = session_db.query(AIRecommendedHomework).filter(
                AIRecommendedHomework.student_id == student.id
            ).all()
            
            # 提取所有推荐过的知识点
            for recommend in recommends:
                if recommend.knowledge_topics:
                    try:
                        knowledge_topics = json.loads(recommend.knowledge_topics)
                        if isinstance(knowledge_topics, list):
                            for problem_number in knowledge_topics:
                                # problem_number 是题目编号，需要从 problems 表中获取知识点名称
                                problem = session_db.query(Problem).filter(
                                    Problem.problem_number == problem_number
                                ).first()
                                if problem and problem.category:
                                    # 提取核心知识点名称（去掉语言前缀）
                                    topic = problem.category
                                    if '-' in topic:
                                        # 从第二个元素开始，因为第一个是语言
                                        core_topic = '-'.join(topic.split('-')[1:])
                                    else:
                                        core_topic = topic
                                    recommended_knowledge.add(core_topic)
                    except Exception as e:
                        print(f"解析推荐知识点失败: {str(e)}")
                        pass
        except Exception as e:
            print(f"获取推荐知识点失败: {str(e)}")

        # 获取学生的第一次推荐时间
        first_recommend_time = None
        try:
            first_recommend = session_db.query(AIRecommendedHomework).filter(
                AIRecommendedHomework.student_id == student.id
            ).order_by(AIRecommendedHomework.generated_at).first()
            if first_recommend:
                first_recommend_time = first_recommend.generated_at
        except Exception as e:
            print(f"获取推荐时间失败: {str(e)}")
            first_recommend_time = None

        knowledge_stats = {}
        pre_recommend_stats = {}
        post_recommend_stats = {}
        category_map = {
            "基础语法": "基础", "变量": "基础", "数据类型": "基础", "字符串": "基础",
            "数字": "基础", "布尔值": "基础", "输入输出": "基础", "变量与运算符": "基础", "控制流": "控制流", "循环": "控制流", "循环语句": "控制流",
            "条件语句": "控制流", "函数": "函数", "函数定义": "函数", "函数调用": "函数",
            "列表": "数据结构", "元组": "数据结构", "字典": "数据结构", "集合": "数据结构",
            "索引": "数据结构", "切片": "数据结构", "算术运算": "运算", "逻辑运算": "运算",
            "比较运算": "运算", "调试": "调试", "异常处理": "调试", "文件操作": "文件",
            "模块": "模块", "面向对象": "高级", "类": "高级", "继承": "高级",
        }

        for submission in submissions:
            if submission.ai_feedback:
                try:
                    feedback_dict = json.loads(submission.ai_feedback)
                    is_correct = feedback_dict.get('is_correct', False)

                    # 优先使用题目当前的分类作为知识点标签
                    if submission.category:
                        tag = submission.category
                        # 保留完整的标签（包含语言前缀）
                        full_tag = tag
                        
                        # 提取核心知识点名称
                        if '-' in tag:
                            # 从第二个元素开始，因为第一个是语言
                            core_tag = '-'.join(tag.split('-')[1:])
                        else:
                            core_tag = tag
                        
                        # 统计整体数据
                        if full_tag not in knowledge_stats:
                            knowledge_stats[full_tag] = {'total': 0, 'correct': 0, 'category': category_map.get(core_tag, '其他'), 'language': tag.split('-')[0] if '-' in tag else '未知'}
                        knowledge_stats[full_tag]['total'] += 1
                        if is_correct:
                            knowledge_stats[full_tag]['correct'] += 1
                        
                        # 统计推荐前数据 - 包含所有提交记录（不考虑推荐时间）
                        if full_tag not in pre_recommend_stats:
                            pre_recommend_stats[full_tag] = {'total': 0, 'correct': 0, 'category': category_map.get(core_tag, '其他'), 'language': tag.split('-')[0] if '-' in tag else '未知'}
                        pre_recommend_stats[full_tag]['total'] += 1
                        if is_correct:
                            pre_recommend_stats[full_tag]['correct'] += 1
                        
                        # 统计推荐后数据 - 只有被推荐过的知识点且在推荐后提交的才统计
                        if first_recommend_time and submission.submission_time >= first_recommend_time:
                            # 检查该知识点是否被推荐过
                            if core_tag in recommended_knowledge:
                                if full_tag not in post_recommend_stats:
                                    post_recommend_stats[full_tag] = {'total': 0, 'correct': 0, 'category': category_map.get(core_tag, '其他'), 'language': tag.split('-')[0] if '-' in tag else '未知'}
                                post_recommend_stats[full_tag]['total'] += 1
                                if is_correct:
                                    post_recommend_stats[full_tag]['correct'] += 1
                    # 如果题目分类为空，从ai_feedback中的knowledge_tags获取
                    elif 'knowledge_tags' in feedback_dict:
                        for tag in feedback_dict['knowledge_tags']:
                            # 保留完整的标签（包含语言前缀）
                            full_tag = tag
                            
                            # 提取核心知识点名称
                            if '-' in tag:
                                # 从第二个元素开始，因为第一个是语言
                                core_tag = '-'.join(tag.split('-')[1:])
                            else:
                                core_tag = tag
                            
                            # 统计整体数据
                            if full_tag not in knowledge_stats:
                                knowledge_stats[full_tag] = {'total': 0, 'correct': 0, 'category': category_map.get(core_tag, '其他'), 'language': tag.split('-')[0] if '-' in tag else '未知'}
                            knowledge_stats[full_tag]['total'] += 1
                            if is_correct:
                                knowledge_stats[full_tag]['correct'] += 1
                            
                            # 统计推荐前数据 - 包含所有提交记录（不考虑推荐时间）
                            if full_tag not in pre_recommend_stats:
                                pre_recommend_stats[full_tag] = {'total': 0, 'correct': 0, 'category': category_map.get(core_tag, '其他'), 'language': tag.split('-')[0] if '-' in tag else '未知'}
                            pre_recommend_stats[full_tag]['total'] += 1
                            if is_correct:
                                pre_recommend_stats[full_tag]['correct'] += 1
                            
                            # 统计推荐后数据 - 只有被推荐过的知识点且在推荐后提交的才统计
                            if first_recommend_time and submission.submission_time >= first_recommend_time:
                                # 检查该知识点是否被推荐过
                                if core_tag in recommended_knowledge:
                                    if full_tag not in post_recommend_stats:
                                        post_recommend_stats[full_tag] = {'total': 0, 'correct': 0, 'category': category_map.get(core_tag, '其他'), 'language': tag.split('-')[0] if '-' in tag else '未知'}
                                    post_recommend_stats[full_tag]['total'] += 1
                                    if is_correct:
                                        post_recommend_stats[full_tag]['correct'] += 1
                except json.JSONDecodeError:
                    pass

        # 从新表中读取推荐前的掌握率
        for name, stats in knowledge_stats.items():
            # 提取核心知识点名称
            if '-' in name:
                core_topic = '-'.join(name.split('-')[1:])
            else:
                core_topic = name
            
            # 从新表中查询推荐前的掌握率
            from sqlalchemy import text
            pre_recommend_record = session_db.execute(
                text('''
                    SELECT pre_recommend_mastery FROM knowledge_recommendation_status 
                    WHERE student_id = :student_id AND knowledge_name = :knowledge_name
                '''), 
                {'student_id': student.id, 'knowledge_name': core_topic}
            ).fetchone()
            
            if pre_recommend_record:
                # 使用新表中的推荐前掌握率
                mastery_rate = pre_recommend_record[0]
                # 计算总提交数和正确数（保持与掌握率一致）
                total = 10  # 假设总提交数为10
                correct = int(total * mastery_rate)
                pre_recommend_stats[name] = {
                    'total': total, 
                    'correct': correct, 
                    'category': stats['category'], 
                    'language': stats['language']
                }
            else:
                # 如果没有推荐前数据，使用所有提交记录
                if name not in pre_recommend_stats:
                    pre_recommend_stats[name] = {
                        'total': 0, 
                        'correct': 0, 
                        'category': stats['category'], 
                        'language': stats['language']
                    }

        # 只统计实际提交的知识点，不添加默认知识点
        if not knowledge_stats:
            # 如果没有提交记录，返回空的节点和链接
            return jsonify({
                "success": True,
                "nodes": [],
                "links": [],
                "student_id": student_id,
                "submission_count": len(submissions),
                "knowledge_stats": {},
                "pre_recommend_stats": {},
                "post_recommend_stats": {}
            })

        nodes = []
        node_id = 1
        for name, stats in knowledge_stats.items():
            if stats['total'] > 0:
                mastery_rate = stats['correct'] / stats['total']
            else:
                mastery_rate = 0.5

            if mastery_rate >= 0.7:
                color = "#4CAF50"
            elif mastery_rate >= 0.4:
                color = "#FFC107"
            else:
                color = "#F44336"

            nodes.append({
                "id": node_id,
                "name": name,
                "value": round(mastery_rate, 2),
                "color": color,
                "category": stats['category'],
                "total": stats['total'],
                "correct": stats['correct']
            })
            node_id += 1

        links = []
        categories = list(set([n['category'] for n in nodes]))
        for i, cat1 in enumerate(categories):
            for cat2 in categories[i+1:]:
                if cat1 == "基础" or cat2 == "基础":
                    cat1_nodes = [n for n in nodes if n['category'] == cat1]
                    cat2_nodes = [n for n in nodes if n['category'] == cat2]
                    if cat1_nodes and cat2_nodes:
                        links.append({
                            "source": cat1_nodes[0]['id'],
                            "target": cat2_nodes[0]['id'],
                            "value": 1
                        })

        return jsonify({
            "success": True,
            "nodes": nodes,
            "links": links,
            "student_id": student_id,
            "submission_count": len(submissions),
            "knowledge_stats": knowledge_stats,
            "pre_recommend_stats": pre_recommend_stats,
            "post_recommend_stats": post_recommend_stats
        })
    except Exception as e:
        print(f"获取知识图谱失败: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": f"获取知识图谱失败: {str(e)}"
        }), 500
    finally:
        if session_db:
            session_db.close()

def init_default_teacher():
    """初始化默认教师账户"""
    try:
        session_db = Session()
        try:
            existing_teacher = session_db.query(Teacher).filter_by(username='teacher').first()
            if not existing_teacher:
                from werkzeug.security import generate_password_hash
                teacher = Teacher(
                    username='teacher',
                    password=generate_password_hash('teacher123'),
                    email='teacher@example.com'
                )
                session_db.add(teacher)
                session_db.commit()
                print("教师账户已创建")
            else:
                print("教师账户已存在")
        finally:
            session_db.close()
    except Exception as e:
        print(f"初始化教师账户失败: {e}")

# 数据库备份相关接口
import os
import shutil
from flask import send_file

@app.route('/api/backup/database', methods=['GET'])
def backup_database():
    """备份数据库"""
    try:
        # 确保备份目录存在
        backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        # 源数据库文件
        db_file = os.path.join(os.path.dirname(__file__), 'learning_analysis.db')
        
        # 生成备份文件名
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'learning_analysis_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_filename)

        # 复制数据库文件
        shutil.copy2(db_file, backup_path)

        # 返回备份文件
        return send_file(backup_path, as_attachment=True, download_name=backup_filename)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"备份失败: {str(e)}"
        }), 500

@app.route('/api/backup/history', methods=['GET'])
def get_backup_history():
    """获取备份历史"""
    try:
        backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        backups = []
        for filename in os.listdir(backup_dir):
            if filename.endswith('.db'):
                file_path = os.path.join(backup_dir, filename)
                stat = os.stat(file_path)
                backups.append({
                    'filename': filename,
                    'size': f"{stat.st_size / 1024:.2f} KB",
                    'timestamp': datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })

        # 按时间倒序排序
        backups.sort(key=lambda x: x['timestamp'], reverse=True)

        return jsonify({
            "success": True,
            "backups": backups
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取备份历史失败: {str(e)}"
        }), 500

@app.route('/api/problems/categories', methods=['GET'])
def get_problem_categories():
    """获取所有题目分类"""
    try:
        session_db = Session()
        try:
            # 查询所有不重复的分类
            categories = session_db.query(Problem.category).distinct().filter(Problem.category.isnot(None)).filter(Problem.category != '').all()
            category_list = [cat[0] for cat in categories]
            return jsonify({
                "success": True,
                "categories": category_list
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取分类失败: {str(e)}"
        }), 500

@app.route('/api/problems/export', methods=['GET'])
def export_problems():
    """导出题目为Excel文件"""
    try:
        session_db = Session()
        try:
            # 查询所有题目
            problems = session_db.query(Problem).all()
            
            # 准备导出数据
            data = []
            for problem in problems:
                data.append({
                    'ID': problem.id,
                    '题目号': problem.problem_number,
                    '标题': problem.title,
                    '题目描述': problem.description,
                    '输入描述': problem.input_description,
                    '输出描述': problem.output_description,
                    '样例输入': problem.sample_input,
                    '样例输出': problem.sample_output,
                    '分类': problem.category,
                    '必需函数': problem.required_functions,
                    '难度等级': problem.difficulty
                })
            
            # 创建DataFrame
            df = pd.DataFrame(data)
            
            # 创建Excel文件
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='题目', index=False)
            output.seek(0)
            
            # 发送文件
            return send_file(output, as_attachment=True, download_name=f'problems_{datetime.datetime.now().strftime("%Y%m%d")}.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        finally:
            session_db.close()
    except Exception as e:
        print(f"导出题目失败: {e}")
        return jsonify({
            "success": False,
            "error": f"导出题目失败: {str(e)}"
        }), 500

@app.route('/api/problems/import', methods=['POST'])
def import_problems():
    """从Excel文件导入题目"""
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "请选择要导入的Excel文件"
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "请选择要导入的Excel文件"
            }), 400
        
        # 检查文件类型
        if not file.filename.endswith('.xlsx') and not file.filename.endswith('.xls'):
            return jsonify({
                "success": False,
                "error": "请选择Excel文件(.xlsx或.xls)"
            }), 400
        
        # 读取Excel文件
        try:
            df = pd.read_excel(file)
        except Exception as e:
            print(f"读取Excel文件失败: {e}")
            return jsonify({
                "success": False,
                "error": f"读取Excel文件失败: {str(e)}"
            }), 400
        
        # 检查必要的列
        required_columns = ['标题', '题目描述', '输入描述', '输出描述', '样例输入', '样例输出', '分类']
        for col in required_columns:
            if col not in df.columns:
                return jsonify({
                    "success": False,
                    "error": f"Excel文件缺少必要的列: {col}"
                }), 400
        
        session_db = Session()
        try:
            imported_count = 0
            skipped_count = 0
            
            # 获取当前最大的题目号
            max_problem_number = session_db.query(sa.func.max(Problem.problem_number)).scalar() or 0
            next_problem_number = max_problem_number + 1
            
            for index, row in df.iterrows():
                # 检查题目是否已存在
                existing_problem = session_db.query(Problem).filter_by(title=row['标题']).first()
                if existing_problem:
                    skipped_count += 1
                    continue  # 跳过已存在的题目
                
                # 从分类中提取语言（如果分类格式为"语言-知识点"）
                language = None
                category = row['分类']
                if category and '-' in category:
                    language_part = category.split('-')[0]
                    language_map = {
                        'Python': 'python', 'C': 'c', 'C++': 'cpp', 'Java': 'java', 'Go': 'go'
                    }
                    if language_part in language_map:
                        language = language_map[language_part]
                
                # 确定题目号
                problem_number = next_problem_number
                if '题目号' in row and pd.notna(row['题目号']):
                    # 使用导入的题目号
                    problem_number = int(row['题目号'])
                    # 更新next_problem_number为较大的值
                    if problem_number >= next_problem_number:
                        next_problem_number = problem_number + 1
                else:
                    # 使用自动生成的题目号
                    problem_number = next_problem_number
                    next_problem_number += 1
                
                # 检查题目号是否已存在
                existing_problem_by_number = session_db.query(Problem).filter_by(problem_number=problem_number).first()
                if existing_problem_by_number:
                    skipped_count += 1
                    continue  # 跳过题目号已存在的题目
                
                # 获取必需函数（如果存在）
                required_functions = row.get('必需函数', '')
                if pd.isna(required_functions):
                    required_functions = '[]'
                
                # 获取难度等级（如果存在）
                difficulty = row.get('难度等级', '')
                if pd.isna(difficulty):
                    difficulty = '入门'
                
                # 创建新题目
                problem = Problem(
                    problem_number=problem_number,
                    title=row['标题'],
                    description=row['题目描述'],
                    input_description=row['输入描述'],
                    output_description=row['输出描述'],
                    sample_input=row['样例输入'],
                    sample_output=row['样例输出'],
                    category=category,
                    language=language,
                    required_functions=required_functions,
                    difficulty=difficulty
                )
                session_db.add(problem)
                imported_count += 1
            
            session_db.commit()
            
            return jsonify({
                "success": True,
                "imported": imported_count,
                "skipped": skipped_count,
                "message": f"成功导入 {imported_count} 道题目，跳过 {skipped_count} 道已存在的题目"
            })
        finally:
            session_db.close()
    except Exception as e:
        print(f"导入题目失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"导入题目失败: {str(e)}"
        }), 500

@app.route('/api/students/<int:student_id>/completed-problems', methods=['GET'])
def get_completed_problems(student_id):
    """获取学生已完成的题目列表"""
    try:
        session_db = Session()
        try:
            # 首先通过user_id查询对应的student对象
            student = session_db.query(Student).filter_by(user_id=student_id).first()
            if not student:
                return jsonify({
                    "success": True,
                    "completed_problem_ids": []
                })
            
            # 查询学生的提交记录，获取已完成的题目
            completed_submissions = session_db.query(HomeworkSubmission).filter(
                HomeworkSubmission.student_id == student.id,
                HomeworkSubmission.ai_feedback.contains('"is_correct": true'),
                HomeworkSubmission.problem_id.isnot(None)
            ).distinct(HomeworkSubmission.problem_id).all()
            
            completed_problem_ids = [submission.problem_id for submission in completed_submissions]
            
            return jsonify({
                "success": True,
                "completed_problem_ids": completed_problem_ids
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取已完成题目失败: {str(e)}"
        }), 500

# ==================== 作业与测验 API ====================

@app.route('/api/homeworks', methods=['GET'])
def get_homeworks():
    """获取作业与测验列表，支持按学生班级过滤"""
    try:
        session_db = Session()
        try:
            # 获取学生ID参数（学生端调用时会传）
            student_id = request.args.get('student_id')
            
            if student_id:
                # 学生端调用，根据学生班级过滤作业
                student = session_db.query(Student).filter_by(id=student_id).first()
                if not student:
                    return jsonify({
                        "success": False,
                        "error": "学生不存在"
                    }), 400
                
                student_class = student.class_name
                
                # 查询作业：class_name为空（所有班级可见）或包含学生班级
                homeworks = session_db.query(Homework).all()
                
                # 过滤作业
                filtered_homeworks = []
                for h in homeworks:
                    if not h.class_name:
                        # 没有设置班级限制，所有班级都可见
                        filtered_homeworks.append(h)
                    else:
                        # 检查学生班级是否在作业的班级列表中
                        class_list = [c.strip() for c in h.class_name.split(',')]
                        if student_class in class_list:
                            filtered_homeworks.append(h)
                
                homeworks = filtered_homeworks
            else:
                # 教师端调用，返回所有作业
                homeworks = session_db.query(Homework).all()
            
            homework_list = []
            for h in homeworks:
                homework_list.append({
                    "id": h.id,
                    "title": h.title,
                    "type": h.type,
                    "language": h.language,
                    "class_name": h.class_name,
                    "problem_numbers": h.problem_numbers,
                    "problem_scores": h.problem_scores,
                    "start_time": h.start_time.isoformat() if h.start_time else None,
                    "end_time": h.end_time.isoformat() if h.end_time else None
                })
            return jsonify({
                "success": True,
                "homeworks": homework_list
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取作业列表失败: {str(e)}"
        }), 500

@app.route('/api/homeworks', methods=['POST'])
def add_homework():
    """添加作业与测验"""
    try:
        data = request.json
        if not data or not data.get('title'):
            return jsonify({
                "success": False,
                "error": "作业标题不能为空"
            }), 400

        session_db = Session()
        try:
            # 计算自动编号
            max_homework = session_db.query(Homework).order_by(Homework.id.desc()).first()
            homework_id = (max_homework.id + 1) if max_homework else 1

            # 处理班级字段，前端传过来的是数组，转换为逗号分隔的字符串
            class_name = data.get('class_name', [])
            class_name_str = ','.join(class_name) if isinstance(class_name, list) else str(class_name)
            
            homework = Homework(
                id=homework_id,
                title=data['title'],
                type=data.get('type', 'homework'),
                language=data.get('language', ''),
                class_name=class_name_str,
                problem_numbers=data.get('problem_numbers', ''),
                problem_scores=data.get('problem_scores', ''),
                start_time=datetime.datetime.fromisoformat(data['start_time'].replace('Z', '+00:00')) if data.get('start_time') else None,
                end_time=datetime.datetime.fromisoformat(data['end_time'].replace('Z', '+00:00')) if data.get('end_time') else None
            )
            session_db.add(homework)
            session_db.commit()

            return jsonify({
                "success": True,
                "message": "作业添加成功",
                "homework": {
                    "id": homework.id,
                    "title": homework.title
                }
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"添加作业失败: {str(e)}"
        }), 500

@app.route('/api/homeworks/<int:homework_id>', methods=['PUT'])
def update_homework(homework_id):
    """更新作业与测验"""
    try:
        data = request.json
        if not data:
            return jsonify({
                "success": False,
                "error": "请求数据不能为空"
            }), 400

        session_db = Session()
        try:
            homework = session_db.query(Homework).filter_by(id=homework_id).first()
            if not homework:
                return jsonify({
                    "success": False,
                    "error": "作业不存在"
                }), 404

            # 更新作业信息
            if 'title' in data:
                homework.title = data['title']
            if 'type' in data:
                homework.type = data['type']
            if 'language' in data:
                homework.language = data['language']
            if 'class_name' in data:
                # 处理班级字段，前端传过来的是数组，转换为逗号分隔的字符串
                class_name = data['class_name']
                homework.class_name = ','.join(class_name) if isinstance(class_name, list) else str(class_name)
            if 'problem_numbers' in data:
                homework.problem_numbers = data['problem_numbers']
            if 'problem_scores' in data:
                homework.problem_scores = data['problem_scores']
            if 'start_time' in data:
                if data['start_time']:
                    try:
                        # 尝试解析ISO格式
                        homework.start_time = datetime.datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
                    except ValueError:
                        # 尝试解析'YYYY/MM/DD HH:MM'格式
                        try:
                            homework.start_time = datetime.datetime.strptime(data['start_time'], '%Y/%m/%d %H:%M')
                        except ValueError:
                            # 尝试解析'YYYY/MM/DD HH:MM:SS'格式
                            homework.start_time = datetime.datetime.strptime(data['start_time'], '%Y/%m/%d %H:%M:%S')
                else:
                    homework.start_time = None
            if 'end_time' in data:
                if data['end_time']:
                    try:
                        # 尝试解析ISO格式
                        homework.end_time = datetime.datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
                    except ValueError:
                        # 尝试解析'YYYY/MM/DD HH:MM'格式
                        try:
                            homework.end_time = datetime.datetime.strptime(data['end_time'], '%Y/%m/%d %H:%M')
                        except ValueError:
                            # 尝试解析'YYYY/MM/DD HH:MM:SS'格式
                            homework.end_time = datetime.datetime.strptime(data['end_time'], '%Y/%m/%d %H:%M:%S')
                else:
                    homework.end_time = None

            session_db.commit()

            return jsonify({
                "success": True,
                "message": "作业更新成功"
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"更新作业失败: {str(e)}"
        }), 500

@app.route('/api/homeworks/<int:homework_id>', methods=['DELETE'])
def delete_homework(homework_id):
    """删除作业与测验"""
    try:
        session_db = Session()
        try:
            homework = session_db.query(Homework).filter_by(id=homework_id).first()
            if not homework:
                return jsonify({
                    "success": False,
                    "error": "作业不存在"
                }), 404

            session_db.delete(homework)
            session_db.commit()

            return jsonify({
                "success": True,
                "message": "作业删除成功"
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"删除作业失败: {str(e)}"
        }), 500

@app.route('/api/homeworks/<int:homework_id>/scores', methods=['GET'])
def get_homework_scores(homework_id):
    """获取作业的学生成绩数据"""
    try:
        session_db = Session()
        try:
            # 获取作业信息
            homework = session_db.query(Homework).filter_by(id=homework_id).first()
            if not homework:
                return jsonify({
                    "success": False,
                    "error": "作业不存在"
                }), 404
            
            # 解析题目编号和分数
            problem_numbers = [n.strip() for n in homework.problem_numbers.split(',')] if homework.problem_numbers else []
            problem_scores_list = [int(s.strip()) for s in homework.problem_scores.split(',')] if homework.problem_scores else []
            
            # 如果没有指定分数，默认平均分配
            if not problem_scores_list and problem_numbers:
                avg_score = 100 // len(problem_numbers)
                problem_scores_list = [avg_score] * len(problem_numbers)
            
            # 获取作业指定的班级
            target_classes = []
            if homework.class_name:
                target_classes = [c.strip() for c in homework.class_name.split(',')]
            
            # 查询学生列表
            if target_classes:
                students = session_db.query(Student).filter(Student.class_name.in_(target_classes)).all()
            else:
                students = session_db.query(Student).all()
            
            # 构建成绩数据
            scores_data = []
            
            for student in students:
                student_scores = {
                    'student_id': student.student_id,
                    'student_name': student.name,
                    'class_name': student.class_name or '',
                    'scores': [],
                    'total_score': 0
                }
                
                # 获取该学生在该作业每道题上的最高得分
                for idx, problem_num in enumerate(problem_numbers):
                    try:
                        problem_id = int(problem_num)
                        max_score = problem_scores_list[idx] if idx < len(problem_scores_list) else 0
                        
                        # 查询该学生该题目的所有提交记录，按提交时间降序排列
                        submissions = session_db.query(HomeworkSubmission).filter(
                            HomeworkSubmission.student_id == student.id,
                            HomeworkSubmission.problem_id == problem_id,
                            HomeworkSubmission.is_homework_submission == True
                        ).order_by(HomeworkSubmission.submission_time.desc()).all()
                        
                        # 计算该题得分（从AI反馈中获取score字段）
                        problem_score = 0
                        for submission in submissions:
                            if submission.ai_feedback:
                                try:
                                    feedback = json.loads(submission.ai_feedback)
                                    if feedback.get('is_correct'):
                                        # 如果有score字段，使用score计算得分比例
                                        if 'score' in feedback:
                                            score_ratio = feedback['score'] / 100
                                            problem_score = int(max_score * score_ratio)
                                        else:
                                            problem_score = max_score
                                        break
                                except (json.JSONDecodeError, ValueError):
                                    # 如果解析失败，检查是否包含通过关键词
                                    if '通过' in submission.ai_feedback or '正确' in submission.ai_feedback or '✓' in submission.ai_feedback:
                                        problem_score = max_score
                                        break
                        
                        student_scores['scores'].append(problem_score)
                    except ValueError:
                        student_scores['scores'].append(0)
                
                # 计算总分
                student_scores['total_score'] = sum(student_scores['scores'])
                scores_data.append(student_scores)
            
            # 按总分降序排序
            scores_data.sort(key=lambda x: x['total_score'], reverse=True)
            
            return jsonify({
                "success": True,
                "scores": scores_data,
                "problem_count": len(problem_numbers)
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取作业成绩失败: {str(e)}"
        }), 500

def get_student_error_summary(session_db, student_id, knowledge_topic):
    """获取学生在特定知识点上的错误总结，包括每个错题的详细信息（用于错一题生成一题）"""
    try:
        
        # 获取学生在该知识点相关题目上的首次错误提交记录（去重，每个题目只取第一次错误）
        from sqlalchemy import text
        results = session_db.execute(
            text('''
                SELECT hs.ai_feedback, p.category, p.difficulty, p.required_functions, p.problem_number, p.title
                FROM homework_submissions hs
                LEFT JOIN problems p ON hs.problem_id = p.id
                WHERE hs.student_id = :student_id
                AND (p.category LIKE :topic_pattern OR p.category IS NULL)
                ORDER BY hs.problem_id, hs.submission_time ASC
            '''),
            {'student_id': student_id, 'topic_pattern': f'%{knowledge_topic}%'}
        )
        
        error_info = []
        difficulties = []
        require_custom_functions = []
        seen_problems = set()  # 用于去重，记录已经处理过的题目ID
        
        for row in results:
            ai_feedback = row[0]
            difficulty = row[2]
            required_functions = row[3]
            problem_number = row[4]
            problem_title = row[5]
            
            # 跳过已经处理过的题目（只处理每个题目的第一次错误）
            if problem_number and problem_number in seen_problems:
                continue
            
            if ai_feedback:
                try:
                    feedback_dict = json.loads(ai_feedback)
                    # 提取错误相关信息
                    if 'error_type' in feedback_dict and feedback_dict.get('error_type') != '无错误':
                        error_entry = {
                            'error_type': feedback_dict.get('error_type', ''),
                            'hint': feedback_dict.get('hint', ''),
                            'score': feedback_dict.get('score', 0),
                            'difficulty': difficulty,
                            'require_custom_function': bool(required_functions and required_functions.strip() and required_functions.strip() not in ('[]', '[""]')),
                            'problem_number': problem_number,
                            'problem_title': problem_title
                        }
                        error_info.append(error_entry)
                        
                        # 记录已处理的题目
                        if problem_number:
                            seen_problems.add(problem_number)
                        
                        # 记录难度等级
                        if difficulty:
                            difficulties.append(difficulty)
                        
                        # 记录是否需要自定义函数（排除空数组的情况）
                        has_required_func = False
                        if required_functions and required_functions.strip():
                            # 检查是否为空数组或空字符串
                            func_str = required_functions.strip()
                            if func_str not in ('', '[]', '[""]'):
                                has_required_func = True
                        require_custom_functions.append(has_required_func)
                except json.JSONDecodeError:
                    pass
        
        # 生成错误总结
        if not error_info:
            return {
                'summary': "该学生在该知识点上暂无错误记录",
                'difficulty': '基础',
                'require_custom_function': False,
                'error_details': [],
                'error_count': 0
            }
        
        summary_parts = []
        error_counts = {}
        for error in error_info:
            error_type = error['error_type']
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        for error_type, count in error_counts.items():
            summary_parts.append(f"{error_type}（出现{count}次）")
        
        # 添加具体的错误提示
        if len(error_info) > 0:
            hints = [e['hint'] for e in error_info if e['hint'] and len(e['hint']) < 100][:3]
            if hints:
                summary_parts.append("具体问题：")
                summary_parts.extend(hints)
        
        # 确定难度等级（取出现次数最多的）
        final_difficulty = '基础'
        if difficulties:
            difficulty_counts = {}
            for d in difficulties:
                difficulty_counts[d] = difficulty_counts.get(d, 0) + 1
            final_difficulty = max(difficulty_counts, key=difficulty_counts.get)
        
        # 确定是否需要自定义函数（只要有一个需要，就需要）
        final_require_custom = any(require_custom_functions)
        
        return {
            'summary': "; ".join(summary_parts),
            'difficulty': final_difficulty,
            'require_custom_function': final_require_custom,
            'error_details': error_info,  # 每个错题的详细信息
            'error_count': len(error_info)  # 错误题目数量
        }
    
    except Exception as e:
        print(f"ERROR: get_student_error_summary failed: {str(e)}")
        return {
            'summary': "获取错误总结失败",
            'difficulty': '基础',
            'require_custom_function': False,
            'error_details': [],
            'error_count': 0
        }

@app.route('/api/ai-recommend/generate', methods=['POST'])
def generate_ai_recommendations():
    """通过DeepSeek API生成AI推荐题目"""
    try:
        data = request.json
        student_id = data.get('student_id')
        class_name = data.get('class_name')
        knowledge_topic = data.get('knowledge_topic')
        language = data.get('language', 'python')
        count = data.get('count', 3)
        
        print(f"DEBUG: generate_ai_recommendations called with student_id={student_id}, class_name={class_name}, knowledge_topic={knowledge_topic}, language={language}, count={count}")
        
        session_db = Session()
        try:
            # 验证参数
            if not student_id and not class_name:
                return jsonify({
                    "success": False,
                    "error": "请提供student_id或class_name参数"
                }), 400
            
            # 如果提供了class_name，为班级所有学生生成推荐
            if class_name:
                # 查找班级中的所有学生
                students = session_db.query(Student).filter_by(class_name=class_name).all()
                if not students:
                    return jsonify({
                        "success": False,
                        "error": "班级不存在或班级中没有学生"
                    }), 404
                
                # 为每个学生生成推荐
                results = []
                for student in students:
                    print(f"DEBUG: Generating recommendations for student {student.id} - {student.name}")
                    try:
                        # 获取学生在该知识点上的错误总结
                        error_summary_data = get_student_error_summary(session_db, student.id, knowledge_topic)
                        error_summary = error_summary_data.get('summary', '')
                        difficulty = error_summary_data.get('difficulty', '基础')
                        require_custom_function = error_summary_data.get('require_custom_function', False)
                        error_count = error_summary_data.get('error_count', 0)
                        
                        # 错一题生成一题，使用错误题目数量作为生成数量
                        generate_count = max(error_count, 1)
                        
                        # 调用DeepSeek API生成题目
                        analyzer = get_deepseek_analyzer()
                        if not analyzer or not getattr(analyzer, 'api_key', ''):
                            return jsonify({
                                "success": False,
                                "error": "DeepSeek API密钥未配置，请设置环境变量 DEEPSEEK_API_KEY"
                            }), 500
                        
                        problems = analyzer.generate_problems_with_errors(knowledge_topic, generate_count, language, error_summary, difficulty, require_custom_function)
                        if problems is None:
                            print(f"DEBUG: AI generation failed for student {student.id}")
                            continue
                        
                        if not problems or len(problems) == 0:
                            print(f"DEBUG: No problems generated for student {student.id}")
                            continue
                        
                        # 获取当前最大的problem_number
                        max_problem = session_db.query(Problem).order_by(Problem.problem_number.desc()).first()
                        next_problem_number = max_problem.problem_number + 1 if max_problem else 10000
                        if next_problem_number < 10000:
                            next_problem_number = 10000
                        
                        # 保存题目
                        saved_problems = []
                        for i, problem in enumerate(problems):
                            description = problem.get('description', '')
                            
                            # 从题目描述中提取函数名称（支持提取多个函数名）
                            # 匹配模式：
                            # 1. 名为xxx的函数、定义一个名为xxx的函数、函数名为xxx
                            # 2. 方法名如 method_name()、类名.method_name()
                            # 使用findall提取所有匹配的函数名
                            extracted_func_names = []
                            
                            # 模式1：匹配 "名为xxx" 或 "函数名为xxx"
                            pattern1 = r'(?:名为|函数名\s*[为:]\s*["\']?)([a-zA-Z_][a-zA-Z0-9_]*)(?:["\'])?'
                            matches1 = re.findall(pattern1, description)
                            extracted_func_names.extend(matches1)
                            
                            # 模式2：匹配 "方法名()" 或 "类名.方法名()"
                            pattern2 = r'(?:[a-zA-Z_][a-zA-Z0-9_]*\.)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
                            matches2 = re.findall(pattern2, description)
                            extracted_func_names.extend(matches2)
                            
                            # 去重并过滤空字符串
                            extracted_func_names = list(filter(None, set(extracted_func_names)))
                            
                            # 获取AI返回的required_functions
                            ai_required_funcs = problem.get('required_functions', '')
                            
                            # 确定最终的必需函数列表
                            if extracted_func_names:
                                # 如果从描述中提取到函数名，使用提取的函数名
                                required_funcs_list = extracted_func_names
                            elif ai_required_funcs and ai_required_funcs.strip():
                                # 否则使用AI返回的函数名
                                required_funcs_list = [f.strip() for f in ai_required_funcs.split(',') if f.strip()]
                            elif require_custom_function:
                                # 如果需要自定义函数但没有提取到，使用默认的solve
                                required_funcs_list = ['solve']
                            else:
                                required_funcs_list = []
                            
                            # 转换为JSON字符串格式
                            required_functions_json = json.dumps(required_funcs_list)
                            
                            new_problem = Problem(
                                problem_number=next_problem_number + i,
                                title=problem.get('title', ''),
                                description=description,
                                input_description=problem.get('input_description', ''),
                                output_description=problem.get('output_description', ''),
                                sample_input=problem.get('sample_input', ''),
                                sample_output=problem.get('sample_output', ''),
                                test_input=problem.get('test_input', ''),
                                test_output=problem.get('test_output', ''),
                                category=knowledge_topic,
                                language=language,
                                difficulty=difficulty,
                                required_functions=required_functions_json
                            )
                            session_db.add(new_problem)
                            
                            ai_problem = AIRecommendedProblem(
                                student_id=student.id,
                                knowledge_topic=knowledge_topic,
                                language=language,
                                title=problem.get('title', ''),
                                description=problem.get('description', ''),
                                input_description=problem.get('input_description', ''),
                                output_description=problem.get('output_description', ''),
                                sample_input=problem.get('sample_input', ''),
                                sample_output=problem.get('sample_output', ''),
                                test_input=problem.get('test_input', ''),
                                test_output=problem.get('test_output', '')
                            )
                            session_db.add(ai_problem)
                            saved_problems.append({
                                'ai_problem': ai_problem,
                                'problem_number': next_problem_number + i
                            })
                        
                        # 更新下一个题目编号
                        next_problem_number += len(problems)
                        
                        # 创建推荐作业记录
                        topic_name = knowledge_topic
                        if '-' in topic_name:
                            parts = topic_name.split('-')
                            if len(parts) >= 2:
                                topic_name = '-'.join(parts[1:])
                        language_name = language.capitalize() if language else 'Python'
                        
                        existing_homeworks = session_db.query(AIRecommendedHomework).filter(
                            AIRecommendedHomework.title.like(f"{language_name}-{topic_name}-%"),
                            AIRecommendedHomework.student_id == student.id
                        ).all()
                        
                        max_sequence = 0
                        for homework in existing_homeworks:
                            match = re.search(rf"{language_name}-{re.escape(topic_name)}-(\d+)$", homework.title)
                            if match:
                                sequence = int(match.group(1))
                                if sequence > max_sequence:
                                    max_sequence = sequence
                        
                        next_sequence = max_sequence + 1
                        homework_title = f"{language_name}-{topic_name}-{next_sequence}"
                        
                        max_homework = session_db.query(AIRecommendedHomework).order_by(AIRecommendedHomework.id.desc()).first()
                        next_homework_id = max_homework.id + 1 if max_homework else 1
                        
                        problem_numbers_json = json.dumps([p['problem_number'] for p in saved_problems])
                        
                        ai_homework = AIRecommendedHomework(
                            id=next_homework_id,
                            student_id=student.id,
                            title=homework_title,
                            description=f"为学生 {student.name} 推荐的 {knowledge_topic} 练习题",
                            knowledge_topics=problem_numbers_json,
                            problem_count=len(saved_problems)
                        )
                        session_db.add(ai_homework)
                        
                        results.append({
                            'student_id': student.id,
                            'student_name': student.name,
                            'problems_count': len(saved_problems),
                            'homework_title': homework_title
                        })
                        
                    except Exception as e:
                        print(f"DEBUG: Error generating recommendations for student {student.id}: {e}")
                        continue
                
                session_db.commit()
                
                if len(results) == 0:
                    return jsonify({
                        "success": False,
                        "error": "未能为班级中的任何学生生成推荐题目"
                    }), 500
                
                return jsonify({
                    "success": True,
                    "message": f"成功为班级 {class_name} 中的 {len(results)} 名学生生成了推荐题目",
                    "results": results
                })
            
            # 如果提供了student_id，为单个学生生成推荐
            # 验证学生是否存在
            student = session_db.query(Student).filter_by(id=student_id).first()
            if not student:
                return jsonify({
                    "success": False,
                    "error": "学生不存在"
                }), 404
            
            # 获取学生在该知识点上的错误总结（包含每个错题的详细信息）
            error_summary_data = get_student_error_summary(session_db, student.id, knowledge_topic)
            error_summary = error_summary_data.get('summary', '')
            difficulty = error_summary_data.get('difficulty', '基础')
            require_custom_function = error_summary_data.get('require_custom_function', False)
            error_details = error_summary_data.get('error_details', [])
            error_count = error_summary_data.get('error_count', 0)
            
            # 错一题生成一题，使用错误题目数量作为生成数量
            generate_count = max(error_count, 1)  # 至少生成1题
            print(f"DEBUG: Student error summary for topic {knowledge_topic}: {error_summary}, difficulty: {difficulty}, require_custom_function: {require_custom_function}, error_count: {error_count}, generate_count: {generate_count}")
            
            # 调用DeepSeek API生成题目（传递难度和自定义函数要求，生成数量等于错误题目数量）
            analyzer = get_deepseek_analyzer()
            if not analyzer or not getattr(analyzer, 'api_key', ''):
                return jsonify({
                    "success": False,
                    "error": "DeepSeek API密钥未配置，请设置环境变量 DEEPSEEK_API_KEY"
                }), 500
            
            problems = analyzer.generate_problems_with_errors(knowledge_topic, generate_count, language, error_summary, difficulty, require_custom_function)
            print(f"DEBUG: Generated problems: {problems}")
            
            if problems is None:
                return jsonify({
                    "success": False,
                    "error": "AI生成题目失败，请检查API配置"
                }), 500
            
            if not problems or len(problems) == 0:
                return jsonify({
                    "success": False,
                    "error": "AI生成题目失败，未生成任何题目，请稍后重试"
                }), 500
            
            # 获取当前最大的problem_number，从10000开始
            max_problem = session_db.query(Problem).order_by(Problem.problem_number.desc()).first()
            if max_problem:
                next_problem_number = max_problem.problem_number + 1
                # 确保从10000开始
                if next_problem_number < 10000:
                    next_problem_number = 10000
            else:
                next_problem_number = 10000
            
            # 将题目保存到problems表和AI推荐表
            saved_problems = []
            print(f"DEBUG: Starting to save {len(problems)} problems")
            
            for i, problem in enumerate(problems):
                print(f"DEBUG: Saving problem {i+1}: {problem.get('title', 'No title')}")
                
                # 获取题目描述
                description = problem.get('description', '')
                
                # 从题目描述中提取函数名称（支持提取多个函数名）
                # 匹配模式：
                # 1. 名为xxx的函数、定义一个名为xxx的函数、函数名为xxx
                # 2. 方法名如 method_name()、类名.method_name()
                # 使用findall提取所有匹配的函数名
                extracted_func_names = []
                
                # 模式1：匹配 "名为xxx" 或 "函数名为xxx"
                pattern1 = r'(?:名为|函数名\s*[为:]\s*["\']?)([a-zA-Z_][a-zA-Z0-9_]*)(?:["\'])?'
                matches1 = re.findall(pattern1, description)
                extracted_func_names.extend(matches1)
                
                # 模式2：匹配 "方法名()" 或 "类名.方法名()"
                pattern2 = r'(?:[a-zA-Z_][a-zA-Z0-9_]*\.)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
                matches2 = re.findall(pattern2, description)
                extracted_func_names.extend(matches2)
                
                # 去重并过滤空字符串
                extracted_func_names = list(filter(None, set(extracted_func_names)))
                
                # 获取AI返回的required_functions
                ai_required_funcs = problem.get('required_functions', '')
                
                # 确定最终的必需函数列表
                if extracted_func_names:
                    # 如果从描述中提取到函数名，使用提取的函数名
                    required_funcs_list = extracted_func_names
                elif ai_required_funcs and ai_required_funcs.strip():
                    # 否则使用AI返回的函数名
                    required_funcs_list = [f.strip() for f in ai_required_funcs.split(',') if f.strip()]
                elif require_custom_function:
                    # 如果需要自定义函数但没有提取到，使用默认的solve
                    required_funcs_list = ['solve']
                else:
                    required_funcs_list = []
                
                # 转换为JSON字符串格式
                required_functions_json = json.dumps(required_funcs_list)
                print(f"DEBUG: Extracted function names: {extracted_func_names}, required_functions: {required_functions_json}")
                
                # 保存到problems表（使用从错题分析中获取的难度和自定义函数要求）
                new_problem = Problem(
                    problem_number=next_problem_number + i,
                    title=problem.get('title', ''),
                    description=description,
                    input_description=problem.get('input_description', ''),
                    output_description=problem.get('output_description', ''),
                    sample_input=problem.get('sample_input', ''),
                    sample_output=problem.get('sample_output', ''),
                    test_input=problem.get('test_input', ''),
                    test_output=problem.get('test_output', ''),
                    category=knowledge_topic,
                    language=language,
                    difficulty=difficulty,
                    required_functions=required_functions_json
                )
                session_db.add(new_problem)
                
                # 保存到AI推荐表
                ai_problem = AIRecommendedProblem(
                    student_id=student_id,
                    knowledge_topic=knowledge_topic,
                    language=language,
                    title=problem.get('title', ''),
                    description=problem.get('description', ''),
                    input_description=problem.get('input_description', ''),
                    output_description=problem.get('output_description', ''),
                    sample_input=problem.get('sample_input', ''),
                    sample_output=problem.get('sample_output', ''),
                    test_input=problem.get('test_input', ''),
                    test_output=problem.get('test_output', '')
                )
                session_db.add(ai_problem)
                saved_problems.append({
                    'ai_problem': ai_problem,
                    'problem_number': next_problem_number + i
                })
            
            print(f"DEBUG: Saved {len(saved_problems)} problems")
            
            # 提取知识点部分（去掉可能的语言前缀）
            topic_name = knowledge_topic
            # 处理可能的重复语言前缀（如"Python-Python-输入输出"）
            if '-' in topic_name:
                # 找到第一个"-"的位置，提取后面的知识点部分
                parts = topic_name.split('-')
                # 确保至少有两部分
                if len(parts) >= 2:
                    # 去掉第一个部分（可能的语言前缀），保留后面的所有部分
                    topic_name = '-'.join(parts[1:])
            # 获取语言名称
            language_name = language.capitalize() if language else 'Python'
            
            # 计算该知识点分类的最大序号
            # 查找包含该知识点分类的所有推荐作业
            category_pattern = f"^{language_name}-{re.escape(topic_name)}-\\d+$"
            existing_homeworks = session_db.query(AIRecommendedHomework).filter(
                AIRecommendedHomework.title.op('REGEXP')(category_pattern),
                AIRecommendedHomework.student_id == student_id
            ).all()
            
            # 提取最大序号
            max_sequence = 0
            for homework in existing_homeworks:
                # 提取序号部分
                match = re.search(rf"{language_name}-{re.escape(topic_name)}-(\d+)$", homework.title)
                if match:
                    sequence = int(match.group(1))
                    if sequence > max_sequence:
                        max_sequence = sequence
            
            # 新序号为最大序号加1
            next_sequence = max_sequence + 1
            
            # 获取当前最大的推荐作业ID
            max_homework = session_db.query(AIRecommendedHomework).order_by(AIRecommendedHomework.id.desc()).first()
            if max_homework:
                next_homework_id = max_homework.id + 1
            else:
                next_homework_id = 1
            
            # 生成推荐标题
            homework_title = f"{language_name}-{topic_name}-{next_sequence}"
            
            # 将题目编号保存为JSON格式
            problem_numbers_json = json.dumps([p['problem_number'] for p in saved_problems])
            
            # 计算推荐前的掌握率并保存到新表
            for p in saved_problems:
                # 根据题目编号获取知识点名称
                problem = session_db.query(Problem).filter(
                    Problem.problem_number == p['problem_number']
                ).first()
                if problem and problem.category:
                    # 提取核心知识点名称
                    topic = problem.category
                    if '-' in topic:
                        core_topic = '-'.join(topic.split('-')[1:])
                    else:
                        core_topic = topic
                    
                    # 计算推荐前的掌握率
                    # 查询该学生该知识点的历史提交记录
                    import datetime
                    current_time = datetime.datetime.now()
                    
                    # 查询该学生该知识点的所有提交记录
                    # 从 submissions 表中查询
                    total_submissions = 0
                    correct_submissions = 0
                    
                    # 构建查询条件
                    # 这里需要根据实际情况调整查询逻辑
                    # 暂时使用一个简单的查询
                    from sqlalchemy import text
                    # 查询 homework_submissions 表，通过 problem_id 关联 problems 表获取 category
                    submissions = session_db.execute(
                        text('''
                            SELECT hs.id, hs.code_content, hs.ai_feedback, p.category 
                            FROM homework_submissions hs
                            LEFT JOIN problems p ON hs.problem_id = p.id
                            WHERE hs.student_id = :student_id AND p.category LIKE :category
                        '''), 
                        {'student_id': student_id, 'category': f'%{core_topic}%'}
                    ).fetchall()
                    
                    for submission in submissions:
                        total_submissions += 1
                        # 解析 ai_feedback 字段，检查是否正确
                        try:
                            ai_feedback = submission[2]  # 第3个字段是 ai_feedback
                            if ai_feedback:
                                feedback = json.loads(ai_feedback)
                                if feedback.get('is_correct', False):
                                    correct_submissions += 1
                        except:
                            pass
                    
                    # 计算掌握率
                    if total_submissions > 0:
                        pre_recommend_mastery = correct_submissions / total_submissions
                    else:
                        pre_recommend_mastery = 0.5  # 没有提交记录时使用默认值
                    
                    # 检查是否已经存在记录
                    from sqlalchemy import text
                    existing_record = session_db.execute(
                        text('''
                            SELECT id FROM knowledge_recommendation_status 
                            WHERE student_id = :student_id AND knowledge_name = :knowledge_name
                        '''), 
                        {'student_id': student_id, 'knowledge_name': core_topic}
                    ).fetchone()
                    
                    if not existing_record:
                        # 插入新记录
                        from sqlalchemy import text
                        session_db.execute(
                            text('''
                                INSERT INTO knowledge_recommendation_status 
                                (student_id, knowledge_name, pre_recommend_mastery, recommend_time) 
                                VALUES (:student_id, :knowledge_name, :pre_recommend_mastery, :recommend_time)
                            '''), 
                            {
                                'student_id': student_id, 
                                'knowledge_name': core_topic, 
                                'pre_recommend_mastery': pre_recommend_mastery, 
                                'recommend_time': current_time
                            }
                        )
                    else:
                        # 更新现有记录
                        from sqlalchemy import text
                        session_db.execute(
                            text('''
                                UPDATE knowledge_recommendation_status 
                                SET pre_recommend_mastery = :pre_recommend_mastery, recommend_time = :recommend_time 
                                WHERE student_id = :student_id AND knowledge_name = :knowledge_name
                            '''), 
                            {
                                'pre_recommend_mastery': pre_recommend_mastery, 
                                'recommend_time': current_time, 
                                'student_id': student_id, 
                                'knowledge_name': core_topic
                            }
                        )
            
            # 创建推荐作业记录
            ai_homework = AIRecommendedHomework(
                id=next_homework_id,
                student_id=student_id,
                title=homework_title,
                description=f"为学生 {student.name} 推荐的 {knowledge_topic} 练习题",
                knowledge_topics=problem_numbers_json,
                problem_count=len(saved_problems)
            )
            session_db.add(ai_homework)
            
            session_db.commit()
            
            # 返回保存的题目
            result = []
            for i, saved in enumerate(saved_problems):
                result.append({
                    'id': saved['ai_problem'].id,
                    'problem_number': saved['problem_number'],
                    'title': saved['ai_problem'].title,
                    'description': saved['ai_problem'].description,
                    'input_description': saved['ai_problem'].input_description,
                    'output_description': saved['ai_problem'].output_description,
                    'sample_input': saved['ai_problem'].sample_input,
                    'sample_output': saved['ai_problem'].sample_output,
                    'knowledge_topic': saved['ai_problem'].knowledge_topic,
                    'language': saved['ai_problem'].language,
                    'generated_at': saved['ai_problem'].generated_at.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return jsonify({
                "success": True,
                "problems": result,
                "homework_id": next_homework_id,
                "message": f"成功生成 {len(result)} 道推荐题目，并创建推荐作业 {homework_title}"
            })
        finally:
            session_db.close()
    except Exception as e:
        print(f"DEBUG: Error in generate_ai_recommendations: {e}")
        return jsonify({
            "success": False,
            "error": f"生成推荐题目失败: {str(e)}"
        }), 500

@app.route('/api/ai-recommend/student/<int:student_id>', methods=['GET'])
def get_student_recommendations(student_id):
    """获取学生的AI推荐题目"""
    try:
        session_db = Session()
        try:
            # 首先通过user_id查找学生
            student = session_db.query(Student).filter_by(user_id=student_id).first()
            
            # 如果找不到，直接用student_id
            if not student:
                student_id_for_query = student_id
            else:
                student_id_for_query = student.id
            
            # 查询学生的推荐题目
            problems = session_db.query(AIRecommendedProblem).filter_by(
                student_id=student_id_for_query,
                is_active=1
            ).order_by(AIRecommendedProblem.generated_at.desc()).all()
            
            result = []
            for problem in problems:
                result.append({
                    'id': problem.id,
                    'title': problem.title,
                    'description': problem.description,
                    'input_description': problem.input_description,
                    'output_description': problem.output_description,
                    'sample_input': problem.sample_input,
                    'sample_output': problem.sample_output,
                    'knowledge_topic': problem.knowledge_topic,
                    'language': problem.language,
                    'generated_at': problem.generated_at.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return jsonify({
                "success": True,
                "recommendations": result
            })
        finally:
            session_db.close()
    except Exception as e:
        print(f"DEBUG: Error in get_student_recommendations: {e}")
        return jsonify({
            "success": False,
            "error": f"获取推荐题目失败: {str(e)}"
        }), 500

@app.route('/api/ai-recommend/list', methods=['GET'])
def get_all_recommendations():
    """获取所有学生的AI推荐题目（教师端）- 支持分页，每页15条"""
    try:
        session_db = Session()
        try:
            # 获取分页参数
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 15))
            
            # 查询所有推荐题目，关联学生信息
            query = session_db.query(AIRecommendedProblem, Student).join(
                Student, AIRecommendedProblem.student_id == Student.id
            ).filter(AIRecommendedProblem.is_active == 1).order_by(
                AIRecommendedProblem.generated_at.asc()
            )
            
            # 计算总记录数
            total = query.count()
            
            # 分页查询
            query = query.offset((page - 1) * per_page).limit(per_page)
            
            result = []
            for idx, (problem, student) in enumerate(query):
                # 查找对应的题目编号
                problem_record = session_db.query(Problem).filter_by(
                    title=problem.title,
                    category=problem.knowledge_topic,
                    language=problem.language
                ).first()
                problem_number = problem_record.problem_number if problem_record else '未知'
                
                # 生成推荐标签
                recommend_tag = f"{problem.knowledge_topic}-{((page - 1) * per_page) + idx + 1}"
                
                result.append({
                    'id': problem.id,
                    'student_id': student.id,
                    'student_name': student.name,
                    'student_number': student.student_id,
                    'class_name': student.class_name,
                    'recommend_tag': recommend_tag,
                    'problem_number': problem_number,
                    'title': problem.title,
                    'knowledge_topic': problem.knowledge_topic,
                    'language': problem.language,
                    'generated_at': problem.generated_at.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return jsonify({
                "success": True,
                "recommendations": result,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取推荐题目列表失败: {str(e)}"
        }), 500

@app.route('/api/ai-recommend/<int:problem_id>/delete', methods=['POST'])
def delete_ai_recommendation(problem_id):
    """删除AI推荐题目"""
    try:
        session_db = Session()
        try:
            problem = session_db.query(AIRecommendedProblem).filter_by(id=problem_id).first()
            if not problem:
                return jsonify({
                    "success": False,
                    "error": "推荐题目不存在"
                }), 404
            
            problem.is_active = 0
            session_db.commit()
            
            return jsonify({
                "success": True,
                "message": "删除成功"
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"删除推荐题目失败: {str(e)}"
        }), 500

@app.route('/api/ai-recommend/homework/list', methods=['GET'])
def get_ai_homework_list():
    """获取所有AI推荐作业列表（优化版，支持分页和搜索，每页15条）"""
    try:
        session_db = Session()
        try:
            # 获取分页参数
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 15))
            
            # 获取搜索参数
            search_student_number = request.args.get('search_student_number', '').strip()
            search_student_name = request.args.get('search_student_name', '').strip()
            search_class_name = request.args.get('search_class_name', '').strip()
            
            # 查询所有推荐作业，关联学生信息
            query = session_db.query(AIRecommendedHomework, Student).join(
                Student, AIRecommendedHomework.student_id == Student.id
            ).filter(AIRecommendedHomework.is_active == 1)
            
            # 应用搜索过滤条件
            if search_student_number:
                query = query.filter(Student.student_id.like(f'%{search_student_number}%'))
            if search_student_name:
                query = query.filter(Student.name.like(f'%{search_student_name}%'))
            if search_class_name:
                query = query.filter(Student.class_name == search_class_name)
            
            # 排序：从最早到最近
            query = query.order_by(AIRecommendedHomework.generated_at.asc())
            
            # 计算总记录数（应用过滤条件后）
            total = query.count()
            
            # 分页查询
            query = query.offset((page - 1) * per_page).limit(per_page)
            
            result = []
            
            # 收集所有题目编号
            all_problem_numbers = set()
            homeworks_list = []
            
            for homework, student in query:
                # 从 knowledge_topics 解析题目编号
                problem_numbers_str = '未知'
                problem_numbers = []
                try:
                    if homework.knowledge_topics:
                        parsed = json.loads(homework.knowledge_topics)
                        if isinstance(parsed, list):
                            problem_numbers = parsed
                            problem_numbers_str = ', '.join(map(str, problem_numbers))
                        else:
                            problem_numbers_str = str(parsed)
                except:
                    pass
                
                # 收集题目编号
                all_problem_numbers.update(problem_numbers)
                
                homeworks_list.append({
                    'id': homework.id,
                    'student_id': student.id,
                    'student_name': student.name,
                    'student_number': student.student_id,
                    'class_name': student.class_name,
                    'title': homework.title,
                    'problem_number': problem_numbers_str,
                    'problem_count': homework.problem_count,
                    'generated_at': homework.generated_at.strftime('%Y-%m-%d %H:%M:%S'),
                    '_problem_numbers': problem_numbers  # 保存原始数字列表供后续使用
                })
            
            # 批量获取所有题目详情
            problem_map = {}
            if all_problem_numbers:
                problems = session_db.query(Problem).filter(
                    Problem.problem_number.in_(all_problem_numbers)
                ).all()
                for p in problems:
                    problem_map[p.problem_number] = {
                        'id': p.id,
                        'problem_number': p.problem_number,
                        'title': p.title
                    }
            
            # 收集所有学生ID
            student_ids = [hw['student_id'] for hw in homeworks_list]
            
            # 批量获取所有学生的提交记录
            submission_map = {}
            if student_ids:
                submissions = session_db.query(HomeworkSubmission).filter(
                    HomeworkSubmission.student_id.in_(student_ids)
                ).all()
                for s in submissions:
                    key = f"{s.student_id}_{s.problem_id}"
                    # 解析 ai_feedback 获取正确性信息
                    is_correct = False
                    try:
                        if s.ai_feedback:
                            feedback = json.loads(s.ai_feedback)
                            is_correct = feedback.get('is_correct', False)
                    except:
                        pass
                    submission_map[key] = is_correct
            
            # 为每个推荐作业添加完成状态
            for homework in homeworks_list:
                is_completed = True
                for num in homework['_problem_numbers']:
                    problem = problem_map.get(num)
                    if problem:
                        key = f"{homework['student_id']}_{problem['id']}"
                        if submission_map.get(key) != 1:
                            is_completed = False
                            break
                    else:
                        is_completed = False
                        break
                
                homework['is_completed'] = is_completed
                del homework['_problem_numbers']  # 删除临时字段
                result.append(homework)
            
            return jsonify({
                "success": True,
                "homeworks": result,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取推荐作业列表失败: {str(e)}"
        }), 500

@app.route('/api/ai-recommend/homework/<int:homework_id>/detail', methods=['GET'])
def get_ai_homework_detail(homework_id):
    """获取AI推荐作业详情（优化版，一次性返回所有数据）"""
    try:
        session_db = Session()
        try:
            # 查询推荐作业
            homework = session_db.query(AIRecommendedHomework).filter_by(id=homework_id).first()
            if not homework:
                return jsonify({
                    "success": False,
                    "error": "推荐作业不存在"
                })
            
            # 获取学生信息
            student = session_db.query(Student).filter_by(id=homework.student_id).first()
            if not student:
                return jsonify({
                    "success": False,
                    "error": "学生不存在"
                })
            
            
            # 解析题目编号列表
            problem_numbers = []
            try:
                if homework.knowledge_topics:
                    parsed = json.loads(homework.knowledge_topics)
                    if isinstance(parsed, list):
                        problem_numbers = parsed
            except:
                pass
            
            # 批量获取所有题目详情
            problems = []
            if problem_numbers:
                problem_list = session_db.query(Problem).filter(
                    Problem.problem_number.in_(problem_numbers)
                ).all()
                
                # 获取该学生的提交记录
                submissions = session_db.query(HomeworkSubmission).filter(
                    HomeworkSubmission.student_id == homework.student_id
                ).all()
                
                # 创建提交记录映射
                submission_map = {}
                for s in submissions:
                    key = f"{s.student_id}_{s.problem_id}"
                    submission_map[key] = s
                
                # 构建题目详情列表
                for num in problem_numbers:
                    problem = next((p for p in problem_list if p.problem_number == num), None)
                    if problem:
                        # 查找提交记录
                        submission = submission_map.get(f"{homework.student_id}_{problem.id}")
                        
                        # 解析提交反馈
                        is_correct = None
                        ai_feedback = None
                        submission_time = None
                        code_content = None
                        
                        if submission:
                            submission_time = submission.submission_time.strftime('%Y-%m-%d %H:%M:%S') if submission.submission_time else None
                            code_content = submission.code_content
                            if submission.ai_feedback:
                                try:
                                    ai_feedback = json.loads(submission.ai_feedback)
                                    is_correct = ai_feedback.get('is_correct')
                                except:
                                    pass
                        
                        problems.append({
                            'problem_number': problem.problem_number,
                            'title': problem.title,
                            'description': problem.description,
                            'input_description': problem.input_description,
                            'output_description': problem.output_description,
                            'sample_input': problem.sample_input,
                            'sample_output': problem.sample_output,
                            'test_input': problem.test_input,
                            'test_output': problem.test_output,
                            'is_correct': is_correct,
                            'ai_feedback': ai_feedback,
                            'submission_time': submission_time,
                            'code_content': code_content
                        })
            
            result = {
                'id': homework.id,
                'student_id': student.id,
                'student_name': student.name,
                'student_number': student.student_id,
                'class_name': student.class_name,
                'title': homework.title,
                'description': homework.description,
                'problem_count': homework.problem_count,
                'generated_at': homework.generated_at.strftime('%Y-%m-%d %H:%M:%S'),
                'problems': problems
            }
            
            return jsonify({
                "success": True,
                "homework": result
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取推荐作业详情失败: {str(e)}"
        }), 500

@app.route('/api/ai-recommend/homework/<int:homework_id>/update-problem-number', methods=['POST'])
def update_ai_homework_problem_number(homework_id):
    """修改AI推荐作业的题目号和生成时间"""
    try:
        data = request.json
        if not data or 'problem_number' not in data:
            return jsonify({
                "success": False,
                "error": "请求数据不能为空"
            }), 400
        
        session_db = Session()
        try:
            # 查找推荐作业
            homework = session_db.query(AIRecommendedHomework).filter_by(id=homework_id).first()
            if not homework:
                return jsonify({
                    "success": False,
                    "error": "推荐作业不存在"
                })
            
            # 解析题目号字符串，转换为数字列表
            problem_numbers_str = data['problem_number']
            numbers = [int(num.strip()) for num in problem_numbers_str.split(',') if num.strip().isdigit()]
            
            # 更新题目数量
            homework.problem_count = len(numbers)
            
            # 更新knowledge_topics字段（JSON格式存储题目编号列表）
            homework.knowledge_topics = json.dumps(numbers) if numbers else ''
            
            # 更新生成时间（如果提供了）
            if 'generated_at' in data and data['generated_at']:
                try:
                    from datetime import datetime as dt
                    homework.generated_at = dt.strptime(data['generated_at'], '%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    print(f"解析生成时间失败: {str(e)}")
            
            session_db.commit()
            
            return jsonify({
                "success": True,
                "message": "修改成功"
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"修改失败: {str(e)}"
        }), 500

@app.route('/api/ai-recommend/homework/<int:homework_id>/delete', methods=['POST', 'DELETE'])
def delete_ai_homework(homework_id):
    """删除AI推荐作业（已生成的题目不会被删除，学生端推荐列表会同步删除）"""
    try:
        session_db = Session()
        try:
            # 查找推荐作业
            homework = session_db.query(AIRecommendedHomework).filter_by(id=homework_id).first()
            if not homework:
                return jsonify({
                    "success": False,
                    "error": "推荐作业不存在"
                })
            
            # 删除推荐作业（只删除推荐记录，不删除已生成的题目）
            session_db.delete(homework)
            session_db.commit()
            
            return jsonify({
                "success": True,
                "message": "删除成功"
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"删除失败: {str(e)}"
        }), 500

@app.route('/api/ai-recommend/homework/<int:homework_id>/send', methods=['POST'])
def send_ai_homework(homework_id):
    """发送AI推荐作业到学生端"""
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        
        if not student_id:
            return jsonify({
                "success": False,
                "error": "学生ID不能为空"
            })
        
        session_db = Session()
        try:
            # 查找推荐作业
            homework = session_db.query(AIRecommendedHomework).filter_by(id=homework_id).first()
            if not homework:
                return jsonify({
                    "success": False,
                    "error": "推荐作业不存在"
                })
            
            # 检查学生是否存在
            student = session_db.query(Student).filter_by(id=student_id).first()
            if not student:
                return jsonify({
                    "success": False,
                    "error": "学生不存在"
                })
            
            # 这里可以添加发送逻辑，比如更新状态或记录发送历史
            # 由于我们的推荐作业已经与学生关联，所以实际上只需要确保数据正确即可
            
            return jsonify({
                "success": True,
                "message": "发送成功"
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"发送失败: {str(e)}"
        }), 500

@app.route('/api/ai-recommend/student-homework/<int:user_id>', methods=['GET'])
def get_student_homework(user_id):
    """获取学生的AI推荐作业列表"""
    try:
        session_db = Session()
        try:
            # 先根据用户ID找到对应的学生
            user = session_db.query(User).filter_by(id=user_id).first()
            if not user:
                return jsonify({
                    "success": False,
                    "error": "用户不存在"
                })
            
            # 根据用户的用户名（学号）找到对应的学生
            student = session_db.query(Student).filter_by(student_id=user.username).first()
            if not student:
                return jsonify({
                    "success": False,
                    "error": "学生不存在"
                })
            
            # 查询学生的推荐作业
            homeworks = session_db.query(AIRecommendedHomework).filter_by(
                student_id=student.id,
                is_active=1
            ).order_by(AIRecommendedHomework.generated_at.desc()).all()
            
            result = []
            for homework in homeworks:
                # 从 knowledge_topics 解析题目编号（JSON格式）
                problem_numbers_str = '未知'
                try:
                    problem_numbers = json.loads(homework.knowledge_topics) if homework.knowledge_topics else []
                    problem_numbers_str = ', '.join(map(str, problem_numbers)) if problem_numbers else '未知'
                except:
                    problem_numbers_str = '未知'
                
                result.append({
                    'id': homework.id,
                    'title': homework.title,  # 推荐标题，格式为"语言-分类知识点-序号"
                    'description': homework.description,
                    'problem_number': problem_numbers_str,  # 题目编号，用逗号分隔
                    'problem_count': homework.problem_count,  # 题目数量
                    'generated_at': homework.generated_at.strftime('%Y-%m-%d %H:%M:%S')  # 生成时间
                })
            
            return jsonify({
                "success": True,
                "homeworks": result
            })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取学生推荐作业列表失败: {str(e)}"
        }), 500

@app.route('/api/students/verify', methods=['POST'])
def verify_student():
    """验证学生登录"""
    try:
        data = request.get_json()
        username = data.get('username', '')
        password = data.get('password', '')
        
        session_db = Session()
        try:
            # 通过学号验证学生
            student = session_db.query(Student).filter_by(student_id=username).first()
            
            if student:
                # 验证密码（这里简单处理，实际应该加密验证）
                if password == '123456':  # 统一密码123456
                    return jsonify({
                        "success": True,
                        "student_id": student.id,
                        "student_name": student.name,
                        "class_name": student.class_name
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": "密码错误"
                    })
            else:
                return jsonify({
                    "success": False,
                    "error": "学号不存在"
                })
        finally:
            session_db.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"验证失败: {str(e)}"
        }), 500

# 前端路由支持 - 所有未匹配的路由返回index.html（用于Vue单页应用）


# ========== 前端路由支持 - 必须放在最后 ==========


# ========== 前端路由支持 - 必须放在最后 ==========


# ========== 前端路由支持 ==========
@app.route("/")
def index():
    from flask import send_from_directory
    return send_from_directory("frontend/dist", "index.html")

@app.route("/teacher")
def teacher_index():
    from flask import send_from_directory
    return send_from_directory("frontend/dist", "index.html")

@app.route("/teacher/<path:path>")
def teacher_catch_all(path):
    from flask import send_from_directory
    static_extensions = [".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2", ".ttf", ".eot"]
    if any(path.endswith(ext) for ext in static_extensions):
        return send_from_directory("frontend/dist", path)
    return send_from_directory("frontend/dist", "index.html")

@app.route("/assets/<path:filename>")
def static_files(filename):
    from flask import send_from_directory
    return send_from_directory("frontend/dist/assets", filename)

@app.route("/<path:path>")
def catch_all(path):
    from flask import send_from_directory
    static_extensions = [".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2", ".ttf", ".eot"]
    if any(path.endswith(ext) for ext in static_extensions):
        return send_from_directory("frontend/dist", path)
    return send_from_directory("frontend/dist", "index.html")

if __name__ == "__main__":
    init_default_teacher()
    app.run(host="0.0.0.0", port=5002, debug=False)
