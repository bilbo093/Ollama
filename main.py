#!/usr/bin/env python3
"""
学术文档处理工具主入口
运行：python main.py
用法：
  python main.py full -i input.txt -o output.txt
  python main.py chapter -i input.txt -o output.txt
  python main.py paragraph -i input.docx
"""
import sys
import os

import argparse

# 自动找到 src 目录
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from ollama_processor import chat
from file_io import read_file_content, validate_file_format, save_to_txt
from config import PROCESSOR_CONFIGS, BASE_URL
from docx_editor import process_document, apply_txt_to_document
from document_provider import create_provider
from content_splitter import split_content_by_chapters


def main():
    """主函数：解析命令行参数并执行对应操作"""
    parser = argparse.ArgumentParser(
        prog='academic-doc',
        description='学术文档处理工具 - 支持三种处理粒度：全文(full)、章节(chapter)、段落(paragraph)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例：
  全文处理:  python main.py full -i input.txt -o output.txt
  章节处理:  python main.py chapter -i input.txt -o output.txt
  段落处理:  python main.py paragraph -i input.docx

  段落处理（自动推断文件）:
    python main.py paragraph -i input.docx
  段落处理（指定检查结果文件）:
    python main.py paragraph -i input.docx -o grammar.txt

  说明：
  - 全文模式：将整个文档一次性送入 LLM 处理
  - 章节模式：按章节拆分后逐章送入 LLM 处理
  - 段落模式：按段落拆分后逐段送入 LLM 检查并应用修改
  - 语法检查文件：使用 -o 指定 .txt 文件，或自动使用 input/{文件名}_grammar.txt
  - 输出 DOCX 文件：自动生成 {输入文件名}_fixed.docx，与输入文件同目录
  - 无需匹配：直接将每段送入模型检查，返回原文和修改后的内容，完全避免匹配问题
        '''
    )

    subparsers = parser.add_subparsers(dest='command', help='命令类型')

    # full 子命令（全文模式）
    full_parser = subparsers.add_parser('full', help='全文模式：整个文档一次性送入 LLM')
    full_parser.add_argument('-i', '--input', type=str, required=True,
                             help='输入文件路径 (.txt 或 .docx)')
    full_parser.add_argument('-o', '--output', type=str, required=True,
                             help='输出文件路径 (.txt)')

    # chapter 子命令（章节模式）
    chapter_parser = subparsers.add_parser('chapter', help='章节模式：按章节拆分后逐章送入 LLM')
    chapter_parser.add_argument('-i', '--input', type=str, required=True,
                                help='输入文件路径 (.txt 或 .docx)')
    chapter_parser.add_argument('-o', '--output', type=str, required=True,
                                help='输出文件路径 (.txt)')

    # paragraph 子命令（段落模式）
    paragraph_parser = subparsers.add_parser('paragraph', help='段落模式：按段落拆分后逐段送入 LLM')
    paragraph_parser.add_argument('-i', '--input', type=str, required=True,
                                  help='输入文件路径 (.txt 或 .docx)')
    paragraph_parser.add_argument('-o', '--output', type=str,
                                  help='检查结果文件路径（.txt）')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == 'full':
            print(f"[使用] 后端：{BASE_URL}")
            input_file = args.input
            output_file = args.output

            if not os.path.exists(input_file):
                print(f"[错误] 输入文件不存在：{input_file}")
                sys.exit(1)

            if not validate_file_format(input_file):
                sys.exit(1)

            # 读取文件内容
            file_ext = os.path.splitext(input_file)[1].lower()
            print(f"[处理] {file_ext.upper().lstrip('.')} 文件：{input_file}")
            content = read_file_content(input_file)

            # 全文送入 LLM
            print("[全文] 正在处理整个文档...")
            config = PROCESSOR_CONFIGS['full']
            prompt = config['prompt_template'].format(content=content)
            messages = [config['role'], {'role': 'user', 'content': prompt}]
            result = chat(messages)
            print("[全文处理完成]")
            save_to_txt(result, output_file)

        elif args.command == 'chapter':
            print(f"[使用] 后端：{BASE_URL}")
            print("[章节] 按章节拆分处理...")

            if not os.path.exists(args.input):
                print(f"[错误] 输入文件不存在：{args.input}")
                sys.exit(1)

            if not validate_file_format(args.input):
                sys.exit(1)

            content = read_file_content(args.input)
            chapters = split_content_by_chapters(content)
            print(f"[信息] 识别到 {len(chapters)} 个章节")

            config = PROCESSOR_CONFIGS['chapter']
            save_to_txt("", args.output, "章节总结", mode='w')

            for idx, chapter in enumerate(chapters, 1):
                print(f"[章节 {idx}/{len(chapters)}] {chapter['title']}")
                prompt = config['prompt_template'].format(
                    content=chapter['content'],
                    chapter_title=chapter['title']
                )
                messages = [config['role'], {'role': 'user', 'content': prompt}]
                summary = chat(messages)
                chapter_content = f"\n\n{chapter['title']}\n\n{summary}\n\n"
                save_to_txt(chapter_content, args.output, "", mode='a')

            print(f"[完成] 共处理 {len(chapters)} 个章节，已保存至：{args.output}")

        elif args.command == 'paragraph':
            print(f"[使用] 后端：{BASE_URL}")

            # 验证输入文件
            if not os.path.exists(args.input):
                print(f"[错误] 输入文件不存在：{args.input}")
                sys.exit(1)

            input_ext = os.path.splitext(args.input)[1].lower()

            # 处理 -o 参数
            output_txt_file = None
            if args.output:
                output_ext = os.path.splitext(args.output)[1].lower()
                if output_ext != '.txt':
                    print(f"[错误] -o 参数必须是 .txt 格式：{args.output}")
                    sys.exit(1)
                output_txt_file = args.output

            if not output_txt_file:
                base_name = os.path.splitext(os.path.basename(args.input))[0]
                output_txt_file = os.path.join('input', base_name + '_grammar.txt')

            # 已有 TXT 时，提供"复用 TXT"选项
            if os.path.exists(output_txt_file):
                print("\n" + "=" * 80)
                print(f"[发现] 语法检查文件已存在：{output_txt_file}")
                print("=" * 80)
                print("\n检测到该文档的语法检查结果文件已存在，请选择处理方式：")
                print("1. 使用现有的 TXT 文件生成 DOCX（跳过 LLM 检查）")
                print("2. 重新进行语法检查（覆盖现有的 TXT 文件）")
                print("3. 取消操作")

                while True:
                    choice = input("\n请输入选项 (1/2/3): ").strip()
                    if choice == '1':
                        print("\n" + "=" * 80)
                        print("[任务] 从 TXT 文件生成文档")
                        print("=" * 80)
                        print(f"[输入] 原始文档：{args.input}")
                        print(f"[输出] 语法检查：{output_txt_file}")
                        provider = create_provider(args.input)
                        apply_txt_to_document(provider, output_txt_file)
                        sys.exit(0)
                    elif choice == '2':
                        break
                    elif choice == '3':
                        print("[取消] 操作已取消")
                        sys.exit(0)
                    else:
                        print("[错误] 无效选项，请重新输入")

            # 创建对应的 DocumentProvider 并执行通用处理
            provider = create_provider(args.input)

            print("\n" + "=" * 80)
            print(f"[段落] 按段落拆分检查并修改 {input_ext.upper().lstrip('.')} 文件")
            print("=" * 80)
            print(f"[输入] 原始文档：{args.input}")
            print(f"[输出] 语法检查：{output_txt_file}")

            process_document(provider, output_txt_file)

    except Exception as e:
        print(f"[错误] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
