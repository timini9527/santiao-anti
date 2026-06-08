import os
import zipfile

def zip_clean_project(output_filename, source_dir):
    # 1. 定义需要整文件夹过滤的“黑名单”
    exclude_dirs = {'.git', '__pycache__', 'venv', '.idea', 'logs', 'reports', 'unused_pages'}
    # 2. 定义需要过滤的无用文件后缀
    exclude_exts = {'.pyc', '.log', '.tmp', '.DS_Store'}

    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            # 过滤不需要的目录，原地修改 dirs 列表
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                # 过滤不需要的文件后缀
                if any(file.endswith(ext) for ext in exclude_exts):
                    continue
                
                # 排除打包脚本自身和已经打好的压缩包
                if file == 'pack.py' or file == output_filename:
                    continue
                
                file_path = os.path.join(root, file)
                # 计算相对路径，保持解压后的目录结构清晰
                arcname = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arcname)
                print(f"已添加: {arcname}")

if __name__ == '__main__':
    zip_clean_project('santiao_0.5-anti.zip', '.')
    print("打包完成！")