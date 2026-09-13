from datetime import datetime
import os
import sys
import tkinter as tk
from tkinter import filedialog

# 检查是否安装了 py7zr
try:
    import py7zr
except ImportError:
    print("❌ 缺少依赖库！请先在命令行运行: pip install py7zr")
    input("按回车键退出...")
    sys.exit()


def format_size(size_bytes):
    """把字节大小自动换算成 KB, MB, GB"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:3.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def format_time(dt):
    """把 datetime 格式化为字符串，缺失时用占位符"""
    if dt is None:
        return "-"
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def export_7z_list(archive_path):
    if not os.path.exists(archive_path):
        print(f"❌ 文件不存在: {archive_path}")
        return

    archive_dir = os.path.dirname(os.path.abspath(archive_path))
    base_name = os.path.splitext(os.path.basename(archive_path))[0]
    output_txt = os.path.join(archive_dir, f"{base_name}_目录清单.txt")

    print(f"正在读取压缩包结构: {os.path.basename(archive_path)} ...")

    try:
        with py7zr.SevenZipFile(archive_path, mode="r") as archive:
            file_info_list = archive.list()

            total_files = 0
            total_dirs = 0
            total_uncompressed_size = 0

            lines = []
            lines.append("=" * 110)
            lines.append(f"压缩包名称: {os.path.basename(archive_path)}")
            lines.append(
                f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            lines.append("=" * 110)
            lines.append(
                f"{'文件大小':<12} | {'类型':<6} | {'修改时间':<19} | 相对路径与名称"
            )
            lines.append("-" * 110)

            for item in file_info_list:
                path = item.filename
                mtime_str = format_time(item.creationtime)
                if item.is_directory:
                    total_dirs += 1
                    lines.append(
                        f"{'-':<12} | {'[目录]':<6} | {mtime_str:<19} | {path}/"
                    )
                else:
                    total_files += 1
                    size_str = format_size(item.uncompressed)
                    total_uncompressed_size += item.uncompressed
                    lines.append(
                        f"{size_str:<12} | {'[文件]':<6} | {mtime_str:<19} | {path}"
                    )

            lines.append("=" * 110)
            lines.append(
                f"统计汇总: 共 {total_files} 个文件，{total_dirs} 个文件夹"
            )
            lines.append(
                f"解压缩后总大小: {format_size(total_uncompressed_size)}"
            )
            lines.append("=" * 110)

        # 写入 TXT，强制 UTF-8 编码，彻底杜绝中文乱码
        with open(output_txt, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"✅ 成功生成清单: {output_txt}\n")

    except Exception as e:
        print(f"❌ 读取压缩包出错: {e}")


def main():
    # 方式 1：如果通过命令行传参，或者直接把 7z 文件拖拽到本 py 文件上
    if len(sys.argv) > 1:
        for file_path in sys.argv[1:]:
            if file_path.lower().endswith(".7z"):
                export_7z_list(file_path)
    else:
        # 方式 2：直接双击运行脚本，自动弹出一个可视化的文件选择框
        root = tk.Tk()
        root.withdraw()  # 隐藏 Tkinter 的主空白窗口
        file_paths = filedialog.askopenfilenames(
            title="请选择一个或多个 7z 压缩包（支持多选）",
            filetypes=[("7z 压缩包", "*.7z"), ("所有文件", "*.*")],
        )
        if file_paths:
            for path in file_paths:
                export_7z_list(path)
        else:
            print("未选择任何文件。")

    input("全部处理完成，按回车键退出...")


if __name__ == "__main__":
    main()
