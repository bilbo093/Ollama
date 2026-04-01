#!/usr/bin/env python3
"""
学术文档处理工具主入口
运行：python main.py
用法：
  python main.py summarizer -i input.txt -o output.txt
  python main.py chapter -i input.txt -o output.txt
"""
import sys
import os
import argparse

# 自动找到 src 目录
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from ollama_processor import generate_and_save_chapter_summaries, generate_and_save_grammar_checks, TextProcessor
from file_io import read_file_content, validate_file_format, save_to_txt
from config import PROCESSOR_CONFIGS
from segmented_evaluator import three_stage_evaluation
from docx_editor import generate_corrected_docx


def main():
    """主函数：解析命令行参数并执行对应操作"""
    parser = argparse.ArgumentParser(
        prog='academic-doc',
        description='学术文档处理工具 - 生成学术摘要、章节总结、分段评价、语法检查',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例：
  生成学术摘要:  python main.py summarizer -i input.txt -o output.txt
  生成章节总结:  python main.py chapter -i input.txt -o output.txt
  三阶段评价:   python main.py evaluate -i input.txt -o output.txt

  语法检查并修改（自动推断文件）:
    python main.py grammar -i input.docx
  语法检查并修改（指定语法检查文件）:
    python main.py grammar -i input.docx -o grammar.txt
  语法检查并修改（指定输出 DOCX 文件）:
    python main.py grammar -i input.docx -o output.docx

  说明：
  - 语法检查文件：使用 -o 指定 .txt 文件，或自动使用 input/{文件名}_grammar.txt
  - 输出 DOCX 文件：使用 -o 指定 .docx 文件，或自动生成 {输入文件名}_fixed.docx
  - 如果语法检查文件不存在，会自动生成
  - 如果语法检查文件已存在，直接使用，跳过重新检查
        '''
    )

    subparsers = parser.add_subparsers(dest='command', help='命令类型')

    # summarizer 子命令
    summarizer_parser = subparsers.add_parser('summarizer', help='生成学术风格摘要')
    summarizer_parser.add_argument('-i', '--input', type=str, required=True,
                                  help='输入文件路径 (.txt 或 .docx)')
    summarizer_parser.add_argument('-o', '--output', type=str, required=True,
                                  help='输出文件路径 (.txt)')

    # chapter 子命令
    chapter_parser = subparsers.add_parser('chapter', help='生成章节总结')
    chapter_parser.add_argument('-i', '--input', type=str, required=True,
                               help='输入文件路径 (.txt 或 .docx)')
    chapter_parser.add_argument('-o', '--output', type=str, required=True,
                               help='输出文件路径 (.txt)')

    # evaluate 子命令
    evaluate_parser = subparsers.add_parser('evaluate', help='三阶段分段评价')
    evaluate_parser.add_argument('-i', '--input', type=str, required=True,
                                help='输入文件路径 (.txt 或 .docx)')
    evaluate_parser.add_argument('-o', '--output', type=str, required=True,
                                help='输出文件路径 (.txt)')
    evaluate_parser.add_argument('--chunk-size', type=int, default=30000,
                                help='每块字符数（默认：30000）')
    evaluate_parser.add_argument('--overlap', type=int, default=3000,
                                help='重叠字符数（默认：3000）')

    # grammar 子命令（合并语法检查和修改功能）
    grammar_parser = subparsers.add_parser('grammar', help='语法检查并修改 DOCX 文件')
    grammar_parser.add_argument('-i', '--input', type=str, required=True,
                               help='输入文件路径 (.docx)')
    grammar_parser.add_argument('-o', '--output', type=str,
                               help='语法检查结果文件路径（.txt）或输出 DOCX 文件路径')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == 'summarizer':
            from config import DEFAULT_MODEL
            print(f"[使用] 模型：{DEFAULT_MODEL}")
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

            # 生成摘要
            print("[摘要] 正在分析整个文档...")
            config = PROCESSOR_CONFIGS['summarizer']
            processor = TextProcessor(config['role'], config['prompt_template'])
            summary = processor.process_content(content)
            print("[摘要生成完成]")
            save_to_txt(summary, output_file)

        elif args.command == 'chapter':
            from config import DEFAULT_MODEL
            print(f"[使用] 模型：{DEFAULT_MODEL}")
            print("[任务] 生成章节总结...")

            if not os.path.exists(args.input):
                print(f"[错误] 输入文件不存在：{args.input}")
                sys.exit(1)

            if not validate_file_format(args.input):
                sys.exit(1)

            # 读取文件内容并生成章节总结
            content = read_file_content(args.input)
            generate_and_save_chapter_summaries(content, args.output)

        elif args.command == 'evaluate':
            from config import DEFAULT_MODEL
            print(f"[使用] 模型：{DEFAULT_MODEL}")
            print("[任务] 三阶段分段评价...")

            if not os.path.exists(args.input):
                print(f"[错误] 输入文件不存在：{args.input}")
                sys.exit(1)

            if not validate_file_format(args.input):
                sys.exit(1)

            # 读取文件内容
            content = read_file_content(args.input)

            # 执行三阶段评价
            chunk_evaluations, aggregated_info, final_report = three_stage_evaluation(
                content,
                chunk_size=args.chunk_size,
                overlap=args.overlap
            )

            # 保存结果（包含所有三个阶段）
            output_content = ""
            output_content += "=" * 80 + "\n"
            output_content += "阶段1：分段评价结果\n"
            output_content += "=" * 80 + "\n\n"
            output_content += chunk_evaluations + "\n\n"

            output_content += "=" * 80 + "\n"
            output_content += "阶段2：分段汇总（按维度整理）\n"
            output_content += "=" * 80 + "\n\n"
            output_content += aggregated_info + "\n\n"

            output_content += "=" * 80 + "\n"
            output_content += "阶段3：最终评价报告\n"
            output_content += "=" * 80 + "\n\n"
            output_content += final_report + "\n\n"

            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_content)

            print(f"\n[完成] 评价报告已保存至：{args.output}")

        elif args.command == 'grammar':
            from config import DEFAULT_MODEL
            print(f"[使用] 模型：{DEFAULT_MODEL}")

            # 验证输入文件
            if not os.path.exists(args.input):
                print(f"[错误] 输入文件不存在：{args.input}")
                sys.exit(1)

            input_ext = os.path.splitext(args.input)[1].lower()
            if input_ext != '.docx':
                print(f"[错误] 输入文件必须是 DOCX 格式：{args.input}")
                sys.exit(1)

            # 处理 -o 参数
            grammar_check_file = None
            output_docx_file = None

            if args.output:
                output_ext = os.path.splitext(args.output)[1].lower()
                if output_ext == '.txt':
                    # -o 指定的是语法检查文件
                    grammar_check_file = args.output
                elif output_ext == '.docx':
                    # -o 指定的是输出 DOCX 文件
                    output_docx_file = args.output
                else:
                    print(f"[错误] -o 参数必须是 .txt 或 .docx 格式：{args.output}")
                    sys.exit(1)

            # 如果没有指定语法检查文件，自动推断
            if not grammar_check_file:
                base_name = os.path.splitext(os.path.basename(args.input))[0]
                grammar_check_file = os.path.join('input', base_name + '_grammar.txt')

            # 检查语法检查文件是否存在
            if not os.path.exists(grammar_check_file):
                print(f"[信息] 语法检查文件不存在，开始生成：{grammar_check_file}")
                print("=" * 60)
                print("[阶段1] 执行语法检查")
                print("=" * 60)

                # 读取文件内容并生成语法检查
                content = read_file_content(args.input)
                generate_and_save_grammar_checks(content, grammar_check_file)
                print(f"[完成] 语法检查结果已保存至：{grammar_check_file}")
            else:
                print(f"[信息] 检测到现有语法检查文件：{grammar_check_file}")
                print(f"[选项] 请选择操作：")
                print(f"  1. 直接使用现有语法检查文件（快速）")
                print(f"  2. 重新生成语法检查（慢速）")

                # 获取用户选择
                while True:
                    choice = input("请输入选择 [1/2, 默认: 1]: ").strip() or "1"
                    if choice == "1":
                        print(f"[信息] 使用现有语法检查文件")
                        break
                    elif choice == "2":
                        print(f"[信息] 开始重新生成语法检查文件...")
                        print("=" * 60)
                        print("[阶段1] 执行语法检查")
                        print("=" * 60)

                        # 读取文件内容并生成语法检查
                        content = read_file_content(args.input)
                        generate_and_save_grammar_checks(content, grammar_check_file)
                        print(f"[完成] 语法检查结果已保存至：{grammar_check_file}")
                        break
                    else:
                        print(f"[错误] 无效选择，请输入 1 或 2")

            # 如果没有指定输出 DOCX 文件，自动推断
            if not output_docx_file:
                # 在输入文件同目录生成 {原文件名}_fixed.docx
                input_dir = os.path.dirname(args.input)
                base_name = os.path.splitext(os.path.basename(args.input))[0]
                output_docx_file = os.path.join(input_dir, base_name + '_fixed.docx')

            # 验证输出文件格式
            output_ext = os.path.splitext(output_docx_file)[1].lower()
            if output_ext != '.docx':
                print(f"[错误] 输出文件必须是 DOCX 格式：{output_docx_file}")
                sys.exit(1)

            print("\n" + "=" * 60)
            print("[阶段2] 应用修改到 DOCX 文件")
            print("=" * 60)
            print(f"[输入] 原始文档：{args.input}")
            print(f"[输入] 语法检查：{grammar_check_file}")
            print(f"[输出] 修改文档：{output_docx_file}")

            # 应用修改到文档
            count = generate_corrected_docx(
                grammar_check_file,
                args.input,
                output_docx_file
            )

            print(f"\n[完成] 处理完成，共处理 {count} 处修改")

    except Exception as e:
        print(f"[错误] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
