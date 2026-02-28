#!/usr/bin/env python3
"""
lica 格式转换工具（流式版）
将 zip 文件打包为 JSON + Base64 格式（.lica），或反向解包。
支持超大文件：打包时边读边写，内存占用极小。
解包时可选择使用 ijson 流式解析，避免加载整个 JSON。
"""

import zipfile
import json
import base64
import os
import argparse

try:
    import ijson
    HAS_IJSON = True
except ImportError:
    HAS_IJSON = False


def pack(zip_path, lica_path):
    """
    将 zip 文件打包成 lica 格式（流式写入 JSON）。
    """
    try:
        zf = zipfile.ZipFile(zip_path, 'r')
    except Exception as e:
        print(f"读取 zip 文件失败: {e}")
        return

    file_count = 0
    with open(lica_path, 'w', encoding='utf-8') as out_f:
        # 写入 JSON 开头
        out_f.write('{')
        first = True

        for info in zf.infolist():
            if info.is_dir():
                continue
            # 读取文件内容
            with zf.open(info) as f:
                content = f.read()
            b64_str = base64.b64encode(content).decode('utf-8')

            # 写入键值对
            if not first:
                out_f.write(',')
            first = False

            # JSON 键需要转义
            key = json.dumps(info.filename)
            out_f.write(f'{key}:"{b64_str}"')
            file_count += 1

            # 可选：输出进度
            if file_count % 100 == 0:
                print(f"已处理 {file_count} 个文件...")

        # 写入 JSON 结尾
        out_f.write('}')
    zf.close()
    print(f"✅ 打包成功：{file_count} 个文件 -> {lica_path}")


def unpack(lica_path, output_dir, use_stream=False):
    """
    将 lica 文件解包到指定目录。
    如果 use_stream=True 且安装了 ijson，则使用流式解析（适合超大 JSON）。
    否则使用标准 json.load（适合中等大小文件）。
    """
    os.makedirs(output_dir, exist_ok=True)

    if use_stream and HAS_IJSON:
        # 流式解析
        try:
            with open(lica_path, 'rb') as f:
                parser = ijson.kvitems(f, '')
                count = 0
                for key, b64_str in parser:
                    try:
                        content = base64.b64decode(b64_str)
                        full_path = os.path.join(output_dir, key)
                        os.makedirs(os.path.dirname(full_path), exist_ok=True)
                        with open(full_path, 'wb') as out_f:
                            out_f.write(content)
                        count += 1
                        if count % 100 == 0:
                            print(f"已解包 {count} 个文件...")
                    except Exception as e:
                        print(f"处理文件 {key} 时出错: {e}")
            print(f"✅ 解包成功：{count} 个文件 -> {output_dir}")
        except Exception as e:
            print(f"流式解析失败: {e}")
    else:
        # 标准一次性加载
        try:
            with open(lica_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"读取 lica 文件失败: {e}")
            return

        count = 0
        for rel_path, b64_str in data.items():
            try:
                content = base64.b64decode(b64_str)
                full_path = os.path.join(output_dir, rel_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'wb') as out_f:
                    out_f.write(content)
                count += 1
            except Exception as e:
                print(f"处理文件 {rel_path} 时出错: {e}")
        print(f"✅ 解包成功：{count} 个文件 -> {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="将 zip 文件转换为 lica 格式（JSON + Base64），或反向解包。支持流式处理大文件。"
    )
    subparsers = parser.add_subparsers(dest='command', required=True, help='子命令')

    # pack 子命令
    parser_pack = subparsers.add_parser('pack', help='将 zip 打包为 lica')
    parser_pack.add_argument('input_zip', help='输入的 zip 文件路径')
    parser_pack.add_argument('output_lica', help='输出的 lica 文件路径（建议后缀 .lica 或 .lic）')

    # unpack 子命令
    parser_unpack = subparsers.add_parser('unpack', help='将 lica 解包到目录')
    parser_unpack.add_argument('input_lica', help='输入的 lica 文件路径')
    parser_unpack.add_argument('output_dir', help='输出目录路径')
    parser_unpack.add_argument('--stream', action='store_true',
                               help='使用流式解析（需要安装 ijson），适合超大 JSON 文件')

    args = parser.parse_args()

    if args.command == 'pack':
        pack(args.input_zip, args.output_lica)
    elif args.command == 'unpack':
        unpack(args.input_lica, args.output_dir, use_stream=args.stream)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()