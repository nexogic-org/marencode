# 如何打包 Maren Code

本项目提供了自动打包脚本，可以将 Maren Code 打包为独立的 `.exe` 可执行文件。

## 前置要求

- Windows 系统
- Python 3.8+ 已安装并添加到 PATH

## 快速打包

双击运行根目录下的 `build.bat` 脚本即可。

脚本会自动执行以下步骤：
1. 创建虚拟环境 `venv`
2. 安装项目依赖 (`requirements.txt`)
3. 安装打包工具 `PyInstaller`
4. 执行打包脚本 `build_installer.py`

打包完成后，可执行文件位于 `dist/maren.exe`。

## 手动打包

如果你想手动执行打包过程，请在终端中运行：

```bash
# 1. 安装依赖
pip install -r requirements.txt
pip install pyinstaller

# 2. 执行打包脚本
python build_installer.py
```

## 注意事项

- 打包脚本会自动处理 `core.skill` 下的动态加载模块。
- 配置文件（`.maren/` 目录）会在程序首次运行时在用户目录下自动生成，无需打包。
