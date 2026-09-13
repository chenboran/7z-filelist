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
            return f"{size_bytes:3.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}PB"


def format_time(dt):
    """把 datetime 格式化为字符串，缺失时用占位符"""
    if dt is None:
        return "-"
    return dt.strftime("%Y-%m-%d %H:%M:%S")


class Node:
    __slots__ = ("name", "is_dir", "size", "mtime", "children")

    def __init__(self, name, is_dir):
        self.name = name
        self.is_dir = is_dir
        self.size = 0
        self.mtime = None
        self.children = {}  # name -> Node，插入顺序保留，展示时再排序


def build_tree(file_info_list):
    """把 py7zr 返回的扁平文件列表，组装成一棵目录树"""
    root = Node("", True)

    for item in file_info_list:
        parts = item.filename.replace("\\", "/").strip("/").split("/")
        node = root
        for i, part in enumerate(parts):
            is_last_part = i == len(parts) - 1
            if part not in node.children:
                # 中间路径可能没有显式目录条目，先按目录占位，后面若有显式条目会被补全
                node.children[part] = Node(part, True if not is_last_part else item.is_directory)
            node = node.children[part]
        # 到达条目本身，写入真实信息
        node.is_dir = item.is_directory
        node.size = 0 if item.is_directory else item.uncompressed
        node.mtime = item.creationtime

    return root


def compute_dir_sizes(node):
    """目录本身在压缩包里通常不带大小，这里递归汇总子项大小，方便查看占用"""
    if not node.is_dir:
        return node.size
    total = 0
    for child in node.children.values():
        total += compute_dir_sizes(child)
    node.size = total
    return total


def render_tree(node, prefix, lines):
    children = sorted(node.children.values(), key=lambda n: n.name.lower())
    for i, child in enumerate(children):
        is_last = i == len(children) - 1
        connector = "└── " if is_last else "├── "
        name_display = child.name + ("/" if child.is_dir else "")
        info = f"[{format_size(child.size)} {format_time(child.mtime)}]"
        lines.append(f"{prefix}{connector}{name_display} {info}")
        extension = "    " if is_last else "│   "
        render_tree(child, prefix + extension, lines)


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
            for item in file_info_list:
                if item.is_directory:
                    total_dirs += 1
                else:
                    total_files += 1
                    total_uncompressed_size += item.uncompressed

            root = build_tree(file_info_list)
            compute_dir_sizes(root)

            lines = []
            lines.append("=" * 110)
            lines.append(f"压缩包名称: {os.path.basename(archive_path)}")
            lines.append(
                f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            lines.append("=" * 110)

            # 根节点：用压缩包本身的大小/修改时间展示
            archive_mtime = datetime.fromtimestamp(os.path.getmtime(archive_path))
            lines.append(
                f"{os.path.basename(archive_path)}/ "
                f"[{format_size(total_uncompressed_size)} {format_time(archive_mtime)}]"
            )

            render_tree(root, "", lines)

            lines.append("")
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